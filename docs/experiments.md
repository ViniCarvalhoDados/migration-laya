# Registro de experimentos

Tudo que foi testado, em ordem, com a conclusão específica de cada tentativa e
o que ela mudou no estudo. Vários experimentos **derrubaram conclusões
anteriores** — isso está marcado onde acontece.

Artefatos brutos em `runs/<id>/`. Todos os números são regeneráveis pelos
comandos indicados.

| # | experimento | run | veredito |
|---|---|---|---|
| [E1](#e1) | Censo determinístico das 99 queries | — | base do estudo |
| [E2](#e2) | Piloto n=10 com cartão | — | ✗ enganoso |
| [E3](#e3) | Escala para n=99 com cartão | `full99` | ✓ base confiável |
| [E4](#e4) | Ablação do `purpose` | `abl_com` / `abl_sem` | ∅ sem efeito detectável |
| [E5](#e5) | SQL bruto em janelas | `sql99` | ✗ piora muito |
| [E6](#e6) | Baseline de regressão logística | `full99` | ✗ Laya empata ou perde |
| [E7](#e7) | Hold-out do limiar | `full99` | ✓ calibração sobrevive |
| [E8](#e8) | Comparação pareada Laya × LR | — | ↻ corrige E6 |
| [E9](#e9) | Sensibilidade à formulação + negação | `variants` | ✗ derruba E7/E8 |
| [E10](#e10) | Ensemble de 6 paráfrases | `ensemble` | ✓ resolve E9 |
| [E11](#e11) | As duas perguntas de valor comercial | `business` | ◑ uma sim, uma não |
| [E12](#e12) | Custo contra LLM tradicional | — | ◑ real mas pequeno |

---

## E1 — Censo determinístico das 99 queries {#e1}

**Pergunta.** Dá para produzir gabarito objetivo para um corpus inteiro sem
trabalho manual?

**Setup.** `sqlglot` sobre as 99 queries TPC-DS, cascata de dialetos
`spark → tsql`. 47 features por script: estrutura, funções analíticas, fontes,
grafo de joins, marcadores de não-portabilidade. Rubrica de complexidade com
limiares derivados de percentis do próprio corpus.

```bash
mlaya census --verify --emit-rubric
```

**Resultado.** 99/99 parseadas (98 em `spark`, 1 em `tsql` — query67 usa
`SELECT TOP`). Bandas 31/37/31. Cobertura de resolução de predicados de join:
92,1%.

**Conclusão específica.** O gabarito das perguntas verificáveis e da
complexidade sai de graça para o corpus inteiro. **Mas isso é exatamente o que
cria a circularidade central do estudo** — ver [limitações](limitations.md#circularidade).

**Achados colaterais.** O corpus é dialeto-misto (query67 é T-SQL). E auditoria
manual pegou um bug: CTEs eram contados como tabelas-fonte, inflando uma feature
pontuada na rubrica *e* o gabarito de `multi_source`.

---

## E2 — Piloto com 10 scripts {#e2}

**Pergunta.** O Laya classifica scripts SQL a partir de um cartão comprimido?

**Setup.** 10 scripts por amostragem estratificada, 6 perguntas tipadas, cartão
de ~100 tokens derivado do AST.

**Resultado.**

| pergunta | acurácia |
|---|---|
| `has_window_function` | 90% |
| `multi_source` | 70% |
| `has_subquery` | **40%** |

**Conclusão específica (ERRADA, corrigida em E3).** Reportei que `has_subquery`
era "pior que o acaso" e que o agregado das binárias (67%) batia "~50% de
acaso".

**Dois erros:**

1. **n=10 é ruído.** Os 40% viraram 74% em n=99.
2. **"50% de acaso" é falso** para pergunta binária com classes
   desbalanceadas. O baseline real é a classe majoritária: 58%, 85%, 79%.

**O que mudou.** Coluna de baseline de classe majoritária em toda tabela do
relatório, e escala para o corpus inteiro.

---

## E3 — Escala para n=99 {#e3}

**Setup.** As 99 queries, mesmas 6 perguntas. Gabarito de julgamento
(`rewrite_strategy`, `needs_human_review`) escrito lendo cada SQL.

```bash
mlaya ask --run-id full99 --no-purpose && mlaya decide --run-id full99
```

**Resultado.**

| pergunta | AUC | acc @0,5 | baseline | respostas distintas |
|---|---|---|---|---|
| `has_window_function` | 0,99 | 88% | 85% | 2 |
| `has_subquery` | 0,95 | 80% | 58% | 2 |
| `multi_source` | 0,88 | 77% | 79% | 2 |
| `needs_human_review` | 0,22 | 54% | 70% | 2 |
| `migration_complexity` | — | 37% | 37% | **1** |
| `rewrite_strategy` | — | 55% | 55% | **1** |

ECE 0,085 · Brier 0,196 · p50 2,3 s/script · `AUTO` 0/99 · `ESCALATE` 0/99.

**Conclusão específica.**

- **O modelo ordena bem e corta errado.** AUC 0,88–0,99 nas binárias
  verificáveis, mas todos os limiares ótimos caem abaixo de 0,5 — subestima
  P(true) de forma sistemática, que é o aviso de temperatura inválida do
  checkpoint aparecendo em número.
- **AUC 0,22 não é ausência de sinal — é sinal invertido.** Invertendo o
  limiar, `needs_human_review` vai a 78%.
- **Os dois categóricos são preditores constantes**, confirmado em escala:
  `medium` e `refactor` nas 99, acurácia igual à taxa-base ao decimal.
- **Zero `ESCALATE`**: nunca afirmou com alta confiança algo que o AST
  contradiz. Os erros são de baixa confiança, o modo recuperável.

---

## E4 — Ablação do `purpose` {#e4}

**Pergunta.** O resumo de negócio escrito por LLM — a parte cara do cartão —
contribui?

**Setup.** Os 10 scripts que têm `purpose` escrito à mão, rodados com e sem ele.

**Resultado.** Cinco das seis perguntas idênticas; `multi_source` ±1 script,
`needs_human_review` ±2.

**Conclusão específica.** **Nenhum efeito detectável — e o teste não tem poder
para afirmar ausência de efeito.** Com n=10 não se demonstra nulidade. A leitura
correta é "nenhum efeito detectável nesta amostra", e foi com base nela que as
99 rodaram sem `purpose`. Decisão de custo assumida, não resultado.

---

## E5 — Laya lendo o SQL bruto {#e5}

**Pergunta.** O cartão entrega os fatos perguntados. E se o modelo lesse o
código?

**Setup.** Cada script partido em janelas de 512 tokens, todas as perguntas por
janela, agregação por regras **pré-registradas** em `chunks.AGGREGATION`. 86 dos
99 cabem numa única janela (mediana: 44 linhas).

```bash
mlaya ask --run-id sql99 --source sql && mlaya compare full99 sql99
```

**Resultado.**

| pergunta | cartão AUC | SQL AUC | P(true) cartão | P(true) SQL | taxa real |
|---|---|---|---|---|---|
| `has_subquery` | 0,95 | **0,57** | 0,44 | **0,97** | 0,58 |
| `has_window_function` | 0,99 | **0,67** | 0,16 | **0,80** | 0,15 |
| `multi_source` | 0,88 | 0,61 | 0,67 | 0,97 | 0,79 |
| `needs_human_review` | 0,22 | 0,50 | 0,60 | 0,82 | 0,70 |

| | cartão | SQL |
|---|---|---|
| `AUTO` | 0 | 3 |
| `ESCALATE` | **0** | **80** |
| ECE | 0,085 | **0,276** |
| Brier | 0,196 | **0,326** (acaso = 0,25) |

**Conclusão específica.** **Piora, e piora feio.** Lendo SQL o modelo responde
"sim" a quase tudo — P(true) médio de 0,80 a 0,97 contra taxas reais de 15% a
58%. Não está lendo o código; está reagindo a texto fora da sua distribuição e
saturando.

**Controle do confundidor.** Restringindo aos 86 scripts de janela única, onde
não há agregação nenhuma, o colapso é idêntico (AUC 0,58 / 0,72 / 0,61 / 0,45).
**O problema é o input, não o fatiamento.**

**Modo de falha muda de categoria.** 81% dos scripts passam a errar com alta
confiança um fato que o AST já conhece — o modo irrecuperável.

**Um ponto a favor:** destrava os categóricos (`rewrite_strategy` emite as 4
classes contra 1). Mas destravar não é acertar: a acurácia cai de 55% para 47%,
abaixo do baseline.

**O que mudou.** Reverteu minha própria recomendação anterior ("mandar SQL em
vez do cartão"). O `laya` é um ModernBERT afinado sobre linguagem natural; SQL é
código e não está na sua distribuição. **O cartão não era muleta — era o que
tornava a tarefa legível.**

---

## E6 — Baseline de regressão logística {#e6}

**Pergunta.** Um modelo de 421M se paga contra aritmética sobre features que já
extraímos de graça?

**Setup.** Regressão logística (IRLS, L2), **leave-one-out**. Duas variantes:
`leaky` inclui a feature de que o rótulo é definido; `clean` a remove.

```bash
mlaya baseline --run-id full99
```

**Resultado.**

| pergunta | variante | LR acc | LR AUC | Laya acc | Laya AUC |
|---|---|---|---|---|---|
| `has_subquery` | leaky | **97%** | 0,97 | 80% | 0,95 |
| `has_subquery` | clean | 85% | 0,88 | 80% | 0,95 |
| `has_window_function` | leaky | **100%** | 1,00 | 88% | 0,99 |
| `has_window_function` | clean | 85% | 0,92 | 88% | 0,99 |
| `multi_source` | leaky | **100%** | 1,00 | 77% | 0,88 |
| `multi_source` | clean | 80% | 0,63 | 77% | 0,88 |
| `needs_human_review` | — | **89%** | **0,94** | 54% | 0,22 |

**Conclusão específica.**

- **A variante leaky em 97–100% é a medida da circularidade.** O cartão lista os
  fatos; a regressão os lê de volta. Sobre o mesmo input, o Laya fica *abaixo*
  da aritmética.
- **Sem vazamento, empate** nas três verificáveis (p = 0,47–0,74).
- **E um achado sobre o meu próprio gabarito:** `needs_human_review` é a única
  pergunta sem vazamento possível, e a LR acerta 89% (AUC 0,94) fora da amostra.
  Ou seja, **meus julgamentos eram em boa medida função das mesmas features do
  AST**. Eu achava que adicionava julgamento semântico; estava majoritariamente
  reescrevendo o extrator.

---

## E7 — Hold-out do limiar {#e7}

**Pergunta.** O "melhor limiar" que eu reportava era ajustado no próprio dado.
Sobrevive a um hold-out?

**Setup.** Divisões estratificadas repetidas, corte escolhido só na metade de
treino, acurácia medida só na de teste.

**Resultado.**

| pergunta | acc @0,5 | **hold-out** | p05–p95 | limiar mediano | hindsight |
|---|---|---|---|---|---|
| `has_window_function` | 88% | **95%** | 92–98% | 0,21 | +2 pts |
| `has_subquery` | 80% | **86%** | 80–90% | 0,36 | +3 pts |
| `multi_source` | 77% | 79% | 72–84% | 0,41 | +4 pts |
| `needs_human_review` | 54% | **75%** | 70–80% | 0,73 (inv.) | +3 pts |

**Conclusão específica.** **A calibração sobrevive** — o gap de hindsight é de 2
a 4 pontos. Não era sorte do ajuste. E todos os limiares ótimos ficam **abaixo
de 0,5**, confirmando a subestimação sistemática de P(true).

---

## E8 — Comparação pareada Laya × LR {#e8}

**Pergunta.** E6 comparou o Laya no corte fixo de 0,5 contra uma LR cujas
probabilidades já saem calibradas do ajuste. Isso é injusto. E se os dois forem
tratados igual?

**Setup.** 200 splits, os dois ajustados só no treino e medidos só no teste.

**Resultado.**

| pergunta | Laya | LR | baseline | diferença | IC90 | splits Laya>LR |
|---|---|---|---|---|---|---|
| `has_window_function` | **95%** | 83% | 85% | **+11,4** | +6,0 a +18,0 | **100%** |
| `has_subquery` | 86% | 80% | 58% | +5,4 | −4,0 a +16,0 | 76% |
| `multi_source` | 79% | 77% | 79% | +2,8 | −8,0 a +12,0 | 63% |
| `needs_human_review` | 75% | **84%** | 70% | **−8,8** | −16,0 a 0,0 | 3% |

**Conclusão específica.** ↻ **Corrige E6.** Com tratamento igual, o Laya **vence
a regressão** em `has_window_function`. Só duas diferenças são consistentes
(IC90 sem cruzar zero): essa, a favor dele, e `needs_human_review`, contra.

**Nota metodológica.** Sem p-valor de propósito: as 200 metades de teste se
sobrepõem, então um teste pareado clássico seria anticonservador. A dispersão
entre splits é o número honesto. (Eu cheguei a calcular McNemar agregando pares
discordantes dos 200 splits — estava errado e foi descartado.)

---

## E9 — Sensibilidade à formulação e teste de negação {#e9}

**Pergunta.** Reformular uma pergunta durante o estudo moveu seu AUC de 0,84
para 0,95. Quanto de todo o resto é a redação?

**Setup.** Cada pergunta em três formas **na mesma chamada**: `v1` a do estudo,
`v2` mesma coisa com outro vocabulário, `v3` **negada**. Previsão registrada
antes do run: um modelo que *lê* deveria inverter, AUC(v3) ≈ 1 − AUC(v1).

```bash
mlaya ask --run-id variants --questions config/questions_variants.yml --no-purpose
mlaya variants --run-id variants
```

**Resultado.**

| pergunta | v1 | v2 | \|Δ\| | v3 previsto | v3 obtido | negação |
|---|---|---|---|---|---|---|
| `has_subquery` | 0,95 | 0,85 | 0,10 | 0,05 | 0,05 | **inverteu** |
| `has_window_function` | 0,99 | **0,42** | **0,57** | 0,01 | 0,47 | **não inverteu** |
| `multi_source` | 0,88 | 0,55 | 0,33 | 0,12 | 0,19 | inverteu |
| `needs_human_review` | 0,22 | 0,35 | 0,13 | 0,78 | 0,14 | **não inverteu** |

**Deslocamento médio: 0,28 de AUC. Máximo: 0,57.**

**Conclusão específica.** ✗ **Derruba E7 e E8.**
`has_window_function` era a única pergunta em que o Laya batia a regressão de
forma consistente — e é a **mais frágil**: trocar *"Does this script use an
analytic window function with an OVER clause?"* por *"Is there an OVER clause
anywhere in this query?"* leva o AUC de 0,99 a 0,42, abaixo do acaso. E não
inverte sob negação: não estava lendo a pergunta.

A única robusta aos dois testes é `has_subquery` — que é justamente onde Laya e
LR empatam.

**A conclusão inteira do estudo cabia dentro do ruído de formulação.** Se eu
tivesse escrito a `v2` como redação principal, as quatro perguntas teriam
parecido próximas do acaso e eu teria concluído "não serve" com a mesma
convicção.

---

## E10 — Ensemble de paráfrases {#e10}

**Pergunta.** Se uma redação sortuda vale 0,57 de AUC, dá para não depender de
acertar a frase?

**Setup.** Seis paráfrases genuínas por pergunta (mesmas condições de verdade,
vocabulário diferente), todas na mesma chamada. Resposta = média de P(true), que
**não olha o gabarito**.

```bash
mlaya ask --run-id ensemble --questions config/questions_ensemble.yml --no-purpose
mlaya ensemble --run-id ensemble
```

**Resultado.**

| pergunta | pior | oráculo | amplitude | média isolada | **ensemble** |
|---|---|---|---|---|---|
| `has_subquery` | 0,77 | 1,00 | 0,23 | 0,91 | **1,00** |
| `has_window_function` | 0,42 | 0,99 | 0,57 | 0,78 | **0,91** |
| `multi_source` | 0,55 | 0,90 | 0,35 | 0,73 | **0,86** |
| `needs_human_review` | 0,15 | 0,40 | 0,25 | 0,28 | 0,24 |

Pareado contra a LR (200 splits, os dois ajustados só no treino):

| pergunta | Laya 1× | **Laya 6×** | LR | baseline | 6×−LR | IC90 | splits |
|---|---|---|---|---|---|---|---|
| `has_subquery` | 86% | **95%** | 80% | 58% | **+15,2** | +6,0 a +26,0 | **100%** |
| `has_window_function` | 95% | 87% | 83% | 85% | +4,1 | −4,0 a +12,0 | 75% |
| `multi_source` | 79% | 79% | 77% | 79% | +2,8 | −6,0 a +12,0 | 62% |
| `needs_human_review` | 75% | 74% | **84%** | 70% | **−9,8** | −18,0 a 0,0 | 3% |

**Conclusão específica.** ✓ **Resolve E9.** Agregar chega ao teto do oráculo
(melhor redação escolhida *com o gabarito na mão*) sem precisar saber qual frase
era a boa.

**`has_subquery` é a única vitória sólida do Laya no estudo inteiro:** 95%
contra 80% da LR e 58% do baseline, IC90 longe de zero, consistente em 100% dos
splits. É também a única robusta à paráfrase e que passa no teste de negação —
três evidências independentes.

**O preço honesto:** em `has_window_function` o ensemble (87%) fica *abaixo* da
redação sortuda (95%). Você troca um número que não teria como saber escolher
por um que dá para implantar.

**Custo:** 8,1 s/script contra 2,3 s (24 chamadas em vez de 6).

**Agregar não cria sinal onde não há:** `needs_human_review` continua em 0,24.

---

## E11 — As duas perguntas de valor comercial {#e11}

**Pergunta.** `migration_complexity` e `rewrite_strategy` são as que uma
consultoria pagaria para responder — e nunca receberam o tratamento que salvou
as binárias. Foram julgadas pelo argmax sob uma redação só, o que não é teste
justo.

**Setup.** Quatro redações cada, variando o eixo que a auditoria apontou: as
opções originais ecoam o vocabulário do cartão; as alternativas descrevem por
esforço, por quem faz o trabalho, e sem descrição nenhuma.

```bash
mlaya ask --run-id business --questions config/questions_business.yml --no-purpose
```

### Complexidade — há base

| redação | AUC low↔high | 3 bandas (hold-out) | baseline |
|---|---|---|---|
| p1 (a do estudo) | **0,86** | **52%** | 31% |
| p2 (por esforço) | 0,77 | 38% | 31% |
| p3 (por quem faz) | 0,83 | 41% | 31% |
| p4 (rótulos nus) | 0,76 | 41% | 31% |
| ensemble | 0,82 | 43% | 31% |

Estrutura do erro (p1, cortes nos quantis do gabarito):

| banda exata | erra 1 banda | **erra 2 bandas** |
|---|---|---|
| 58% | 36% | **6%** |

**Conclusão específica.** Todas as redações ficam acima do baseline. Chamar um
`high` de `low` — o erro que estraga planejamento — acontece em 6%. **94% das
vezes erra no máximo uma banda adjacente.** Para ordenar backlog e decidir por
onde começar, é utilizável.

**Assimetria contra E10:** aqui o **ensemble não ajuda** (43% contra 52% da
melhor redação). Para `score` ordinal, agregar achata a distribuição em vez de
estabilizá-la. E comparar 4 redações e apontar a melhor já é seleção — o
intervalo defensável é **38–52%**.

### Estratégia de reescrita — morta em todas as redações

| redação | classes emitidas | acurácia |
|---|---|---|
| p1 (a do estudo) | 1 | 55% = baseline |
| p2 (por resultado) | 2 | 54% |
| p3 (por abordagem) | 1 | 55% |
| p4 (rótulos nus) | 1 | 55% |
| ensemble | 1 | 55% |

**Conclusão específica.** Quatro formulações muito diferentes, todas colapsam em
`refactor`. Nem os rótulos nus destravam. **Não é viés de formulação — é
ausência de capacidade zero-shot.**

**Mas zero-shot nunca foi o teste certo para essa pergunta.** O rótulo depende
do padrão de código da empresa: o que é "refactor" numa casa é "lift and shift"
em outra. Meu gabarito é a minha opinião, não a decisão do cliente. O caminho é
fine-tune com o histórico dele — ver [`finetuning.md`](finetuning.md).

---

## E12 — Custo contra um LLM tradicional {#e12}

**Setup.** Preços de tabela da API Anthropic, tokens medidos no próprio corpus
(167 por cartão, 517 por SQL cru, + ~250 de prompt), uma chamada por script
respondendo as duas perguntas.

**Resultado — 5.000 scripts.**

| modelo | só o rótulo | com justificativa |
|---|---|---|
| Haiku 4.5 | **$5,83** | $19 |
| Sonnet 5 | $12 | $56 |
| Opus 5 | $20 | $94 |

Com Batch API, metade. Laya: **~$1,28 de CPU para 50.000 scripts**.

**Conclusão específica.** Relativamente 10–100× mais barato; em absoluto,
dezenas de dólares. **Custo de token sozinho não justifica um classificador
pior.** Os dois eixos que justificam são outros:

1. **Residência de dado** — o Laya roda local, o SQL do cliente não sai do
   perímetro. Para consultoria costuma valer mais que $94.
2. **Fine-tune por cliente** — um encoder de 421M você afina com centenas de
   exemplos rotulados; Opus não.

---

## Auditoria externa

Uma auditoria independente reproduziu os números e encontrou erros reais.
Verifiquei cada alegação de forma independente; **todas reproduziram**.

| achado | impacto | estado |
|---|---|---|
| Comparava binárias contra "~50% de acaso" | Inflava o ganho: 79% vs 74% real, não vs 50% | corrigido |
| Só acurácia, sem AUC | Levou ao veredito errado: "sem informação" virou "ordena bem, corta errado" | corrigido |
| `cross_join_risk` disparava com predicado não resolvido ou join por função | Contaminava o gabarito: 12 → 6 scripts; query30 e query81 mudaram de banda | corrigido |
| Pergunta `has_subquery` ambígua com CTE (9 scripts) | Só reformular levou o **AUC de 0,84 para 0,95** | corrigido |
| Runs antigos irreprodutíveis — `sample` remapeou ids | Re-pontuar casava respostas com o gabarito errado | corrigido: raw guarda a query de origem |
| "8% sem humano com zero erro" | n=7, IC95 de 49–97% | retirado |
| A rubrica não mede dificuldade de migração (ρ=0,82 com contagem de linhas) | Mede tamanho, não esforço | [em aberto](limitations.md) |
| Score esperado correlaciona mais com `max_nesting_depth` (0,67) que com a rubrica (0,59) | Reage a números literais do cartão | [em aberto](limitations.md) |
| `multi_source` não faz comparação numérica: P(true) sobe até 4 fontes (0,92) e **cai** para 0,32 em 13 | Não conta tabelas | [em aberto](limitations.md) |

O caso mais instrutivo é o da pergunta ambígua. *"Does this script nest a SELECT
inside another query?"* é ambíguo para um `WITH` — um CTE é, na maioria das
leituras, exatamente isso. Nove scripts têm CTE e nenhuma subquery inline, e
cinco dos erros do modelo eram esses nove. **Explicitar que CTE não conta levou
o AUC de 0,84 a 0,95** — evidência direta, antes mesmo de E9, de que parte do
que eu chamava de "o checkpoint não carrega informação" era viés de formulação.
