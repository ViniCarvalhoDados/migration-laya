# Censo do corpus — `corpus/tpcds`

**n = 99 scripts.** Extração 100% determinística (sqlglot). Nenhum modelo envolvido: estes números são o gabarito do estudo.

## 1. Saúde do parse

- Parseados: **99/99**
  - `spark`: 98
  - `tsql`: 1
- Nenhuma falha de parse.

- Predicados de join resolvidos: **89.1%** (399 resolvidos, 49 não resolvidos).
  Um predicado não resolvido é uma coluna que o extrator não conseguiu
  atribuir a uma fonte; ele é contado, nunca chutado.

## 2. Distribuição por feature

| feature | min | p25 | p33 | p50 | p66 | p75 | p90 | p95 | max | média | zeros |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `loc_code` | 14 | 29 | 34 | 44 | 56 | 67 | 105 | 134 | 305 | 56.778 | 0/99 |
| `statements` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1.04 | 0/99 |
| `source_tables` | 1 | 4 | 4 | 5 | 5 | 6 | 7 | 9 | 13 | 4.939 | 0/99 |
| `subquery_count` | 0 | 0 | 0 | 1 | 1 | 2 | 4 | 8 | 19 | 1.758 | 42/99 |
| `correlated_subquery_count` | 0 | 0 | 0 | 0 | 0 | 1 | 3 | 6 | 15 | 0.879 | 73/99 |
| `cte_count` | 0 | 0 | 0 | 0 | 0 | 1 | 3 | 3 | 6 | 0.707 | 69/99 |
| `window_function_count` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2 | 6 | 0.273 | 84/99 |
| `set_operation_count` | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 10 | 0.475 | 78/99 |
| `case_expression_count` | 0 | 0 | 0 | 0 | 0 | 1 | 4 | 5 | 48 | 1.323 | 70/99 |
| `max_nesting_depth` | 0 | 0 | 0 | 1 | 1 | 2 | 3 | 4 | 4 | 1.222 | 33/99 |
| `graph_nodes` | 1 | 4 | 4 | 5 | 5 | 6 | 7 | 9 | 13 | 4.939 | 0/99 |
| `graph_edges` | 0 | 2 | 3 | 3 | 5 | 6 | 7 | 9 | 15 | 4.03 | 6/99 |
| `graph_max_degree` | 0 | 2 | 2 | 3 | 3 | 3 | 4 | 5 | 9 | 2.838 | 6/99 |
| `graph_max_scope_sources` | 1 | 3 | 3 | 4 | 4 | 5 | 6 | 7 | 12 | 4.182 | 0/99 |

> `zeros` importa: quando a maioria dos scripts tem 0 de uma feature,
> o percentil baixo é 0 e o limiar da rubrica cai para 1 — ou seja,
> **ter** a feature já é o sinal, e não *quanto* dela se tem.

## 3. Histogramas

**loc_code**
```
      14-50     | ######################################## 61
      50-87     | ###############                          23
      87-123    | #####                                    8
     123-160    | ###                                      4
     160-196    |                                          0
     196-232    | #                                        1
     232-269    | #                                        1
     269-305    | #                                        1
```

**source_tables**
```
       1-2      | ###                                      4
       2-4      | ##############                           17
       4-6      | ######################################## 47
       6-7      | ##############                           16
       7-8      | #########                                10
       8-10     | ##                                       2
      10-12     | #                                        1
      12-13     | ##                                       2
```

**graph_edges**
```
       0-2      | ##########                               10
       2-4      | ######################################## 42
       4-6      | ####################                     21
       6-8      | ################                         17
       8-9      | ######                                   6
       9-11     | ##                                       2
      11-13     |                                          0
      13-15     | #                                        1
```

## 4. Rubrica derivada

_Cuts at <=4 / <=6 / rest, giving 31/37/31 scripts over n=99. Chosen as the split closest to equal thirds, with the middle band spanning at least two score values._

