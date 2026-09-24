# Revisões metodológicas

Histórico das revisões críticas do estudo. Cada revisão é um arquivo imutável,
nomeado pela data e hora em que foi feita e ancorado no commit que avaliou.
Quando um ponto é resolvido, **não se edita a revisão antiga**: o estado muda na
tabela abaixo, e a revisão seguinte registra como foi verificado.

## Convenção

- Arquivo: `AAAA-MM-DD_HHMM_<tema>.md`, com horário local (−03:00).
- Cada ponto tem um id estável `R<nn>` e segue com o mesmo id nas revisões
  seguintes, mesmo depois de resolvido.
- Severidade:
  - **grave**: muda uma conclusão publicada.
  - **moderado**: enfraquece uma conclusão ou a reprodutibilidade.
  - **menor**: afeta clareza ou consistência.
- Estado:
  - `aberto`: nada foi feito ainda.
  - `em andamento`: há trabalho, mas ainda não foi verificado.
  - `resolvido`: verificado numa revisão posterior.
  - `aceito`: a limitação foi reconhecida e documentada, e não será corrigida.

## Revisões

| data e hora | commit avaliado | tema | arquivo |
|---|---|---|---|
| 2026-09-23 23:48 | `b6fc738` | Metodologia, conclusões e pontos em aberto | [2026-09-23_2348_revisao-metodologica.md](2026-09-23_2348_revisao-metodologica.md) |

## Pontos de revisão

| id | severidade | ponto | estado | aberto em | última revisão |
|---|---|---|---|---|---|
| R01 | grave | A comparação Laya × LR clean é assimétrica: o cartão entrega o fato à LR não | resolvido | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R02 | grave | Complexidade não bate o baseline trivial `loc_code` | resolvido | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R03 | grave | E8, E10, E11 e E12 não são reproduzíveis a partir do que está commitado | em andamento | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R04 | grave | O caso de custo não mede o acerto do LLM | aberto | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R05 | moderado | Near-duplicates atravessam os splits de avaliação | aceito | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R06 | moderado | A dispersão entre splits sobrepostos é reportada como IC | em andamento | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R07 | moderado | Caminhos de análise demais para n = 99 | aceito | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R08 | moderado | A árvore de decisão usa confiança não calibrada | aberto | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R09 | moderado | `rewrite_strategy` foi avaliada só por argmax | aceito | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R10 | moderado | Não foi verificado se várias perguntas na mesma chamada interferem entre si ou são truncadas | aberto | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R11 | menor | A procedência do gabarito se contradiz entre arquivos | aberto | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R12 | menor | O teste pré-registrado do E11 não teve resultado reportado | resolvido | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R13 | menor | "6% de erro de 2 bandas" aparece sem baseline | resolvido | 2026-09-23 23:48 | 2026-09-24 00:52 |
| R14 | moderado | Validade de construto: a rubrica mede tamanho, o corpus é TPC-DS e o gabarito tem um anotador só | aceito | 2026-09-23 23:48 | 2026-09-24 00:52 |

## Resolução de 2026-09-24 00:52 — commit `37207df` e seguinte

O que mudou, ponto a ponto:

- **R01 resolvido.** `mlaya paired` entrou no repositório e reporta as duas
  variantes da regressão em toda tabela. Confirmado o que a revisão previu: com
  a mesma informação que o cartão, o Laya empata em `has_subquery` (+3,3, p05–p95
  de −4 a +14) e perde em `has_window_function` (−11,3) e `multi_source` (−18,1).
  O "+15,2" saiu do README, de `docs/experiments.md` e do relatório visual.
- **R02 resolvido.** `mlaya business` passou a imprimir as regras triviais.
  Reproduzido com folga: `loc_code` sozinho dá **AUC 0,98 e 72% em hold-out**,
  contra 0,87 e 54% do Laya, e erra duas bandas em 2% contra 8%. A conclusão nº 1
  do README foi reescrita para "contar linhas é melhor que o modelo".
- **R03 em andamento.** E8, E10 e E11 agora saem de `mlaya paired` e
  `mlaya business`, commitados, com as saídas em `runs/*/paired_*.yml` e
  `runs/business/business.yml`. **E12 continua sem script de custo** — o ponto só
  fecha quando ele existir.
- **R06 em andamento.** O rótulo "IC90" foi trocado por "p05–p95" em todos os
  lugares, com a ressalva explícita de que metades sobrepostas subestimam a
  variância. O *corrected resampled t-test* não foi implementado.
- **R12 resolvido.** O resultado da hipótese pré-registrada está reportado no
  E11: a hipótese de eco lexical **não se confirmou** (p1 54%, p4 44%).
- **R13 resolvido.** Toda estrutura de erro agora aparece ao lado do preditor
  constante (0% de erro de duas bandas) e do `loc_code` (2%).
- **R05, R07, R09, R14 aceitos.** Estão declarados em
  [`docs/limitations.md`](../docs/limitations.md), com o motivo de cada um. R05
  em particular favorece o comparador, não o modelo, então a conclusão de E13 é
  conservadora.
- **R04, R08, R10, R11 seguem abertos.**

Dois achados fora da revisão apareceram no caminho e foram corrigidos: o
relatório lia a latência do YAML do script (que guarda o último run, não o
próprio), e o grid de cortes da complexidade arredondava a 3 casas enquanto o
corte era aplicado ao valor cru. Os dois estão fixados por teste.
