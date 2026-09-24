# Registro de experimentos

Tudo que foi testado, em ordem, com a conclusão específica de cada tentativa e
o que ela mudou no estudo. Vários experimentos **derrubaram conclusões
anteriores** — isso está marcado onde acontece.

Artefatos brutos em `runs/<id>/`. Todos os números são regeneráveis pelos
comandos indicados — desde [E13](#e13), que trouxe para o repositório as
comparações de E8, E10 e E11, até então produzidas por scripts fora dele.

| # | experimento | run | veredito |
|---|---|---|---|
| [E1](#e1) | Censo determinístico das 99 queries | — | base do estudo |
| [E2](#e2) | Piloto n=10 com cartão | — | ✗ enganoso |
| [E3](#e3) | Escala para n=99 com cartão | `full99` | ✓ base confiável |
| [E4](#e4) | Ablação do `purpose` | `abl_com` / `abl_sem` | ∅ sem efeito detectável |
| [E5](#e5) | SQL bruto em janelas | `sql99` | ✗ piora muito |
| [E6](#e6) | Baseline de regressão logística | `full99` | ✗ Laya empata ou perde |
| [E7](#e7) | Hold-out do limiar | `full99` | ✓ calibração sobrevive |
| [E8](#e8) | Comparação pareada Laya × LR | `full99` | ↻ corrige E6 |
| [E9](#e9) | Sensibilidade à formulação + negação | `variants` | ✗ derruba E7/E8 |
| [E10](#e10) | Ensemble de 6 paráfrases | `ensemble` | ✓ resolve E9 |
| [E11](#e11) | As duas perguntas de valor comercial | `business` | ✗ nenhuma das duas |
| [E12](#e12) | Custo contra LLM tradicional | — | ◑ real mas pequeno |
| [E13](#e13) | O comparador certo e o baseline certo | `full99` / `ensemble` / `business` | ↻ **corrige E8, E10, E11** |

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

**Setup.** 200 splits estratificados. Limiar do Laya, coeficientes da LR e
classe majoritária: todos ajustados só na metade de treino, todos medidos só na
metade de teste.

```bash
mlaya paired --run-id full99        # runs/full99/paired_single.yml
```

**Resultado.** Duas colunas de LR, porque a diferença entre elas é o achado de
[E13](#e13): a **limpa** não recebe as features que definem o rótulo; a **mesma
info** recebe — é a informação que o cartão entrega ao Laya de graça.

| pergunta | Laya | LR limpa | LR mesma info | base | Laya − limpa | Laya − mesma info |
|---|---|---|---|---|---|---|
| `has_window_function` | **95%** | 85% | **100%** | 86% | **+10,2** (+4 a +20) | −4,7 (−8 a 0) |
| `has_subquery` | 86% | 80% | 94% | 58% | +6,6 (−4 a +18) | −7,4 (−16 a +2) |
| `multi_source` | 80% | 76% | **98%** | 78% | +3,8 (−4 a +14) | **−18,0** (−26 a −10) |
| `needs_human_review` | 74% | **84%** | 84% | 70% | **−9,5** (−18 a −2) | **−9,5** (−18 a −2) |

Entre parênteses, p05 e p95 da diferença entre os 200 splits. `needs_human_review`
tem as duas colunas iguais porque o rótulo é julgamento humano: não há feature
que o defina, logo nada a vazar.

**Conclusão específica.** ↻ **Corrige E6.** Com tratamento igual, o Laya vence a
regressão **limpa** em `has_window_function`. ↻ **Corrigido por [E13](#e13):**
contra a regressão com a mesma informação que o cartão, essa vitória desaparece.

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

Pareado contra as duas variantes da LR (200 splits, tudo ajustado só no treino):

```bash
mlaya paired --run-id ensemble --paraphrases   # runs/ensemble/paired_ensemble.yml
```

| pergunta | Laya 1× | **Laya 6×** | LR limpa | LR mesma info | base | 6× − limpa | 6× − mesma info |
|---|---|---|---|---|---|---|---|
| `has_subquery` | 86% | **97%** | 80% | 94% | 58% | **+17,2** (+8 a +28) | +3,3 (−4 a +14) |
| `has_window_function` | 95% | 88% | 85% | **100%** | 86% | +3,6 (−8 a +12) | **−11,3** (−22 a −6) |
| `multi_source` | 80% | 80% | 76% | **98%** | 78% | +3,8 (−2 a +12) | **−18,1** (−24 a −10) |
| `needs_human_review` | 74% | 74% | **84%** | 84% | 70% | −9,8 (−20 a 0) | −9,8 (−20 a 0) |

**Conclusão específica.** ✓ **Resolve E9.** Agregar chega ao teto do oráculo
(melhor redação escolhida *com o gabarito na mão*) sem precisar saber qual frase
era a boa. Esse achado continua de pé: é sobre estabilidade, não sobre o
comparador.

**O que não continua de pé.** ↻ **Corrigido por [E13](#e13).** Eu chamei
`has_subquery` de "a única vitória sólida do estudo" com base nos +15,2 pontos
sobre a LR limpa. Contra a LR que enxerga o mesmo que o cartão, a diferença cai
para **+3,3 pontos com IC de −4 a +14** — empate. Os +17,2 medem o quanto a
regressão foi cegada, não o que o Laya sabe.

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
mlaya business --run-id business          # runs/business/business.yml
```

### Complexidade — ordena, mas não acrescenta nada à rubrica

O baseline é a **classe majoritária do corpus: 37%** (as bandas saem 31 / 37 /
31). A primeira versão desta tabela usava 31%, que é o reflexo "três bandas,
logo um terço" — e sob ele uma redação de 38% parecia estar acima da linha
quando está em cima dela. Corrigido em [E13](#e13).

Cortes ajustados só na metade de treino, medidos só na metade de teste, 200
splits:

| redação | AUC low↔high | argmax | rótulos distintos | 3 bandas (hold-out) | [p05, p95] | teto in-sample |
|---|---|---|---|---|---|---|
| p1 (a do estudo) | **0,87** | 37% | 1 | **54%** | 45–61% | 61% |
| p2 (por esforço) | 0,78 | 37% | 1 | 40% | 33–45% | 47% |
| p3 (por quem faz) | 0,83 | 40% | 2 | 41% | 35–47% | 51% |
| p4 (rótulos nus) | 0,76 | 37% | 1 | 44% | 35–53% | 53% |
| ensemble | 0,82 | 37% | 1 | 44% | 35–53% | 54% |
| **baseline (classe majoritária)** | — | — | — | **37%** | — | — |
| **a própria rubrica** | — | — | — | **100%** | — | — |

Estrutura do erro da p1, também em hold-out:

| banda exata | erra 1 banda | **erra 2 bandas** | dentro de 1 banda |
|---|---|---|---|
| 54% | 38% | **8%** | 92% |

**Conclusão específica.** ↻ **Corrigida por [E13](#e13).** O que sobrevive: o
score esperado **ordena** o corpus (AUC 0,87 entre `low` e `high`) e o erro de
duas bandas é raro (8%). O que não sobrevive: a leitura de que isso serve para
ordenar backlog.

**Por quê.** O gabarito de complexidade *é a rubrica*, uma função determinística
e gratuita das features que o extrator já calcula. A última linha da tabela não
é retórica: para ordenar o backlog basta rodar a rubrica, que acerta 100% em
milissegundos. O Laya a reproduz com 54% — e só depois de cortes ajustados em
dados rotulados. Sem esse ajuste, o argmax é **constante em `medium` nas 99**,
ou seja, exatamente o baseline.

**Assimetria contra E10:** aqui o **ensemble não ajuda** (44% contra 54% da
melhor redação). Para `score` ordinal, agregar achata a distribuição em vez de
estabilizá-la. E comparar 4 redações e apontar a melhor já é seleção — o
intervalo defensável é **40–54%**, não os 54% da melhor.

### Estratégia de reescrita — morta em todas as redações

| redação | classes emitidas | acurácia |
|---|---|---|
| p1 (a do estudo) | 1 (`refactor`) | 55% = baseline |
| p2 (por resultado) | 2 | 54% |
| p3 (por abordagem) | 1 (`refactor`) | 55% |
| p4 (rótulos nus) | 1 (`refactor`) | 55% |

IC95 de todas: 44–64%. Baseline (classe majoritária `refactor`): 55%.

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

A coluna "só o rótulo" assume ~150 tokens de saída, que é generoso para dois
rótulos — o número real seria menor, e a conclusão fica ainda mais forte, não
mais fraca: quanto mais barato o LLM, menos o custo justifica trocá-lo.

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

## E13 — O comparador certo e o baseline certo {#e13}

**Pergunta.** Uma segunda auditoria externa apontou duas coisas que mudam
conclusões, não detalhes:

1. E8 e E10 comparam o Laya contra a regressão **limpa** — aquela de quem foram
   removidas as features que definem o rótulo. Mas o cartão que o Laya lê
   *imprime esses fatos*: `subqueries=0`, `window_fns=2`. Comparar o cartão
   contra um modelo cego para o que o cartão diz mede o handicap, não o modelo.
2. O baseline de complexidade estava em 31% quando a classe majoritária das 99
   é **37%**.

**Setup.** As duas comparações passaram a sair de código versionado, em vez dos
scripts ad-hoc que produziram E8, E10 e E11. Mesmo protocolo para todos os
braços — limiar, coeficientes e classe majoritária ajustados só no treino,
medidos só no teste.

```bash
mlaya paired  --run-id full99                  # E8, agora com as duas LRs
mlaya paired  --run-id ensemble --paraphrases  # E10, idem
mlaya business --run-id business               # E11, com o baseline certo
```

**Resultado — o Laya contra a regressão com a mesma informação.**

| pergunta | Laya 6× | LR mesma info | diferença | IC90 | veredito |
|---|---|---|---|---|---|
| `has_subquery` | 97% | 94% | +3,3 | −4 a +14 | empate |
| `has_window_function` | 88% | **100%** | −11,3 | −22 a −6 | **perde** |
| `multi_source` | 80% | **98%** | −18,1 | −24 a −10 | **perde** |
| `needs_human_review` | 74% | 84% | −9,8 | −20 a 0 | empate |

**Resultado — complexidade contra o baseline certo.**

| | valor |
|---|---|
| classe majoritária (`medium`, 37 de 99) | **37%** |
| argmax do Laya, qualquer redação | 37%, e constante em `medium` |
| melhor redação, cortes em hold-out | 54% (45–61%) |
| a rubrica que define o gabarito | **100%, determinística, grátis** |

**Conclusão específica.** ↻ **Corrige E8, E10 e E11.**

**Com a mesma informação, o Laya nunca vence.** Empata em `has_subquery`, perde
nas outras duas verificáveis. Os "+15,2 pontos" que o README anunciava mediam o
quanto a regressão tinha sido cegada.

**E a conclusão positiva sobre complexidade não se sustenta.** Ela era positiva
*sobre um gabarito que é ele próprio uma função gratuita das features*. Quem
quer ordenar um backlog roda a rubrica e acerta 100%; o Laya entrega 54% da
mesma coisa, e só com cortes ajustados em dados já rotulados.

**O que isto não derruba.** Os resultados **negativos** ficam todos de pé — e
ficam mais fortes, porque agora o comparador é mais duro, não mais frouxo:
[E5](#e5) (SQL bruto), [E9](#e9) (sensibilidade à formulação),
[E11](#e11) em `rewrite_strategy`. O veredito do estudo — **não adotar este
checkpoint zero-shot** — não muda; o que muda é que ele deixa de ter uma
exceção.

**Nota de honestidade.** Esta é a segunda auditoria a encontrar o mesmo padrão:
o desenho favorece o resultado positivo até alguém de fora olhar. Da primeira
vez o problema era a ausência de AUC; desta, a escolha do comparador. As duas
vezes o achado veio de fora, não de mim.

---

## Auditorias externas

Duas auditorias independentes reproduziram os números e encontraram erros
reais. Verifiquei cada alegação de forma independente; **todas reproduziram**.

### Primeira rodada

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

### Segunda rodada

| achado | impacto | estado |
|---|---|---|
| E8/E10 comparavam o Laya contra a LR **limpa**, mas o cartão entrega as features que ela não recebe | Derruba a única vitória do estudo: +15,2 vira +3,3 com IC de −4 a +14 | corrigido em [E13](#e13) |
| Baseline de complexidade em 31%; a classe majoritária é 37% | A redação p2 (40%) deixa de estar "acima do baseline" | corrigido em [E13](#e13) |
| A conclusão positiva sobre complexidade é sobre um gabarito que é a própria rubrica | A rubrica ordena o backlog de graça e com 100%; o Laya entrega 54% da mesma função | conclusão reescrita |
| E8, a tabela pareada do E10 e o E11 inteiro não tinham código no repositório | "Todos os números são regeneráveis" era falso | corrigido: `mlaya paired` e `mlaya business` |
| O relatório lia `measured_ms` do YAML do script, que guarda o **último** run | A tabela de latência do `full99` mostrava o tempo do run `variants` (4060 ms contra 2209 ms reais) | corrigido: lê o raw do próprio run |
| `methodology.md` dizia "8 scripts, zero erros: 49–97%" | Eram 7 scripts com 1 erro | corrigido |
| Redações e paráfrases escritas **depois** de ver os erros | Margem de manobra do pesquisador, não fraude — mas precisa estar declarado | [declarado](limitations.md) |
| `derive-labels` validado em um par só (8 de 9 acertos) | Amostra pequena demais para afirmar que a derivação funciona | [em aberto](limitations.md) |

Um achado desta rodada era um bug meu de aritmética, não de desenho: o grid de
cortes da complexidade arredondava a 3 casas mas o corte era aplicado ao valor
cru, então `1.5999999999999999` caía abaixo de um limiar de `1.6`. Custava
bandas inteiras de acurácia e está fixado por teste.

