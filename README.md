# Discovery: Laya como classificador para triagem de migração SQL

Avaliação técnica de [Laya](https://github.com/NandhaKishorM/laya) — motor de
decisão não-autoregressivo, sem geração de texto — para triar automaticamente um
backlog de scripts SQL legados antes de uma migração.

**Pergunta:** quantos scripts podem ser classificados sem envolver um humano, e
com que confiabilidade?

📄 **Relatório visual:** [`reports/discovery.html`](reports/discovery.html) —
metodologia, resultados e pontos em aberto com diagramas.
Publicado também em <https://claude.ai/code/artifact/6f7ffaeb-abbb-47c1-97b6-f662771470af>.

---

## Veredito (n=99, corpus TPC-DS completo, CPU)

**O que este experimento mede não é o que a pergunta de negócio precisa saber.**
Isso vem antes de qualquer número, e foi apontado por uma auditoria externa que
reproduziu tudo.

O Laya nunca vê o SQL — vê um cartão de ~100 tokens que **lista os fatos
perguntados** (`subqueries=0`, "No CTE, subquery…"). Quatro das seis perguntas
são, portanto, um teste de leitura: um `if` sobre o cartão acerta 100%. E o
gabarito de `migration_complexity` é uma função determinística dos mesmos
números. O desenho não consegue mostrar valor agregado do modelo nessas
perguntas.

Com isso dito, o que dá para afirmar:

| pergunta | AUC | acc @0.5 | IC95 | baseline | McNemar p | melhor limiar | acc nele |
|---|---|---|---|---|---|---|---|
| `has_window_function` | **0.99** | 88% | 80–93% | 85% | 0.25 | 0.21 | **97%** |
| `has_subquery` | **0.95** | 80% | 71–87% | 58% | **0.007** | 0.34 | **89%** |
| `multi_source` | **0.88** | 77% | 68–84% | 79% | 0.86 | 0.35 | **84%** |
| `needs_human_review` | **0.22** | 54% | 44–63% | 70% | **<0.001** | 0.69 (inv.) | **78%** |
| `migration_complexity` | — | 37% | — | 37% | — | — | — |
| `rewrite_strategy` | — | 55% | — | 55% | — | — | — |

**O modelo ordena bem e corta no lugar errado.** AUC 0.88–0.99 nas três
binárias verificáveis, mas o limiar ótimo de todas cai **abaixo de 0.5** — ele
subestima P(true) sistematicamente, que é o aviso de temperatura inválida do
checkpoint aparecendo em números.

`needs_human_review` com AUC **0.22** não é "sem informação": é informação com
**sinal invertido**. Invertendo o limiar, vai a 78%.

Os dois categóricos continuam sendo preditores constantes (`medium` e
`refactor` nas 99), com acurácia igual à taxa-base ao decimal.

> ⚠️ O "melhor limiar" foi ajustado nos mesmos 99 pontos em que é medido. É um
> **teto otimista**, não uma configuração implantável — serve para separar *não
> sabe* de *corta errado*. Um número defensável exige hold-out.

ECE **0.085** · Brier **0.196** · p50 **2.3 s**/script em CPU · 99 scripts em
**3min46s** · `AUTO` 0/99 · `ESCALATE` 0/99.

### Correções após auditoria externa

Uma auditoria independente reproduziu os números e encontrou erros reais. Todos
confirmados e corrigidos:

| achado | estado |
|---|---|
| Eu comparava binárias contra "~50% de acaso" | Corrigido — baseline de classe majoritária em toda tabela |
| Só acurácia reportada; AUC mostraria outra coisa | Corrigido — AUC, McNemar e IC95 adicionados |
| `cross_join_risk` disparava quando um predicado era **não resolvido** (ou feito por função, `Substr(a)=Substr(b)`) | Corrigido — só marca quando o escopo foi 100% entendido. 12 → 6 scripts; query30/query81 caíram de `medium` para `low` |
| Pergunta `has_subquery` ambígua com CTE (9 scripts) | Corrigido — enunciado explicita que CTE não conta. **AUC subiu 0.84 → 0.95** |
| `r2`/`ablation` irreprodutíveis: `sample --n 99` remapeou os ids e os raw JSONs só guardavam `script_id` | Corrigido — raw agora guarda a query de origem, e `decide` casa por ela e avisa quando não consegue |
| README com ECE/Brier e cobertura desatualizados | Corrigido |
| "Gabarito cego" contradizia o aviso de que 89 rótulos vieram depois | Corrigido |

A correção do enunciado de `has_subquery` merece destaque: **mudar só a
redação levou o AUC de 0.84 para 0.95**. Isso é evidência direta de que parte do
que eu chamei de "o checkpoint não carrega informação" era viés de formulação —
e só uma formulação foi testada.

### O baseline que decide o caso: regressão logística nas mesmas features

Superar a classe majoritária é barra baixa. A pergunta real é se um modelo de
421M parâmetros se paga contra aritmética sobre features que já extraímos de
graça. Regressão logística (IRLS, L2, **leave-one-out** — nunca ajustando e
medindo nas mesmas linhas):

| pergunta | variante | LR acc | LR AUC | Laya acc | Laya AUC | McNemar p | leitura |
|---|---|---|---|---|---|---|---|
| `has_subquery` | leaky | **97%** | 0.97 | 80% | 0.95 | 0.0005 | **LR vence** |
| `has_subquery` | clean | 85% | 0.88 | 80% | 0.95 | 0.47 | empate |
| `has_window_function` | leaky | **100%** | 1.00 | 88% | 0.99 | 0.0005 | **LR vence** |
| `has_window_function` | clean | 85% | 0.92 | 88% | 0.99 | 0.51 | empate |
| `multi_source` | leaky | **100%** | 1.00 | 77% | 0.88 | <0.001 | **LR vence** |
| `multi_source` | clean | 80% | 0.63 | 77% | 0.88 | 0.74 | empate |
| `needs_human_review` | — | **89%** | **0.94** | 54% | 0.22 | <0.001 | **LR vence** |

- **leaky** = todas as features, inclusive aquela de que o rótulo é definido.
- **clean** = essas removidas. `needs_human_review` não tem o que vazar (é
  julgamento lido do SQL), então tem uma variante só.

Três leituras, e nenhuma favorece o Laya:

**1. A variante leaky em 97–100% é a medida da circularidade.** O cartão lista
os fatos perguntados; a regressão os lê de volta. Nessas perguntas o Laya não
tem como agregar valor — e, sobre exatamente o mesmo input, fica **abaixo** da
aritmética.

**2. Sem vazamento, é empate.** Nas três verificáveis, LR e Laya são
estatisticamente indistinguíveis (p = 0.47–0.74). O Laya não perde, mas também
não ganha — e custa 421M parâmetros, 2,3 s por script e 1 GB de download contra
uns milissegundos de álgebra.

> Nuance a favor do Laya: por **AUC** ele bate a LR clean em duas das três
> (`multi_source` 0.88 vs 0.63; `has_window_function` 0.99 vs 0.92). Ordena
> melhor, mesmo empatando em acurácia. Se a calibração for resolvida, é aí que
> ele teria alguma chance.

**3. A que mais importa, ele perde feio.** `needs_human_review` é a única
pergunta sem vazamento possível — é julgamento humano/LLM lido do SQL. A
regressão acerta **89% (AUC 0.94)** fora da amostra; o Laya, 54% (AUC 0.22).

E isso expõe um problema **no meu gabarito**, não só no modelo: se uma regressão
logística prevê meu julgamento de "precisa de revisão humana" com AUC 0.94 a
partir de features do AST, então meus julgamentos eram, em boa medida, uma
função determinística dessas mesmas features. Eu achei que estava adicionando
julgamento semântico; estava, majoritariamente, reescrevendo o extrator. A
crítica de circularidade da auditoria alcança também os rótulos que eu supunha
imunes a ela.

### E se o Laya lesse o SQL, em vez do cartão?

Era a recomendação mais importante da auditoria — o cartão entrega os fatos
perguntados, então enquanto o input for um resumo numérico o teto do modelo é
ler números. Testei: `mlaya ask --source sql` parte cada script em janelas do
tamanho do contexto (512 tokens), pergunta tudo de cada janela e agrega por
regras **pré-registradas** em `chunks.AGGREGATION`.

Nota de escala: a mediana dos scripts tem 44 linhas ≈ 136 tokens, então **86 dos
99 cabem inteiros numa janela**. Para a maioria isto não é "fatiado", é
literalmente "o Laya lê o SQL inteiro".

`mlaya compare full99 sql99` — 99 scripts, mesmo gabarito:

| pergunta | gold+ | cartão acc | AUC | P(true) | SQL acc | AUC | P(true) | McNemar |
|---|---|---|---|---|---|---|---|---|
| `has_subquery` | 58% | **80%** | **0.95** | 0.44 | 58% | 0.57 | **0.97** | 0.007 |
| `has_window_function` | 15% | **88%** | **0.99** | 0.16 | **28%** | 0.67 | **0.80** | <0.001 |
| `multi_source` * | 79% | 77% | **0.88** | 0.67 | 79% | 0.61 | **0.97** | 0.86 |
| `needs_human_review` | 70% | 54% | 0.22 | 0.60 | 73% | 0.50 | 0.82 | <0.001 |

\* contagem global: uma janela não vê o script inteiro. Mantida no run para que
o custo do fatiamento apareça em número, em vez de ser discutido.

**A resposta é não — piora, e piora feio.** O AUC despenca de 0.95→0.57 e
0.99→0.67. Olhe a coluna `P(true)`: lendo SQL o modelo responde "sim" a quase
tudo (média 0.80–0.97 contra taxas reais de 15–58%). Ele não está lendo o SQL,
está reagindo a um texto fora da sua distribuição e saturando.

Com o cartão, `has_window_function` tinha P(true) médio de **0.16** contra uma
taxa real de **0.15** — quase perfeito. Com SQL, 0.80.

**Não é artefato da agregação.** Restringindo aos 86 scripts de janela única —
onde não há agregação nenhuma — o colapso é o mesmo (AUC 0.58 / 0.72 / 0.61 /
0.45). O problema é o input, não o fatiamento.

**E o modo de falha muda de categoria:**

| | cartão | SQL bruto |
|---|---|---|
| `AUTO` | 0 | 3 |
| `HUMAN_REVIEW` | 99 | 16 |
| **`ESCALATE`** (erro confiante em fato do AST) | **0** | **80** |

Com o cartão ele nunca afirmou com alta confiança algo que o AST contradiz. Com
SQL, isso acontece em **81% dos scripts** — confiança média de 88–97% enquanto a
acurácia cai para 28% em `has_window_function`. É o modo de falha irrecuperável,
e é o pior resultado do estudo inteiro.

**Um ponto a favor, honestamente:** ler SQL **destrava os categóricos**.
`rewrite_strategy` passa a emitir as 4 classes (contra 1 com o cartão) e
`migration_complexity`, 2. Mas destravar não é acertar: a acurácia de
`rewrite_strategy` cai de 55% para 47%, **abaixo** do baseline de classe
majoritária.

**Leitura:** o `laya` é um ModernBERT afinado sobre estados em linguagem
natural (tickets, mensagens). SQL é código, e não está na sua distribuição.
Isso reverte minha própria recomendação anterior — "mandar SQL em vez do
cartão" era a hipótese certa a testar e o resultado foi negativo. O cartão não
era uma muleta; era o que tornava a tarefa legível para este modelo.

### Validação 2 · o limiar calibrado sobrevive ao hold-out

O "melhor limiar" que eu reportava era ajustado nos mesmos 99 pontos. Refiz com
divisões estratificadas repetidas — corte escolhido só no treino, medido só no
teste:

| pergunta | acc @0,5 | **hold-out** | p05–p95 | limiar mediano | hindsight |
|---|---|---|---|---|---|
| `has_window_function` | 88% | **95%** | 92–98% | 0,21 | +2 pts |
| `has_subquery` | 80% | **86%** | 80–90% | 0,36 | +3 pts |
| `multi_source` | 77% | **79%** | 72–84% | 0,41 | +4 pts |
| `needs_human_review` | 54% | **75%** | 70–80% | 0,73 (inv.) | +3 pts |

O gap de hindsight é de 2 a 4 pontos: **a calibração sobrevive**. E isso me
obriga a corrigir a comparação com a regressão logística, que eu tinha feito de
forma injusta — comparei o Laya no corte fixo de 0,5 contra uma LR cujas
probabilidades já saem calibradas do ajuste.

Refazendo pareado (mesmos splits, os dois ajustados só no treino, 200 repetições):

| pergunta | Laya | LR | baseline | diferença | IC90 | splits Laya&gt;LR |
|---|---|---|---|---|---|---|
| `has_window_function` | **95%** | 83% | 85% | **+11,4 pts** | +6,0 a +18,0 | **100%** |
| `has_subquery` | 86% | 80% | 58% | +5,4 pts | −4,0 a +16,0 | 76% |
| `multi_source` | 79% | 77% | 79% | +2,8 pts | −8,0 a +12,0 | 63% |
| `needs_human_review` | 75% | **84%** | 70% | **−8,8 pts** | −16,0 a 0,0 | 3% |

Só duas diferenças são consistentes (IC90 sem cruzar zero): `has_window_function`
a favor do Laya e `needs_human_review` a favor da LR. **Com calibração, o Laya
vence a regressão numa pergunta** — o que não acontecia na leitura anterior.

> Sem p-valor aqui de propósito: as 200 metades de teste se sobrepõem, então um
> teste pareado clássico seria anticonservador. A dispersão entre splits é o
> número honesto.

### Validação 3 · quanto disso é a redação da pergunta?

Cada pergunta feita de três formas, **na mesma chamada** (para que variância
entre runs não vire efeito de redação): `v1` a do estudo, `v2` a mesma coisa com
outro vocabulário, `v3` **negada**. A previsão foi registrada em
`config/questions_variants.yml` antes do run: um modelo que *lê* deveria
inverter, AUC(v3) ≈ 1 − AUC(v1).

| pergunta | v1 | v2 | \|Δ\| | v3 previsto | v3 obtido | negação |
|---|---|---|---|---|---|---|
| `has_subquery` | 0,95 | 0,85 | 0,10 | 0,05 | 0,05 | **inverteu** |
| `has_window_function` | 0,99 | **0,42** | **0,57** | 0,01 | 0,47 | **não inverteu** |
| `multi_source` | 0,88 | 0,55 | 0,33 | 0,12 | 0,19 | **inverteu** |
| `needs_human_review` | 0,22 | 0,35 | 0,13 | 0,78 | 0,14 | **não inverteu** |

**Deslocamento médio por reescrita: 0,28 de AUC. Máximo: 0,57.**

Isso derruba o achado da validação 2. `has_window_function` era a única pergunta
em que o Laya batia a regressão de forma consistente (+11,4 pts, 100% dos
splits) — e é justamente a **mais frágil**: trocar *"Does this script use an
analytic window function with an OVER clause?"* por *"Is there an OVER clause
anywhere in this query?"* leva o AUC de **0,99 para 0,42**, abaixo do acaso. E
ela não inverte sob negação, ou seja, não estava lendo a pergunta.

A única que se sustenta nos dois testes é `has_subquery`: robusta à paráfrase
(0,95 → 0,85) e inverte corretamente sob negação. É também aquela em que Laya e
LR empatam.

> **A conclusão inteira deste estudo cabe dentro do ruído de formulação.** Se eu
> tivesse escrito a `v2` como redação principal, as quatro perguntas teriam
> parecido próximas do acaso e eu teria concluído "o checkpoint não serve" — com
> a mesma convicção.

### O que o experimento **não** pode concluir

- **A rubrica não mede dificuldade de migração.** Ela tem **rho = 0.82 com
  contagem de linhas**. Mede tamanho e estrutura. Além disso o TPC-DS foi
  escrito para rodar em qualquer engine, e a pergunta não informa dialeto de
  origem nem de destino.
- **O score esperado reage ao que está escrito no cartão**, não à rubrica:
  correlaciona mais com `max_nesting_depth` (0.67) e `subquery_count` (0.66) do
  que com os pontos da rubrica (0.59).
- **`multi_source` não faz a comparação numérica** que a pergunta pede
  ("≥4 fontes"): P(true) sobe até 4 fontes (0.92) e depois **cai** — 0.56 em 6,
  0.32 em 13.
- **"8% sem humano com zero erro" não se sustenta.** São n=7–8 scripts; o IC95
  da acurácia é 49–97%. E são fatos que o AST responde de graça.
- **O gabarito de julgamento tem um anotador só, que é um LLM**, sem
  concordância humana medida, e `manual_rewrite` tem zero instâncias. Pior: uma
  regressão logística reproduz esses julgamentos com AUC 0.94, o que sugere que
  eles são em grande parte função das features — e não do julgamento que
  deveriam trazer.

### Recomendação

**Não adotar o Laya para esta tarefa com este checkpoint.** Não porque ele seja
ruim — ele ordena bem (AUC 0.88–0.99 nas verificáveis) — mas porque:

1. Nas perguntas em que o cartão entrega a resposta, uma regressão logística
   acerta 97–100% e ele fica abaixo disso.
2. Nas mesmas perguntas sem vazamento, ele **empata** com a regressão.
3. Na única pergunta que exigiria julgamento de verdade, a regressão faz 89%
   (AUC 0.94) e ele faz 54% (AUC 0.22).

Nenhum desses três cenários justifica 421M parâmetros, 1 GB de download e 2,3 s
por script contra milissegundos de álgebra sobre features que o `sqlglot` já
produz.

**O que faria sentido tentar antes de descartar de vez**, em ordem de custo:

1. **Calibrar temperatura** e usar o limiar ajustado em hold-out — a AUC diz
   que a informação está lá e o corte é que está errado (0.21–0.35, não 0.5).
2. ~~Mandar SQL, não o cartão.~~ **Testado, e é pior** — ver a seção acima.
   AUC despenca para ~0.6 e 81% dos scripts caem em `ESCALATE`. Um modelo
   afinado em código (não este) seria outra conversa.
3. ~~Testar outras formulações de prompt.~~ **Feito** (`mlaya variants`), e é o
   achado mais forte: 0,28 de AUC de deslocamento médio por reescrita.
4. Só então, fine-tune.

### O que faria o estudo valer

1. Gabarito independente do input: esforço real de migração, anotadores humanos,
   kappa medido.
2. Corpus legado de verdade (PL/SQL, T-SQL procedural, SQL dinâmico) e dialeto
   de destino explícito na pergunta.
3. ~~Regressão logística sobre as mesmas features como baseline~~ — **feito**
   (`mlaya baseline`). Resultado acima: o Laya empata na melhor hipótese e
   perde por larga margem na única pergunta sem vazamento.
4. Variações de prompt e de opções; mandar o SQL (ou trechos) em vez do cartão.
5. Ajustar limiar em treino e medir em hold-out.

### Ablação do `purpose` — sem efeito detectável, mas sem poder

Rodei os 10 scripts que têm resumo de negócio escrito à mão, com e sem ele
(`runs/abl_com` vs `runs/abl_sem`). Cinco das seis perguntas deram resultado
idêntico; `multi_source` variou ±1 e `needs_human_review` ±2 scripts.

**Isso não demonstra que o `purpose` não ajuda.** Com n=10 o teste não tem poder
para detectar um efeito moderado — a leitura correta é "nenhum efeito
detectável nesta amostra", e foi com base nela que as 99 rodaram sem `purpose`.
É uma decisão de custo assumida, não um resultado.

Relatório completo: `runs/full99/report.md`.

> ⚠️ **Sobre o gabarito.** Os 3 fatos verificáveis e `migration_complexity` vêm
> do AST e da rubrica. `rewrite_strategy` e `needs_human_review` são julgamentos
> de um único anotador (Claude) lendo cada SQL: **10 escritos antes** de o Laya
> rodar, **89 depois** de um run existir em disco (sem consultá-lo). Blindagem
> procedimental, não estrutural. Registrado em `state/gold_judgements.yml`.

---

## O que este repositório entrega

O **Bloco A (censo)** vale por si só, independentemente do Laya:

- `reports/census.md` — perfil objetivo das 99 queries TPC-DS
- `state/corpus_census.csv` — 47 features por script, extraídas do AST
- `config/rubric.yml` — rubrica de complexidade com limiares derivados de
  percentis do corpus, não de opinião

O **Bloco B (Laya)** produz `runs/<id>/report.md` com acurácia **e AUC**,
baseline de classe majoritária, **baseline de regressão logística sobre as
mesmas features**, McNemar, IC95, calibração, matrizes de confusão, curva
cobertura×acurácia (por resposta **e** por script) e latência.

---

## Arquitetura

```
[0] censo — sqlglot nas 99 queries ──► distribuição do corpus
      │   percentis ──► limiares da rubrica ──► complexidade GOLD
      │   └─► amostragem estratificada ──► n scripts
      ▼
[1] extrator determinístico ──► features + grafo de joins   (verdade sintática)
[2] Claude ──► propósito de negócio + gabarito de julgamento (escrito às cegas)
      │
      └──► evidence card (~100 tokens)  ◄── único input do Laya
                  │
[3] Laya ──► choice/score/noul + probabilidades
                  │
[4] árvore de decisão ──► AUTO / HUMAN_REVIEW / ESCALATE
                  │
[5] relatório ──► acurácia · ECE · Brier · cobertura×acurácia · latência
```

**Por que o Laya nunca vê o SQL:** o checkpoint inglês tem contexto de 512 tokens
por passagem. Um script de 300 linhas não cabe. O *evidence card* — 3 linhas
comprimidas do AST mais uma frase de propósito — é o que realmente é
classificado.

**Por que perguntar coisas que o AST já sabe:** `has_subquery`,
`has_window_function` e `multi_source` são 100% verificáveis. Isso torna o
gabarito objetivo e barato para as 99 queries sem trabalho manual, e transforma
um erro confiante nessas perguntas no sinal negativo mais forte possível — é o
que a árvore de decisão chama de `ESCALATE`.

---

## Como rodar

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"

# Bloco A — sem Laya, sem torch, segundos
mlaya census --verify --emit-rubric     # 99 queries → censo + rubrica + relatório
mlaya sample --n 99 --seed 42           # gera repos/legacy/scripts/ + state/script_*.yml
mlaya card                              # evidence cards + orçamento de tokens

# Bloco B — Laya (baixa ~1 GB de pesos na primeira vez)
uv pip install laya
mlaya calibrate                         # modelo de custo de latência desta máquina
mlaya ask --run-id full99 --no-purpose  # ~3min45s para as 99 em CPU
mlaya decide --run-id full99            # árvore de decisão
mlaya baseline --run-id full99          # regressão logística vs Laya (~1 s)
mlaya report --run-id full99            # runs/full99/report.md

# Variante: Laya lendo o SQL bruto em janelas, em vez do cartão (~11 min)
mlaya ask --run-id sql99 --source sql
mlaya decide --run-id sql99 && mlaya report --run-id sql99
mlaya compare full99 sql99              # head-to-head sobre o mesmo gabarito
```

Auditoria e testes:

```bash
pytest                                   # 150 testes
mlaya census --verify                    # falha se alguma das 99 não parsear
mlaya features corpus/tpcds/query23.sql  # dump de features para conferência manual
mlaya card --check                       # valida orçamento sem escrever
```

---

## Decisões de projeto que valem nota

**Cascata de dialetos.** 99/99 parseiam com `spark → tsql`. O corpus é misto:
query67 usa `SELECT TOP` (T-SQL). Qual dialeto foi necessário é registrado como
um marcador de não-portabilidade — é informação de migração, não ruído.

**Grafo de joins em dois níveis.** *Footprint* (tabelas base, global) e
*complexidade estrutural* (por escopo, incluindo CTEs e derived tables) medem
coisas diferentes e não podem ser somadas. Ler `connected_components` global
como "risco de produto cartesiano" é errado: escopos separados *devem* ser
desconexos. Risco cartesiano é avaliado por escopo.

**Resolução de colunas sem schema.** TPC-DS deixa colunas de join sem
qualificação e usa convenção de abreviatura (`ss_item_sk` → `store_sales`). A
convenção é inferida genericamente dos nomes em escopo — iniciais, iniciais sem
sufixo de dimensão, truncamento (`inv_` → `inventory`) — com desempate pelo
restante do nome (`i_item_sk` → `item`, não `inventory`). Cobertura: **92.1%**;
os 7.9% restantes são ambiguidade real (`ws_` serve a `web_sales` e `web_site`) e
são **contados, nunca chutados**.

**Limiares vindos de percentis.** `mlaya census --emit-rubric` deriva cada
limiar de um percentil observado e registra qual. "Por que 40 linhas?" vira "por
que o percentil 66?" — uma pergunta que o time consegue responder.

**Bandas pelo split mais equilibrado.** Tercis puros quebram numa distribuição
discreta com pico: um terço do corpus empilhado em 5–6 pontos colapsaria a banda
`medium` num único valor, e um ponto de diferença decidiria o gabarito. O corte
escolhido é o mais próximo de terços iguais com `medium` cobrindo ≥2 valores —
aqui 29/39/31.

**Identidade pela query de origem, não pelo id.** O id sequencial é atribuído
pelo amostrador e é reaproveitado para outra query quando o tamanho da amostra
muda. Por isso `gold_judgements.yml` é chaveado por `query42`, e os JSONs de
resposta guardam a origem — sem isso, re-pontuar um run antigo o casa em
silêncio com o gabarito errado (foi o que aconteceu com os runs `r2` e
`ablation`, hoje descartados).

**Cobertura por script, não só por resposta.** As duas curvas estão no
relatório porque a diferença entre elas é a conclusão: no corte 0.70, 38% de
cobertura por resposta viram 21% por script — e com o intervalo de confiança ao
lado, porque a essa altura n já é pequeno demais para um número sozinho.

---

## Limitações declaradas

0. **O desenho não valida a pergunta de negócio.** O cartão entrega os fatos
   perguntados e o gabarito de complexidade é função dos mesmos números. As
   conclusões negativas valem para *este cartão e este prompt*; as positivas
   sobre automação não se sustentam. Ver "O que o experimento não pode
   concluir".
1. **Domínio único** — TPC-DS é analytics em SQL ANSI. Não cobre PL/SQL
   procedural, cursores, SQL dinâmico. A pipeline aceita um segundo corpus sem
   alteração estrutural.
2. **Julgamentos com blindagem mista** — `rewrite_strategy` e
   `needs_human_review` cobrem as 99, mas 89 foram escritos depois de um run
   existir em disco (sem consultá-lo). Blindagem procedimental, não estrutural.
   Um revisor humano discordando de julgamentos específicos muda esses números.
3. **O extrator é ponto único de falha** — todo o gabarito depende dele. Daí
   `census --verify`, a auditoria manual (que encontrou um bug real: CTEs sendo
   contados como tabelas-fonte) e o cruzamento `source_tables == graph_nodes` em
   99/99.
4. **CPU** — latências ~20× as do benchmark em T4 do README.
5. **Licença** — queries derivadas da spec TPC-DS; procedência em
   `repos/legacy/scripts/NOTICE.md`. Uso de avaliação interna. As cópias em
   `repos/legacy/scripts/*.sql` **não são versionadas**: são saída de
   `mlaya sample` a partir de `corpus/tpcds/` e se regeneram com um comando,
   o que limita a redistribuição sem custar reprodutibilidade.
