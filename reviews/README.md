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
| R01 | grave | A comparação Laya × LR clean é assimétrica: o cartão entrega o fato à LR não | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R02 | grave | Complexidade não bate o baseline trivial `loc_code` | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R03 | grave | E8, E10, E11 e E12 não são reproduzíveis a partir do que está commitado | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R04 | grave | O caso de custo não mede o acerto do LLM | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R05 | moderado | Near-duplicates atravessam os splits de avaliação | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R06 | moderado | A dispersão entre splits sobrepostos é reportada como IC | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R07 | moderado | Caminhos de análise demais para n = 99 | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R08 | moderado | A árvore de decisão usa confiança não calibrada | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R09 | moderado | `rewrite_strategy` foi avaliada só por argmax | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R10 | moderado | Não foi verificado se várias perguntas na mesma chamada interferem entre si ou são truncadas | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R11 | menor | A procedência do gabarito se contradiz entre arquivos | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R12 | menor | O teste pré-registrado do E11 não teve resultado reportado | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R13 | menor | "6% de erro de 2 bandas" aparece sem baseline | aberto | 2026-09-23 23:48 | 2026-09-23 23:48 |
| R14 | moderado | Validade de construto: a rubrica mede tamanho, o corpus é TPC-DS e o gabarito tem um anotador só | aceito | 2026-09-23 23:48 | 2026-09-23 23:48 |