| feature | +1 a partir de | +2 a partir de | percentis usados |
|---|---|---|---|
| `loc_code` | 56 | 105 | p66=56 / p90=105 |
| `source_tables` | 5 | 7 | p66=5 / p90=7 |
| `subquery_count` | 1 | 4 | p50=1 / p90=4 |
| `cte_count` | 1 | 3 | p50=0 / p90=3 |
| `window_function_count` | 1 | — | p66=0 |
| `set_operation_count` | 1 | 2 | p66=0 / p90=2 |
| `max_nesting_depth` | 1 | — | p66=1 |
| `case_expression_count` | 1 | 4 | p66=0 / p90=4 |
| `join_graph.edges` | 5 | 7 | p66=5 / p90=7 |
| `join_graph.max_degree` | 4 | — | p90=4 |
| `join_graph.max_scope_sources` | 4 | 6 | p66=4 / p90=6 |

**Regras fixas (+1 cada):**

- `multi_statement` — more than one statement in the file
- `cross_join_risk` — a source in some scope joins to nothing
- `nonportable_syntax` — engine-specific syntax detected
- `correlated_subquery` — correlated subquery present

**Bandas:** low `[0, 4]` · medium `[5, 6]` · high `[7, None]`

## 5. Distribuição de complexidade

| banda | scripts | % |
|---|---|---|
| low | 31 | 31% |
| medium | 37 | 37% |
| high | 31 | 31% |

## 6. Os 12 scripts mais complexos

| # | script | pontos | banda | loc | fontes | subq | CTE | win | setop | arestas |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `query77` | **15** | high | 105 | 9 | 1 | 6 | 0 | 2 | 10 |
| 2 | `query80` | **15** | high | 104 | 12 | 1 | 3 | 0 | 2 | 10 |
| 3 | `query14` | **14** | high | 243 | 5 | 19 | 4 | 0 | 10 | 6 |
| 4 | `query23` | **14** | high | 134 | 6 | 14 | 6 | 0 | 2 | 7 |
| 5 | `query33` | **13** | high | 64 | 6 | 4 | 3 | 0 | 2 | 9 |
| 6 | `query56` | **13** | high | 67 | 6 | 4 | 3 | 0 | 2 | 9 |
| 7 | `query60` | **13** | high | 65 | 6 | 4 | 3 | 0 | 2 | 9 |
| 8 | `query4` | **12** | high | 151 | 5 | 0 | 1 | 0 | 2 | 6 |
| 9 | `query5` | **12** | high | 126 | 10 | 4 | 3 | 0 | 5 | 1 |
| 10 | `query66` | **12** | high | 305 | 6 | 1 | 0 | 0 | 1 | 8 |
| 11 | `query24` | **11** | high | 94 | 6 | 2 | 2 | 0 | 0 | 5 |
| 12 | `query49` | **11** | high | 132 | 7 | 6 | 0 | 6 | 2 | 6 |

## 7. Os 8 mais simples

| # | script | pontos | banda | loc | fontes | arestas | forma |
|---|---|---|---|---|---|---|---|
| 1 | `query55` | 0 | low | 16 | 3 | 2 | star |
| 2 | `query52` | 0 | low | 19 | 3 | 2 | star |
| 3 | `query42` | 0 | low | 20 | 3 | 2 | star |
| 4 | `query3` | 0 | low | 18 | 3 | 2 | star |
| 5 | `query96` | 1 | low | 14 | 4 | 3 | star |
| 6 | `query15` | 1 | low | 19 | 4 | 3 | snowflake |
| 7 | `query98` | 2 | low | 27 | 3 | 2 | star |
| 8 | `query82` | 2 | low | 21 | 4 | 3 | snowflake |

## 8. Marcadores de não-portabilidade

| marcador | scripts |
|---|---|
| `interval_arithmetic` | 16 |
| `rollup` | 11 |
| `backtick_identifier` | 8 |
| `grouping_fn` | 4 |
| `stddev_samp` | 3 |
| `select_top` | 1 |
| `requires_dialect:tsql` | 1 |

## 9. Forma do join mais largo

| forma | scripts |
|---|---|
| star | 71 |
| snowflake | 13 |
| mesh | 8 |
| disconnected | 5 |
| single | 2 |
