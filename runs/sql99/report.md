# Resultado — run `sql99`

99 scripts · 6 perguntas · modelo `convaiinnovations/laya` em `cpu`

**Input:** **SQL bruto**, partido em janelas do tamanho do contexto.

> As regras de agregação entre janelas estão pré-registradas em
> `chunks.AGGREGATION`, escritas antes de qualquer resultado. `multi_source`
> pede uma contagem global de tabelas e é **estruturalmente irrespondível por
> janela** — fica no run para que o custo do fatiamento apareça nos números.

> **Aviso emitido pelo próprio runtime ao carregar o checkpoint:**
>
> `laya: this checkpoint ships invalid temperatures or values outside [0.5, 5]; using choice:11+=0.10058280825614929 -> 0.5. Treat confidence from the affected entries as uncalibrated.`
>
> Ou seja, os percentuais de confiança abaixo são declaradamente não
> calibrados pelo fornecedor. Isso não invalida as respostas — invalida
> lê-las pelo valor de face. É exatamente o que a seção de calibração mede.

## 1. Manchete

| desfecho | scripts | % | significado |
|---|---|---|---|
| `AUTO` | 3 | 3% | classificado sem humano |
| `HUMAN_REVIEW` | 16 | 16% | humano confere — erro pequeno ou baixa confiança |
| `ESCALATE` | 80 | 81% | **erro confiante** em fato verificável pelo AST |

**3 de 99 scripts (3%) passariam sem revisão humana.**

**80 script(s) erraram com alta confiança um fato que o AST já conhecia** — o modo de falha que quebra confiança em produção.

## 2. Representatividade da amostra

- 99 de 99 scripts do corpus.
- Bandas: {'low': 31, 'medium': 37, 'high': 31}
- Pontos de rubrica cobertos: [0, 15] de [0, 15] do corpus.

| script | origem | banda gold | pontos | percentil loc | percentil fontes |
|---|---|---|---|---|---|
| `script_01` | query42 | low | 0 | p10 | p21 |
| `script_02` | query55 | low | 0 | p2 | p21 |
| `script_03` | query3 | low | 0 | p3 | p21 |
| `script_04` | query52 | low | 0 | p5 | p21 |
| `script_05` | query96 | low | 1 | p1 | p45 |
| `script_06` | query15 | low | 1 | p5 | p45 |
| `script_07` | query37 | low | 2 | p14 | p45 |
| `script_08` | query22 | low | 2 | p10 | p45 |
| `script_09` | query43 | low | 2 | p60 | p21 |
| `script_10` | query20 | low | 2 | p26 | p21 |
| `script_11` | query82 | low | 2 | p14 | p45 |
| `script_12` | query98 | low | 2 | p23 | p21 |
| `script_13` | query12 | low | 2 | p26 | p21 |
| `script_14` | query65 | low | 3 | p36 | p45 |
| `script_15` | query48 | low | 3 | p32 | p69 |
| `script_16` | query26 | low | 3 | p19 | p69 |
| `script_17` | query7 | low | 3 | p19 | p69 |
| `script_18` | query86 | low | 3 | p19 | p21 |
| `script_19` | query97 | low | 3 | p40 | p21 |
| `script_20` | query93 | low | 3 | p14 | p21 |
| `script_21` | query92 | low | 4 | p14 | p21 |
| `script_22` | query84 | low | 4 | p10 | p85 |
| `script_23` | query27 | low | 4 | p21 | p69 |
| `script_24` | query81 | low | 4 | p65 | p45 |
| `script_25` | query79 | low | 4 | p34 | p69 |
| `script_26` | query36 | low | 4 | p28 | p45 |
| `script_27` | query1 | low | 4 | p16 | p45 |
| `script_28` | query41 | low | 4 | p75 | p2 |
| `script_29` | query30 | low | 4 | p59 | p45 |
| `script_30` | query90 | low | 4 | p21 | p45 |
| `script_31` | query32 | low | 4 | p10 | p21 |
| `script_32` | query34 | medium | 5 | p54 | p69 |
| `script_33` | query21 | medium | 5 | p38 | p45 |
| `script_34` | query62 | medium | 5 | p52 | p69 |
| `script_35` | query51 | medium | 5 | p64 | p21 |
| `script_36` | query67 | medium | 5 | p46 | p45 |
| `script_37` | query73 | medium | 5 | p40 | p69 |
| `script_38` | query13 | medium | 5 | p48 | p85 |
| `script_39` | query63 | medium | 5 | p52 | p45 |
| `script_40` | query40 | medium | 5 | p34 | p69 |
| `script_41` | query45 | medium | 5 | p23 | p69 |
| `script_42` | query6 | medium | 5 | p16 | p69 |
| `script_43` | query44 | medium | 5 | p62 | p4 |
| `script_44` | query53 | medium | 5 | p54 | p45 |
| `script_45` | query19 | medium | 5 | p28 | p85 |
| `script_46` | query50 | medium | 5 | p78 | p45 |
| `script_47` | query89 | medium | 5 | p43 | p45 |
| `script_48` | query11 | medium | 6 | p89 | p45 |
| `script_49` | query87 | medium | 6 | p10 | p69 |
| `script_50` | query99 | medium | 6 | p52 | p69 |
| `script_51` | query69 | medium | 6 | p56 | p93 |
| `script_52` | query18 | medium | 6 | p38 | p85 |
| `script_53` | query16 | medium | 6 | p31 | p69 |
| `script_54` | query46 | medium | 6 | p48 | p85 |
| `script_55` | query59 | medium | 6 | p84 | p21 |
| `script_56` | query29 | medium | 6 | p43 | p85 |
| `script_57` | query94 | medium | 6 | p24 | p69 |
| `script_58` | query85 | medium | 6 | p63 | p93 |
| `script_59` | query91 | medium | 6 | p30 | p93 |
| `script_60` | query25 | medium | 6 | p45 | p85 |
| `script_61` | query38 | medium | 6 | p30 | p69 |
| `script_62` | query71 | medium | 6 | p57 | p85 |
| `script_63` | query68 | medium | 6 | p45 | p85 |
| `script_64` | query74 | medium | 6 | p77 | p45 |
| `script_65` | query57 | medium | 6 | p75 | p45 |
| `script_66` | query70 | medium | 6 | p43 | p21 |
| `script_67` | query28 | medium | 6 | p62 | p2 |
| `script_68` | query47 | medium | 6 | p80 | p45 |
| `script_69` | query76 | high | 7 | p68 | p69 |
| `script_70` | query78 | high | 7 | p85 | p93 |
| `script_71` | query31 | high | 7 | p81 | p45 |
| `script_72` | query10 | high | 7 | p70 | p93 |
| `script_73` | query95 | high | 7 | p36 | p69 |
| `script_74` | query9 | high | 7 | p71 | p4 |
| `script_75` | query17 | high | 7 | p66 | p85 |
| `script_76` | query2 | high | 7 | p83 | p21 |
| `script_77` | query8 | high | 7 | p98 | p69 |
| `script_78` | query88 | high | 7 | p86 | p45 |
| `script_79` | query35 | high | 8 | p69 | p93 |
| `script_80` | query83 | high | 9 | p82 | p69 |
| `script_81` | query61 | high | 9 | p56 | p93 |
| `script_82` | query58 | high | 9 | p80 | p69 |
| `script_83` | query72 | high | 9 | p59 | p97 |
| `script_84` | query39 | high | 10 | p92 | p45 |
| `script_85` | query54 | high | 10 | p68 | p95 |
| `script_86` | query64 | high | 11 | p93 | p100 |
| `script_87` | query49 | high | 11 | p95 | p93 |
| `script_88` | query24 | high | 11 | p88 | p85 |
| `script_89` | query75 | high | 11 | p87 | p95 |
| `script_90` | query66 | high | 12 | p100 | p85 |
| `script_91` | query4 | high | 12 | p97 | p69 |
| `script_92` | query5 | high | 12 | p94 | p98 |
| `script_93` | query60 | high | 13 | p75 | p85 |
| `script_94` | query56 | high | 13 | p76 | p85 |
| `script_95` | query33 | high | 13 | p72 | p85 |
| `script_96` | query14 | high | 14 | p99 | p69 |
| `script_97` | query23 | high | 14 | p96 | p85 |
| `script_98` | query80 | high | 15 | p90 | p99 |
| `script_99` | query77 | high | 15 | p91 | p97 |

## 3. Script a script

Confiança = maior massa de probabilidade. ✓ acerto · ✗ erro.

| script | desfecho | `migration_complexity` | `rewrite_strategy` | `has_subquery` | `has_window_function` | `multi_source` | `needs_human_review` |
|---|---|---|---|---|---|---|---|
| `script_01` | **ESCALATE** | ✗ medium · 49% | ✗ redesign · 33% | ✗ True · 90% | ✓ False · 76% | ✗ True · 97% | ✓ False · 74% |
| `script_02` | **ESCALATE** | ✗ medium · 61% | ✓ lift_and_shift · 44% | ✗ True · 100% | ✓ False · 76% | ✗ True · 96% | ✓ False · 61% |
| `script_03` | **ESCALATE** | ✗ medium · 53% | ✗ refactor · 32% | ✗ True · 92% | ✓ False · 83% | ✗ True · 94% | ✓ False · 68% |
| `script_04` | **ESCALATE** | ✗ medium · 58% | ✗ refactor · 31% | ✗ True · 94% | ✓ False · 82% | ✗ True · 93% | ✓ False · 82% |
| `script_05` | **ESCALATE** | ✗ medium · 63% | ✓ lift_and_shift · 51% | ✗ True · 92% | ✓ False · 87% | ✓ True · 95% | ✗ True · 63% |
| `script_06` | **ESCALATE** | ✗ medium · 68% | ✗ refactor · 31% | ✗ True · 95% | ✓ False · 83% | ✓ True · 94% | ✓ False · 78% |
| `script_07` | **ESCALATE** | ✗ medium · 61% | ✗ refactor · 45% | ✗ True · 90% | ✗ True · 71% | ✓ True · 95% | ✗ True · 79% |
| `script_08` | **ESCALATE** | ✗ medium · 64% | ✗ refactor · 44% | ✗ True · 100% | ✓ False · 71% | ✓ True · 99% | ✓ True · 60% |
| `script_09` | **ESCALATE** | ✗ medium · 69% | ✓ refactor · 38% | ✗ True · 100% | ✓ False · 64% | ✗ True · 100% | ✓ True · 93% |
| `script_10` | **ESCALATE** | ✗ medium · 66% | ✗ refactor · 47% | ✗ True · 94% | ✓ True · 82% | ✗ True · 98% | ✗ True · 90% |
| `script_11` | **ESCALATE** | ✗ medium · 60% | ✗ refactor · 45% | ✗ True · 86% | ✗ True · 81% | ✓ True · 95% | ✗ True · 87% |
| `script_12` | **ESCALATE** | ✗ medium · 59% | ✗ refactor · 41% | ✗ True · 100% | ✓ True · 88% | ✗ True · 100% | ✗ True · 94% |
| `script_13` | **ESCALATE** | ✗ medium · 64% | ✗ refactor · 52% | ✗ True · 94% | ✓ True · 90% | ✗ True · 97% | ✗ True · 91% |
| `script_14` | REVIEW | ✗ medium · 57% | ✗ lift_and_shift · 37% | ✓ True · 97% | ✗ True · 83% | ✓ True · 98% | ✓ True · 91% |
| `script_15` | **ESCALATE** | ✗ medium · 61% | ✓ refactor · 35% | ✗ True · 98% | ✗ True · 68% | ✓ True · 100% | ✓ True · 84% |
| `script_16` | **ESCALATE** | ✗ medium · 64% | ✗ refactor · 38% | ✗ True · 92% | ✓ False · 74% | ✓ True · 91% | ✗ True · 61% |
| `script_17` | **ESCALATE** | ✗ medium · 62% | ✗ refactor · 39% | ✗ True · 97% | ✓ False · 78% | ✓ True · 92% | ✗ True · 52% |
| `script_18` | **ESCALATE** | ✗ medium · 58% | ✓ refactor · 34% | ✗ True · 100% | ✓ True · 100% | ✗ True · 91% | ✓ True · 89% |
| `script_19` | **ESCALATE** | ✗ medium · 61% | ✓ refactor · 42% | ✗ True · 100% | ✗ True · 100% | ✗ True · 100% | ✓ True · 89% |
| `script_20` | **ESCALATE** | ✗ medium · 52% | ✓ refactor · 33% | ✓ True · 92% | ✗ True · 84% | ✗ True · 94% | ✓ True · 52% |
| `script_21` | **ESCALATE** | ✗ medium · 55% | ✗ redesign · 44% | ✓ True · 94% | ✗ True · 86% | ✗ True · 92% | ✓ True · 62% |
| `script_22` | **ESCALATE** | ✗ medium · 74% | ✗ refactor · 37% | ✗ True · 95% | ✓ False · 87% | ✓ True · 100% | ✗ True · 78% |
| `script_23` | **ESCALATE** | ✗ medium · 62% | ✓ lift_and_shift · 45% | ✗ True · 95% | ✓ False · 86% | ✓ True · 88% | ✓ True · 84% |
| `script_24` | **ESCALATE** | ✗ medium · 56% | ✓ refactor · 41% | ✓ True · 96% | ✗ True · 92% | ✓ True · 94% | ✓ True · 84% |
| `script_25` | **ESCALATE** | ✗ medium · 59% | ✓ lift_and_shift · 41% | ✓ True · 100% | ✗ True · 95% | ✓ True · 100% | ✗ True · 92% |
| `script_26` | **ESCALATE** | ✗ medium · 63% | ✗ lift_and_shift · 74% | ✗ True · 97% | ✓ True · 94% | ✓ True · 89% | ✓ True · 73% |
| `script_27` | REVIEW | ✗ medium · 60% | ✓ refactor · 38% | ✓ True · 92% | ✗ True · 55% | ✓ True · 91% | ✓ True · 82% |
| `script_28` | **ESCALATE** | ✗ medium · 67% | ✓ refactor · 37% | ✓ True · 95% | ✗ True · 67% | ✗ True · 96% | ✓ True · 89% |
| `script_29` | **ESCALATE** | ✗ medium · 53% | ✓ refactor · 35% | ✓ True · 95% | ✗ True · 94% | ✓ True · 96% | ✓ True · 85% |
| `script_30` | **ESCALATE** | ✗ medium · 61% | ✓ lift_and_shift · 33% | ✓ True · 97% | ✗ True · 87% | ✓ True · 95% | ✗ True · 79% |
| `script_31` | **ESCALATE** | ✗ medium · 56% | ✓ refactor · 32% | ✓ True · 84% | ✗ True · 79% | ✗ True · 90% | ✗ False · 59% |
| `script_32` | **ESCALATE** | ✓ medium · 64% | ✗ refactor · 40% | ✓ True · 100% | ✗ True · 98% | ✓ True · 100% | ✗ True · 92% |
| `script_33` | REVIEW | ✓ medium · 61% | ✗ refactor · 36% | ✓ True · 100% | ✗ True · 83% | ✓ True · 97% | ✓ True · 87% |
| `script_34` | **ESCALATE** | ✓ medium · 59% | ✓ refactor · 28% | ✗ True · 92% | ✗ True · 73% | ✓ True · 93% | ✓ True · 68% |
| `script_35` | **ESCALATE** | ✓ medium · 58% | ✓ refactor · 32% | ✓ True · 99% | ✓ True · 100% | ✗ True · 96% | ✓ True · 90% |
| `script_36` | **AUTO** | ✓ medium · 62% | ✓ refactor · 34% | ✓ True · 100% | ✓ True · 97% | ✓ True · 100% | ✓ True · 86% |
| `script_37` | **ESCALATE** | ✓ medium · 62% | ✗ refactor · 35% | ✓ True · 100% | ✗ True · 93% | ✓ True · 100% | ✗ True · 96% |
| `script_38` | **ESCALATE** | ✓ medium · 63% | ✓ refactor · 33% | ✗ True · 94% | ✗ True · 95% | ✓ True · 99% | ✓ True · 92% |
| `script_39` | **AUTO** | ✓ medium · 63% | ✗ refactor · 36% | ✓ True · 92% | ✓ True · 97% | ✓ True · 89% | ✗ True · 87% |
| `script_40` | **ESCALATE** | ✓ medium · 57% | ✗ lift_and_shift · 35% | ✗ True · 95% | ✗ True · 96% | ✓ True · 100% | ✓ True · 97% |
| `script_41` | REVIEW | ✓ medium · 58% | ✓ refactor · 37% | ✓ True · 94% | ✗ True · 70% | ✓ True · 96% | ✓ True · 84% |
| `script_42` | **ESCALATE** | ✓ medium · 47% | ✗ lift_and_shift · 36% | ✓ True · 96% | ✗ True · 85% | ✓ True · 100% | ✓ True · 57% |
| `script_43` | **ESCALATE** | ✓ medium · 60% | ✗ lift_and_shift · 36% | ✓ True · 100% | ✓ True · 83% | ✗ True · 100% | ✓ True · 86% |
| `script_44` | **AUTO** | ✓ medium · 65% | ✗ refactor · 42% | ✓ True · 92% | ✓ True · 97% | ✓ True · 93% | ✗ True · 89% |
| `script_45` | **ESCALATE** | ✓ medium · 50% | ✗ refactor · 29% | ✗ True · 97% | ✓ False · 82% | ✓ True · 100% | ✗ True · 93% |
| `script_46` | **ESCALATE** | ✓ medium · 65% | ✓ refactor · 34% | ✗ True · 94% | ✗ True · 81% | ✓ True · 98% | ✓ True · 82% |
| `script_47` | REVIEW | ✓ medium · 58% | ✗ refactor · 30% | ✓ True · 94% | ✓ True · 85% | ✓ True · 100% | ✗ True · 94% |
| `script_48` | **ESCALATE** | ✓ medium · 64% | ✗ lift_and_shift · 34% | ✗ True · 99% | ✗ True · 97% | ✓ True · 89% | ✓ True · 78% |
| `script_49` | REVIEW | ✓ medium · 70% | ✓ refactor · 35% | ✓ True · 85% | ✗ True · 79% | ✓ True · 99% | ✗ False · 73% |
| `script_50` | **ESCALATE** | ✓ medium · 60% | ✓ refactor · 32% | ✗ True · 95% | ✗ True · 82% | ✓ True · 92% | ✓ True · 66% |
| `script_51` | **ESCALATE** | ✓ medium · 57% | ✓ refactor · 36% | ✓ True · 100% | ✗ True · 91% | ✓ True · 100% | ✓ True · 95% |
| `script_52` | **ESCALATE** | ✓ medium · 67% | ✗ refactor · 36% | ✗ True · 97% | ✗ True · 100% | ✓ True · 95% | ✓ True · 96% |
| `script_53` | **ESCALATE** | ✓ medium · 59% | ✗ lift_and_shift · 42% | ✓ True · 96% | ✗ True · 85% | ✓ True · 94% | ✓ True · 86% |
| `script_54` | **ESCALATE** | ✓ medium · 65% | ✗ refactor · 47% | ✓ True · 100% | ✗ True · 89% | ✓ True · 100% | ✗ True · 100% |
| `script_55` | **ESCALATE** | ✓ medium · 65% | ✓ refactor · 42% | ✓ True · 100% | ✗ True · 95% | ✗ True · 96% | ✓ True · 75% |
| `script_56` | **ESCALATE** | ✓ medium · 59% | ✗ refactor · 40% | ✗ True · 98% | ✗ True · 91% | ✓ True · 100% | ✗ True · 95% |
| `script_57` | REVIEW | ✓ medium · 58% | ✗ lift_and_shift · 38% | ✓ True · 96% | ✗ True · 64% | ✓ True · 94% | ✓ True · 90% |
| `script_58` | **ESCALATE** | ✓ medium · 60% | ✓ refactor · 36% | ✗ True · 97% | ✗ True · 83% | ✓ True · 98% | ✓ True · 93% |
| `script_59` | **ESCALATE** | ✓ medium · 67% | ✗ refactor · 39% | ✗ True · 100% | ✗ True · 96% | ✓ True · 100% | ✗ True · 95% |
| `script_60` | **ESCALATE** | ✓ medium · 59% | ✗ refactor · 43% | ✗ True · 100% | ✗ True · 86% | ✓ True · 100% | ✗ True · 93% |
| `script_61` | **ESCALATE** | ✗ high · 45% | ✗ lift_and_shift · 55% | ✓ True · 92% | ✗ True · 93% | ✓ True · 100% | ✓ True · 85% |
| `script_62` | **ESCALATE** | ✓ medium · 61% | ✗ refactor · 36% | ✓ True · 100% | ✗ True · 100% | ✓ True · 100% | ✗ True · 88% |
| `script_63` | **ESCALATE** | ✓ medium · 62% | ✗ refactor · 40% | ✓ True · 100% | ✗ True · 90% | ✓ True · 100% | ✗ True · 97% |
| `script_64` | **ESCALATE** | ✓ medium · 59% | ✓ refactor · 31% | ✗ True · 100% | ✗ True · 100% | ✓ True · 100% | ✓ True · 66% |
| `script_65` | **ESCALATE** | ✓ medium · 56% | ✓ refactor · 40% | ✗ True · 97% | ✓ True · 89% | ✓ True · 99% | ✓ True · 83% |
| `script_66` | **ESCALATE** | ✓ medium · 61% | ✗ manual_rewrite · 32% | ✓ True · 96% | ✓ True · 100% | ✗ True · 91% | ✓ True · 89% |
| `script_67` | **ESCALATE** | ✓ medium · 60% | ✓ refactor · 54% | ✓ True · 94% | ✗ True · 100% | ✗ True · 100% | ✓ True · 90% |
| `script_68` | **ESCALATE** | ✓ medium · 59% | ✓ refactor · 35% | ✗ True · 98% | ✓ True · 100% | ✓ True · 100% | ✓ True · 86% |
| `script_69` | **ESCALATE** | ✗ medium · 62% | ✓ lift_and_shift · 28% | ✓ True · 100% | ✗ True · 100% | ✓ True · 100% | ✗ True · 93% |
| `script_70` | **ESCALATE** | ✗ medium · 60% | ✓ refactor · 44% | ✗ True · 100% | ✗ True · 91% | ✓ True · 94% | ✓ True · 91% |
| `script_71` | **ESCALATE** | ✗ medium · 61% | ✓ refactor · 43% | ✗ True · 100% | ✗ True · 93% | ✓ True · 97% | ✓ True · 89% |
| `script_72` | REVIEW | ✗ medium · 60% | ✗ manual_rewrite · 44% | ✓ True · 93% | ✗ True · 83% | ✓ True · 96% | ✓ True · 89% |
| `script_73` | **ESCALATE** | ✗ medium · 52% | ✓ refactor · 37% | ✓ True · 99% | ✗ True · 100% | ✓ True · 100% | ✓ True · 94% |
| `script_74` | REVIEW | ✗ medium · 63% | ✗ refactor · 36% | ✓ True · 93% | ✗ True · 78% | ✗ True · 83% | ✓ True · 78% |
| `script_75` | **ESCALATE** | ✗ medium · 60% | ✗ refactor · 30% | ✗ True · 97% | ✗ True · 95% | ✓ True · 93% | ✓ True · 84% |
| `script_76` | **ESCALATE** | ✗ medium · 64% | ✓ refactor · 36% | ✓ True · 100% | ✗ True · 100% | ✗ True · 100% | ✓ True · 90% |
| `script_77` | **ESCALATE** | ✗ medium · 64% | ✓ refactor · 41% | ✓ True · 100% | ✗ True · 100% | ✓ True · 100% | ✓ True · 100% |
| `script_78` | **ESCALATE** | ✗ medium · 66% | ✓ refactor · 38% | ✓ True · 95% | ✗ True · 90% | ✓ True · 100% | ✓ True · 80% |
| `script_79` | REVIEW | ✗ medium · 60% | ✗ manual_rewrite · 44% | ✓ True · 94% | ✗ True · 82% | ✓ True · 94% | ✓ True · 86% |
| `script_80` | **ESCALATE** | ✗ medium · 60% | ✓ refactor · 54% | ✓ True · 96% | ✗ True · 97% | ✓ True · 100% | ✓ True · 84% |
| `script_81` | **ESCALATE** | ✗ medium · 60% | ✗ refactor · 27% | ✓ True · 99% | ✗ True · 96% | ✓ True · 97% | ✗ True · 89% |
| `script_82` | REVIEW | ✗ medium · 57% | ✓ refactor · 50% | ✓ True · 100% | ✗ True · 83% | ✓ True · 100% | ✓ True · 84% |
| `script_83` | **ESCALATE** | ✗ medium · 58% | ✓ refactor · 30% | ✗ True · 89% | ✗ True · 76% | ✓ True · 100% | ✓ True · 86% |
| `script_84` | REVIEW | ✗ medium · 57% | ✗ lift_and_shift · 59% | ✓ True · 100% | ✗ True · 77% | ✓ True · 91% | ✓ True · 85% |
| `script_85` | **ESCALATE** | ✗ medium · 63% | ✓ refactor · 40% | ✓ True · 100% | ✗ True · 92% | ✓ True · 100% | ✓ True · 91% |
| `script_86` | **ESCALATE** | ✗ medium · 63% | ✗ refactor · 64% | ✗ True · 99% | ✗ True · 100% | ✓ True · 97% | ✓ True · 93% |
| `script_87` | REVIEW | ✗ medium · 66% | ✗ refactor · 40% | ✓ True · 96% | ✓ True · 89% | ✓ True · 96% | ✓ True · 92% |
| `script_88` | **ESCALATE** | ✗ medium · 60% | ✓ refactor · 40% | ✓ True · 100% | ✗ True · 100% | ✓ True · 100% | ✓ True · 97% |
| `script_89` | REVIEW | ✗ medium · 62% | ✓ refactor · 32% | ✓ True · 98% | ✗ True · 77% | ✓ True · 97% | ✓ True · 88% |
| `script_90` | **ESCALATE** | ✗ medium · 60% | ✓ refactor · 41% | ✓ True · 100% | ✗ True · 100% | ✓ True · 100% | ✓ True · 93% |
| `script_91` | **ESCALATE** | ✗ medium · 65% | ✗ refactor · 40% | ✗ True · 100% | ✗ True · 100% | ✓ True · 95% | ✓ True · 96% |
| `script_92` | **ESCALATE** | ✗ medium · 58% | ✗ refactor · 52% | ✓ True · 97% | ✗ True · 94% | ✓ True · 96% | ✓ True · 93% |
| `script_93` | **ESCALATE** | ✗ medium · 59% | ✓ refactor · 39% | ✓ True · 100% | ✗ True · 95% | ✓ True · 99% | ✓ True · 92% |
| `script_94` | **ESCALATE** | ✗ medium · 60% | ✓ refactor · 38% | ✓ True · 100% | ✗ True · 100% | ✓ True · 100% | ✓ True · 88% |
| `script_95` | **ESCALATE** | ✗ medium · 60% | ✓ refactor · 39% | ✓ True · 100% | ✗ True · 90% | ✓ True · 97% | ✓ True · 91% |
| `script_96` | **ESCALATE** | ✗ medium · 61% | ✗ refactor · 50% | ✓ True · 93% | ✗ True · 95% | ✓ True · 100% | ✓ True · 92% |
| `script_97` | **ESCALATE** | ✗ medium · 64% | ✗ refactor · 37% | ✓ True · 100% | ✗ True · 98% | ✓ True · 100% | ✓ True · 93% |
| `script_98` | REVIEW | ✗ medium · 62% | ✗ refactor · 37% | ✓ True · 100% | ✗ True · 85% | ✓ True · 100% | ✓ True · 94% |
| `script_99` | REVIEW | ✗ medium · 68% | ✗ refactor · 36% | ✓ True · 99% | ✗ True · 84% | ✓ True · 99% | ✓ True · 94% |

**Gabarito, para conferência:**

| script | complexidade | estratégia | subquery | window | multi-fonte | revisão |
|---|---|---|---|---|---|---|
| `script_01` | low (0pts) | lift_and_shift | False | False | False | False |
| `script_02` | low (0pts) | lift_and_shift | False | False | False | False |
| `script_03` | low (0pts) | lift_and_shift | False | False | False | False |
| `script_04` | low (0pts) | lift_and_shift | False | False | False | False |
| `script_05` | low (1pts) | lift_and_shift | False | False | True | False |
| `script_06` | low (1pts) | lift_and_shift | False | False | True | False |
| `script_07` | low (2pts) | lift_and_shift | False | False | True | False |
| `script_08` | low (2pts) | lift_and_shift | False | False | True | True |
| `script_09` | low (2pts) | refactor | False | False | False | True |
| `script_10` | low (2pts) | lift_and_shift | False | True | False | False |
| `script_11` | low (2pts) | lift_and_shift | False | False | True | False |
| `script_12` | low (2pts) | lift_and_shift | False | True | False | False |
| `script_13` | low (2pts) | lift_and_shift | False | True | False | False |
| `script_14` | low (3pts) | refactor | True | False | True | True |
| `script_15` | low (3pts) | refactor | False | False | True | True |
| `script_16` | low (3pts) | lift_and_shift | False | False | True | False |
| `script_17` | low (3pts) | lift_and_shift | False | False | True | False |
| `script_18` | low (3pts) | refactor | False | True | False | True |
| `script_19` | low (3pts) | refactor | False | False | False | True |
| `script_20` | low (3pts) | refactor | True | False | False | True |
| `script_21` | low (4pts) | refactor | True | False | False | True |
| `script_22` | low (4pts) | lift_and_shift | False | False | True | False |
| `script_23` | low (4pts) | lift_and_shift | False | False | True | True |
| `script_24` | low (4pts) | refactor | True | False | True | True |
| `script_25` | low (4pts) | lift_and_shift | True | False | True | False |
| `script_26` | low (4pts) | refactor | False | True | True | True |
| `script_27` | low (4pts) | refactor | True | False | True | True |
| `script_28` | low (4pts) | refactor | True | False | False | True |
| `script_29` | low (4pts) | refactor | True | False | True | True |
| `script_30` | low (4pts) | lift_and_shift | True | False | True | False |
| `script_31` | low (4pts) | refactor | True | False | False | True |
| `script_32` | medium (5pts) | lift_and_shift | True | False | True | False |
| `script_33` | medium (5pts) | lift_and_shift | True | False | True | True |
| `script_34` | medium (5pts) | refactor | False | False | True | True |
| `script_35` | medium (5pts) | refactor | True | True | False | True |
| `script_36` | medium (5pts) | refactor | True | True | True | True |
| `script_37` | medium (5pts) | lift_and_shift | True | False | True | False |
| `script_38` | medium (5pts) | refactor | False | False | True | True |
| `script_39` | medium (5pts) | lift_and_shift | True | True | True | False |
| `script_40` | medium (5pts) | refactor | False | False | True | True |
| `script_41` | medium (5pts) | refactor | True | False | True | True |
| `script_42` | medium (5pts) | refactor | True | False | True | True |
| `script_43` | medium (5pts) | redesign | True | True | False | True |
| `script_44` | medium (5pts) | lift_and_shift | True | True | True | False |
| `script_45` | medium (5pts) | lift_and_shift | False | False | True | False |
| `script_46` | medium (5pts) | refactor | False | False | True | True |
| `script_47` | medium (5pts) | lift_and_shift | True | True | True | False |
| `script_48` | medium (6pts) | refactor | False | False | True | True |
| `script_49` | medium (6pts) | refactor | True | False | True | True |
| `script_50` | medium (6pts) | refactor | False | False | True | True |
| `script_51` | medium (6pts) | refactor | True | False | True | True |
| `script_52` | medium (6pts) | lift_and_shift | False | False | True | True |
| `script_53` | medium (6pts) | refactor | True | False | True | True |
| `script_54` | medium (6pts) | lift_and_shift | True | False | True | False |
| `script_55` | medium (6pts) | refactor | True | False | False | True |
| `script_56` | medium (6pts) | lift_and_shift | False | False | True | False |
| `script_57` | medium (6pts) | refactor | True | False | True | True |
| `script_58` | medium (6pts) | refactor | False | False | True | True |
| `script_59` | medium (6pts) | lift_and_shift | False | False | True | False |
| `script_60` | medium (6pts) | lift_and_shift | False | False | True | False |
| `script_61` | medium (6pts) | refactor | True | False | True | True |
| `script_62` | medium (6pts) | lift_and_shift | True | False | True | False |
| `script_63` | medium (6pts) | lift_and_shift | True | False | True | False |
| `script_64` | medium (6pts) | refactor | False | False | True | True |
| `script_65` | medium (6pts) | refactor | False | True | True | True |
| `script_66` | medium (6pts) | refactor | True | True | False | True |
| `script_67` | medium (6pts) | refactor | True | False | False | True |
| `script_68` | medium (6pts) | refactor | False | True | True | True |
| `script_69` | high (7pts) | lift_and_shift | True | False | True | False |
| `script_70` | high (7pts) | refactor | False | False | True | True |
| `script_71` | high (7pts) | refactor | False | False | True | True |
| `script_72` | high (7pts) | refactor | True | False | True | True |
| `script_73` | high (7pts) | refactor | True | False | True | True |
| `script_74` | high (7pts) | redesign | True | False | False | True |
| `script_75` | high (7pts) | lift_and_shift | False | False | True | True |
| `script_76` | high (7pts) | refactor | True | False | False | True |
| `script_77` | high (7pts) | refactor | True | False | True | True |
| `script_78` | high (7pts) | refactor | True | False | True | True |
| `script_79` | high (8pts) | refactor | True | False | True | True |
| `script_80` | high (9pts) | refactor | True | False | True | True |
| `script_81` | high (9pts) | lift_and_shift | True | False | True | False |
| `script_82` | high (9pts) | refactor | True | False | True | True |
| `script_83` | high (9pts) | refactor | False | False | True | True |
| `script_84` | high (10pts) | refactor | True | False | True | True |
| `script_85` | high (10pts) | refactor | True | False | True | True |
| `script_86` | high (11pts) | redesign | False | False | True | True |
| `script_87` | high (11pts) | redesign | True | True | True | True |
| `script_88` | high (11pts) | refactor | True | False | True | True |
| `script_89` | high (11pts) | refactor | True | False | True | True |
| `script_90` | high (12pts) | refactor | True | False | True | True |
| `script_91` | high (12pts) | redesign | False | False | True | True |
| `script_92` | high (12pts) | redesign | True | False | True | True |
| `script_93` | high (13pts) | refactor | True | False | True | True |
| `script_94` | high (13pts) | refactor | True | False | True | True |
| `script_95` | high (13pts) | refactor | True | False | True | True |
| `script_96` | high (14pts) | redesign | True | False | True | True |
| `script_97` | high (14pts) | redesign | True | False | True | True |
| `script_98` | high (15pts) | redesign | True | False | True | True |
| `script_99` | high (15pts) | redesign | True | False | True | True |

## 4. Acurácia por pergunta

| pergunta | AST | acertos | acurácia | baseline | ganho | respostas distintas | conf. média | excesso |
|---|---|---|---|---|---|---|---|---|
| `migration_complexity` | não | 36/99 | 36% | 37% | **-1%** | 2 | 61% | +24% |
| `rewrite_strategy` | não | 47/99 | 47% | 55% | **-7%** | 4 | 39% | -8% |
| `has_subquery` | sim | 57/99 | 58% | 58% | **+0%** | 1 | 97% | +39% |
| `has_window_function` | sim | 28/99 | 28% | 85% | **-57%** | 2 | 88% | +60% |
| `multi_source` | sim | 78/99 | 79% | 79% | **+0%** | 1 | 97% | +18% |
| `needs_human_review` | não | 72/99 | 73% | 70% | +3% | 2 | 85% | +12% |

> **baseline** = acurácia de sempre responder a classe majoritária do
> gabarito. **ganho** = acurácia menos baseline; zero ou negativo significa
> que a pergunta não carrega informação. **respostas distintas** = quantos
> rótulos diferentes o modelo chegou a emitir; `1` é um preditor constante.


> _Excesso de confiança_ = confiança média menos acurácia. Positivo
> significa que o modelo se diz mais certo do que de fato é.

**Nas 3 perguntas que o AST responde sozinho: 163/297 = 55%, contra um baseline de classe majoritária de 74% — ganho de -19%.**

> Uma pergunta binária com classes desbalanceadas **não** tem acaso em 50%.
> Comparar contra 50% infla o resultado; o número honesto é o ganho sobre
> responder sempre a classe majoritária.

## 4b. A acurácia esconde a qualidade do ranking

Acurácia responde *o limiar está certo?*. AUC responde *a ordenação está
certa?*. As duas se separam aqui, e ler só a primeira leva à conclusão
errada.

| pergunta | n | AUC | acc @0.5 | IC95 | baseline | McNemar p | melhor limiar | acc nele | leitura |
|---|---|---|---|---|---|---|---|---|---|
| `has_subquery` | 99 | **0.57** | 58% | 48%–67% | 58% | 1.0000 | 0.92 | **61%** | dentro do ruído |
| `has_window_function` | 99 | **0.67** | 28% | 20%–38% | 85% | 0.0000 | 0.00 (inv.) | **85%** | ganho real |
| `multi_source` | 99 | **0.61** | 79% | 70%–86% | 79% | 1.0000 | 0.88 | **80%** | dentro do ruído |
| `needs_human_review` | 99 | **0.50** | 73% | 63%–81% | 70% | 0.4531 | 0.41 | **74%** | dentro do ruído |

> **AUC** = probabilidade de um caso positivo receber score maior que um
> negativo. 0.5 é o acaso. **Abaixo de 0.5 não é ausência de sinal — é
> sinal apontando para o lado errado**, que um limiar invertido recuperaria.
> **McNemar p** testa se a diferença para o baseline de classe majoritária
> é maior que o acaso; p alto significa que o ganho (ou a perda) é ruído.

> ⚠️ **O melhor limiar foi ajustado nos mesmos 99 pontos em que é medido.**
> É um teto otimista, não uma configuração implantável — serve só para
> separar *o modelo não sabe* de *o corte está no lugar errado*. Um número
> defensável exigiria ajustar em treino e medir em hold-out.

> Todos os limiares ótimos caem **abaixo de 0.5**: o modelo subestima
> P(true) de forma sistemática — é o aviso de temperatura inválida do
> checkpoint aparecendo em números.

## 4c. Contra uma regressão logística sobre as mesmas features

Superar a classe majoritária é uma barra baixa. A pergunta de um
discovery é se um modelo de 421M parâmetros se paga contra algumas
linhas de aritmética sobre features que já extraímos de graça.

Duas variantes, e a diferença entre elas é um resultado por si só:

- **leaky** — todas as features, inclusive aquelas de que o gabarito é
  *definido*. Mede **quanto da pergunta o cartão simplesmente entrega**.
- **clean** — essas features removidas. É o baseline honesto.

Tudo avaliado *leave-one-out*, nunca ajustando e medindo nas mesmas
linhas.

| pergunta | variante | feats | LR acc | LR AUC | Laya acc | Laya AUC | McNemar p | leitura |
|---|---|---|---|---|---|---|---|---|
| `has_subquery` | leaky | 32 | 97% | 0.97 | 58% | 0.57 | 0.0000 | **LR vence** |
| `has_subquery` | clean | 26 | 85% | 0.88 | 58% | 0.57 | 0.0002 | **LR vence** |
| `has_window_function` | leaky | 32 | 100% | 1.00 | 28% | 0.67 | 0.0000 | **LR vence** |
| `has_window_function` | clean | 30 | 85% | 0.92 | 28% | 0.67 | 0.0000 | **LR vence** |
| `multi_source` | leaky | 32 | 100% | 1.00 | 79% | 0.61 | 0.0000 | **LR vence** |
| `multi_source` | clean | 20 | 80% | 0.64 | 79% | 0.61 | 1.0000 | empate estatístico |
| `needs_human_review` | leaky | 32 | 89% | 0.94 | 73% | 0.50 | 0.0090 | **LR vence** |
| `needs_human_review` | clean | 32 | 89% | 0.94 | 73% | 0.50 | 0.0090 | **LR vence** |

> A variante **leaky** chegando a 97–100% é a medida da circularidade
> deste experimento: o cartão lista os fatos perguntados e uma regressão
> logística os lê de volta. Nessas perguntas o Laya não tem como agregar
> valor — e de fato fica **abaixo** da aritmética sobre o mesmo input.

> Na variante **clean** os dois empatam estatisticamente nas três
> perguntas verificáveis: o Laya não perde, mas também não ganha.

## 5. Matriz de confusão — complexidade

| gold \ predito | low | medium | high |
|---|---|---|---|
| **low** | 0 | 31 | 0 |
| **medium** | 0 | 36 | 1 |
| **high** | 0 | 31 | 0 |

## 5b. Matriz de confusão — estratégia de reescrita

| gold \ predito | lift_and_shift | refactor | redesign | manual_rewrite |
|---|---|---|---|---|
| **lift_and_shift** | 6 | 28 | 1 | 0 |
| **refactor** | 9 | 41 | 1 | 3 |
| **redesign** | 1 | 9 | 0 | 0 |

## 5c. O argmax travou — mas existe sinal de ordenação?

A matriz acima tem uma coluna só: o argmax caiu na mesma classe para todos os scripts.
Isso *parece* ausência total de sinal. Mas a distribuição por trás do argmax
não é constante — ela se move na direção certa:

- Correlação de postos (Spearman, n=99) entre os pontos de rubrica e o **score esperado** do Laya: **rho = +0.048**.
- Entre pontos de rubrica e P(high): rho = +0.041.
- Entre pontos de rubrica e P(low): rho = -0.097.
- Mas o score esperado varia só de **0.929 a 1.339**, numa escala de 0 a 2 — todo
  o intervalo útil comprimido em torno da classe do meio.

| pontos gold | score esperado do Laya |
|---|---|
| 0 | 0.995 |
| 0 | 1.163 |
| 0 | 1.167 |
| 0 | 1.339 |
| 1 | 0.967 |
| 1 | 1.082 |
| 2 | 0.929 |
| 2 | 0.956 |
| 2 | 1.024 |
| 2 | 1.050 |
| 2 | 1.093 |
| 2 | 1.098 |
| 2 | 1.125 |
| 3 | 1.080 |
| 3 | 1.096 |
| 3 | 1.116 |
| 3 | 1.125 |
| 3 | 1.131 |
| 3 | 1.133 |
| 3 | 1.242 |
| 4 | 1.023 |
| 4 | 1.028 |
| 4 | 1.044 |
| 4 | 1.046 |
| 4 | 1.099 |
| 4 | 1.118 |
| 4 | 1.137 |
| 4 | 1.157 |
| 4 | 1.170 |
| 4 | 1.199 |
| 4 | 1.230 |
| 5 | 1.037 |
| 5 | 1.085 |
| 5 | 1.099 |
| 5 | 1.103 |
| 5 | 1.107 |
| 5 | 1.125 |
| 5 | 1.127 |
| 5 | 1.139 |
| 5 | 1.140 |
| 5 | 1.146 |
| 5 | 1.155 |
| 5 | 1.163 |
| 5 | 1.180 |
| 5 | 1.252 |
| 5 | 1.280 |
| 5 | 1.282 |
| 6 | 1.013 |
| 6 | 1.038 |
| 6 | 1.058 |
| 6 | 1.070 |
| 6 | 1.073 |
| 6 | 1.085 |
| 6 | 1.087 |
| 6 | 1.103 |
| 6 | 1.111 |
| 6 | 1.112 |
| 6 | 1.118 |
| 6 | 1.127 |
| 6 | 1.127 |
| 6 | 1.133 |
| 6 | 1.133 |
| 6 | 1.137 |
| 6 | 1.147 |
| 6 | 1.157 |
| 6 | 1.180 |
| 6 | 1.199 |
| 6 | 1.334 |
| 7 | 1.058 |
| 7 | 1.060 |
| 7 | 1.075 |
| 7 | 1.090 |
| 7 | 1.100 |
| 7 | 1.119 |
| 7 | 1.119 |
| 7 | 1.134 |
| 7 | 1.225 |
| 7 | 1.256 |
| 8 | 1.226 |
| 9 | 1.028 |
| 9 | 1.043 |
| 9 | 1.124 |
| 9 | 1.178 |
| 10 | 1.042 |
| 10 | 1.101 |
| 11 | 1.027 |
| 11 | 1.117 |
| 11 | 1.151 |
| 11 | 1.180 |
| 12 | 1.148 |
| 12 | 1.149 |
| 12 | 1.187 |
| 13 | 1.066 |
| 13 | 1.091 |
| 13 | 1.091 |
| 14 | 1.115 |
| 14 | 1.118 |
| 15 | 1.080 |
| 15 | 1.154 |

> Esta é a diferença entre *não ter sinal* e *não saber onde cortar*.
> A primeira exigiria outras features; a segunda se resolve com
> calibração de temperatura ou um limiar ajustado sobre o score
> esperado — muito mais barato.


## 6. Calibração

**ECE = 0.276** sobre 594 decisões (0 = perfeitamente calibrado).

| faixa de confiança | n | confiança média | acurácia | lacuna |
|---|---|---|---|---|
| 0.0-0.2 | 0 | — | — | — |
| 0.2-0.4 | 60 | 35% | 52% | 17% |
| 0.4-0.6 | 84 | 52% | 43% | 9% |
| 0.6-0.8 | 97 | 67% | 39% | 28% |
| 0.8-1.0 | 353 | 94% | 60% | 34% |

**Brier = 0.326** (0 = perfeito, 0.25 = chute a 50%).

## 7. Cobertura × acurácia — onde colocar o corte

| limiar | respostas acima | cobertura | acurácia | erros |
|---|---|---|---|---|
| 0.50 | 502 | 85% | 55% | 228 |
| 0.60 | 450 | 76% | 56% | 199 |
| 0.70 | 380 | 64% | 59% | 154 |
| 0.80 | 353 | 59% | 60% | 140 |
| 0.85 | 320 | 54% | 60% | 127 |
| 0.90 | 274 | 46% | 59% | 111 |
| 0.95 | 178 | 30% | 63% | 66 |

> Se a acurácia **não sobe** conforme o limiar aperta, a confiança não
> carrega informação sobre estar certo — e nenhum corte torna o
> classificador auto-operável.

## 7b. O mesmo corte, mas por script

A tabela acima conta **respostas**. Um script só é triado sem humano quando
*todas* as perguntas sobre ele passam do corte ao mesmo tempo — e a conjunção
de respostas independentes é muito mais dura que cada uma isolada.

| limiar | scripts com os 3 fatos acima do corte | cobertura | acurácia (IC95) | erros |
|---|---|---|---|---|
| 0.50 | 99 | 100% | 5% (2%–11%) | 94 |
| 0.60 | 98 | 99% | 5% (2%–11%) | 93 |
| 0.70 | 93 | 94% | 5% (2%–12%) | 88 |
| 0.80 | 80 | 81% | 6% (3%–14%) | 75 |
| 0.85 | 61 | 62% | 7% (3%–16%) | 57 |
| 0.90 | 44 | 44% | 5% (1%–15%) | 42 |

Sem exigir confiança nenhuma, **5/99 scripts (5%) acertam os três fatos verificáveis**. É a distância
entre esse número e a coluna de cobertura acima que mede o custo da exigência
de confiança — e é ela que zera o `AUTO`.

## 8. Onde o modelo erra

| script | pontos gold | fontes | arestas | subq | erros de 6 |
|---|---|---|---|---|---|
| `script_01` | 0 | 3 | 2 | 0 | **4** |
| `script_02` | 0 | 3 | 2 | 0 | **3** |
| `script_03` | 0 | 3 | 2 | 0 | **4** |
| `script_04` | 0 | 3 | 2 | 0 | **4** |
| `script_05` | 1 | 4 | 3 | 0 | **3** |
| `script_06` | 1 | 4 | 3 | 0 | **3** |
| `script_07` | 2 | 4 | 3 | 0 | **5** |
| `script_08` | 2 | 4 | 3 | 0 | **3** |
| `script_09` | 2 | 3 | 2 | 0 | **3** |
| `script_10` | 2 | 3 | 2 | 0 | **5** |
| `script_11` | 2 | 4 | 3 | 0 | **5** |
| `script_12` | 2 | 3 | 2 | 0 | **5** |
| `script_13` | 2 | 3 | 2 | 0 | **5** |
| `script_14` | 3 | 4 | 1 | 3 | **3** |
| `script_15` | 3 | 5 | 4 | 0 | **3** |
| `script_16` | 3 | 5 | 4 | 0 | **4** |
| `script_17` | 3 | 5 | 4 | 0 | **4** |
| `script_18` | 3 | 3 | 2 | 0 | **3** |
| `script_19` | 3 | 3 | 2 | 0 | **4** |
| `script_20` | 3 | 3 | 2 | 1 | **3** |
| `script_21` | 4 | 3 | 2 | 1 | **4** |
| `script_22` | 4 | 6 | 5 | 0 | **4** |
| `script_23` | 4 | 5 | 4 | 0 | **2** |
| `script_24` | 4 | 4 | 2 | 1 | **2** |
| `script_25` | 4 | 5 | 3 | 1 | **3** |
| `script_26` | 4 | 4 | 3 | 0 | **3** |
| `script_27` | 4 | 4 | 1 | 1 | **2** |
| `script_28` | 4 | 1 | 0 | 1 | **3** |
| `script_29` | 4 | 4 | 2 | 1 | **2** |
| `script_30` | 4 | 4 | 3 | 2 | **3** |
| `script_31` | 4 | 3 | 2 | 1 | **4** |
| `script_32` | 5 | 5 | 3 | 1 | **3** |
| `script_33` | 5 | 4 | 3 | 1 | **2** |
| `script_34` | 5 | 5 | 0 | 0 | **2** |
| `script_35` | 5 | 3 | 2 | 2 | **1** |
| `script_36` | 5 | 4 | 3 | 2 | **0** |
| `script_37` | 5 | 5 | 3 | 1 | **3** |
| `script_38` | 5 | 6 | 5 | 0 | **2** |
| `script_39` | 5 | 4 | 3 | 1 | **2** |
| `script_40` | 5 | 5 | 4 | 0 | **3** |
| `script_41` | 5 | 5 | 4 | 1 | **1** |
| `script_42` | 5 | 5 | 4 | 2 | **2** |
| `script_43` | 5 | 2 | 0 | 8 | **2** |
| `script_44` | 5 | 4 | 3 | 1 | **2** |
| `script_45` | 5 | 6 | 5 | 0 | **3** |
| `script_46` | 5 | 4 | 4 | 0 | **2** |
| `script_47` | 5 | 4 | 3 | 1 | **2** |
| `script_48` | 6 | 4 | 4 | 0 | **3** |
| `script_49` | 6 | 5 | 6 | 1 | **2** |
| `script_50` | 6 | 5 | 4 | 0 | **2** |
| `script_51` | 6 | 7 | 5 | 3 | **1** |
| `script_52` | 6 | 6 | 6 | 0 | **3** |
| `script_53` | 6 | 5 | 3 | 2 | **2** |
| `script_54` | 6 | 6 | 5 | 1 | **3** |
| `script_55` | 6 | 3 | 1 | 2 | **2** |
| `script_56` | 6 | 6 | 7 | 0 | **4** |
| `script_57` | 6 | 5 | 3 | 2 | **2** |
| `script_58` | 6 | 7 | 6 | 0 | **2** |
| `script_59` | 6 | 7 | 6 | 0 | **4** |
| `script_60` | 6 | 6 | 7 | 0 | **4** |
| `script_61` | 6 | 5 | 6 | 1 | **3** |
| `script_62` | 6 | 6 | 3 | 1 | **3** |
| `script_63` | 6 | 6 | 5 | 1 | **3** |
| `script_64` | 6 | 4 | 4 | 0 | **2** |
| `script_65` | 6 | 4 | 3 | 0 | **1** |
| `script_66` | 6 | 3 | 2 | 2 | **2** |
| `script_67` | 6 | 1 | 0 | 6 | **2** |
| `script_68` | 6 | 4 | 3 | 0 | **1** |
| `script_69` | 7 | 5 | 6 | 1 | **3** |
| `script_70` | 7 | 7 | 6 | 0 | **3** |
| `script_71` | 7 | 4 | 4 | 0 | **3** |
| `script_72` | 7 | 7 | 5 | 3 | **3** |
| `script_73` | 7 | 5 | 3 | 2 | **2** |
| `script_74` | 7 | 2 | 0 | 15 | **4** |
| `script_75` | 7 | 6 | 7 | 0 | **4** |
| `script_76` | 7 | 3 | 0 | 3 | **3** |
| `script_77` | 7 | 5 | 3 | 3 | **2** |
| `script_78` | 7 | 4 | 3 | 8 | **2** |
| `script_79` | 8 | 7 | 5 | 3 | **3** |
| `script_80` | 9 | 5 | 6 | 6 | **2** |
| `script_81` | 9 | 7 | 6 | 2 | **4** |
| `script_82` | 9 | 5 | 6 | 6 | **2** |
| `script_83` | 9 | 9 | 9 | 0 | **3** |
| `script_84` | 10 | 4 | 3 | 2 | **3** |
| `script_85` | 10 | 8 | 2 | 3 | **2** |
| `script_86` | 11 | 13 | 15 | 0 | **4** |
| `script_87` | 11 | 7 | 6 | 6 | **2** |
| `script_88` | 11 | 6 | 5 | 2 | **2** |
| `script_89` | 11 | 8 | 9 | 1 | **2** |
| `script_90` | 12 | 6 | 8 | 1 | **2** |
| `script_91` | 12 | 5 | 6 | 0 | **4** |
| `script_92` | 12 | 10 | 1 | 4 | **3** |
| `script_93` | 13 | 6 | 9 | 4 | **2** |
| `script_94` | 13 | 6 | 9 | 4 | **2** |
| `script_95` | 13 | 6 | 9 | 4 | **2** |
| `script_96` | 14 | 5 | 6 | 19 | **3** |
| `script_97` | 14 | 6 | 7 | 14 | **3** |
| `script_98` | 15 | 12 | 10 | 1 | **3** |
| `script_99` | 15 | 9 | 10 | 1 | **3** |

## 9. Latência

- Carga do modelo: **6.905 s** (uma vez).
- Por script (6 perguntas): **p50 = 6082 ms · p95 = 12090 ms** (min 2831, max 24053).
- Lote completo: **642.0 s** para 99 scripts.
- Por pergunta: ~1014 ms.

Extrapolando para as 99 queries do corpus: ~642 s de inferência em CPU.

| script | estimado (ms) | medido (ms) | erro |
|---|---|---|---|
| `script_01` | 1969 | 3600 | +83% |
| `script_02` | 1687 | 2831 | +68% |
| `script_03` | 1687 | 3374 | +100% |
| `script_04` | 1687 | 3460 | +105% |
| `script_05` | 1687 | 2932 | +74% |
| `script_06` | 1687 | 3709 | +120% |
| `script_07` | 1718 | 3859 | +125% |
| `script_08` | 1718 | 3303 | +92% |
| `script_09` | 1718 | 6526 | +280% |
| `script_10` | 1760 | 4550 | +158% |
| `script_11` | 1718 | 3829 | +123% |
| `script_12` | 1760 | 4516 | +157% |
| `script_13` | 1760 | 4508 | +156% |
| `script_14` | 1781 | 6019 | +238% |
| `script_15` | 1687 | 6449 | +282% |
| `script_16` | 1687 | 4193 | +149% |
| `script_17` | 1687 | 4178 | +148% |
| `script_18` | 1812 | 4012 | +121% |
| `script_19` | 1823 | 5622 | +208% |
| `script_20` | 1823 | 3448 | +89% |
| `script_21` | 1948 | 4143 | +113% |
| `script_22` | 1687 | 3486 | +107% |
| `script_23` | 2031 | 4388 | +116% |
| `script_24` | 1927 | 6132 | +218% |
| `script_25` | 1781 | 5746 | +223% |
| `script_26` | 1812 | 5190 | +186% |
| `script_27` | 1927 | 4516 | +134% |
| `script_28` | 1885 | 9497 | +404% |
| `script_29` | 1927 | 6552 | +240% |
| `script_30` | 1781 | 5713 | +221% |
| `script_31` | 1948 | 4137 | +112% |
| `script_32` | 1823 | 6542 | +259% |
| `script_33` | 1865 | 6212 | +233% |
| `script_34` | 1760 | 6500 | +269% |
| `script_35` | 1854 | 6551 | +253% |
| `script_36` | 1885 | 6114 | +224% |
| `script_37` | 1823 | 6488 | +256% |
| `script_38` | 1969 | 6487 | +229% |
| `script_39` | 1844 | 6552 | +255% |
| `script_40` | 2000 | 5970 | +198% |
| `script_41` | 1885 | 4621 | +145% |
| `script_42` | 1885 | 4356 | +131% |
| `script_43` | 1927 | 6549 | +240% |
| `script_44` | 1844 | 6620 | +259% |
| `script_45` | 1687 | 4677 | +177% |
| `script_46` | 1760 | 6573 | +273% |
| `script_47` | 1844 | 6362 | +245% |
| `script_48` | 1844 | 6584 | +257% |
| `script_49` | 1823 | 5006 | +175% |
| `script_50` | 1760 | 6540 | +272% |
| `script_51` | 1885 | 6545 | +247% |
| `script_52` | 1718 | 6549 | +281% |
| `script_53` | 1948 | 5745 | +195% |
| `script_54` | 1781 | 6523 | +266% |
| `script_55` | 1844 | 6611 | +259% |
| `script_56` | 1687 | 6267 | +271% |
| `script_57` | 1948 | 4966 | +155% |
| `script_58` | 1687 | 6253 | +271% |
| `script_59` | 1687 | 5029 | +198% |
| `script_60` | 2031 | 6018 | +196% |
| `script_61` | 1823 | 5213 | +186% |
| `script_62` | 1823 | 6018 | +230% |
| `script_63` | 1781 | 6107 | +243% |
| `script_64` | 1844 | 6050 | +228% |
| `script_65` | 1844 | 6026 | +227% |
| `script_66` | 2011 | 6131 | +205% |
| `script_67` | 1781 | 7713 | +333% |
| `script_68` | 2115 | 6144 | +190% |
| `script_69` | 2136 | 5978 | +180% |
| `script_70` | 1781 | 6006 | +237% |
| `script_71` | 1823 | 6082 | +234% |
| `script_72` | 1885 | 6074 | +222% |
| `script_73` | 1979 | 6013 | +204% |
| `script_74` | 1927 | 6044 | +214% |
| `script_75` | 1718 | 6094 | +255% |
| `script_76` | 1854 | 6039 | +226% |
| `script_77` | 1823 | 18002 | +888% |
| `script_78` | 1781 | 12090 | +579% |
| `script_79` | 1927 | 6144 | +219% |
| `script_80` | 1927 | 6155 | +219% |
| `script_81` | 1781 | 6055 | +240% |
| `script_82` | 1927 | 6054 | +214% |
| `script_83` | 1760 | 6116 | +247% |
| `script_84` | 1885 | 6110 | +224% |
| `script_85` | 1948 | 6046 | +210% |
| `script_86` | 2188 | 9146 | +318% |
| `script_87` | 1844 | 11873 | +544% |
| `script_88` | 1927 | 6167 | +220% |
| `script_89` | 1844 | 6071 | +229% |
| `script_90` | 2104 | 24053 | +1043% |
| `script_91` | 1844 | 10653 | +478% |
| `script_92` | 1896 | 11870 | +526% |
| `script_93` | 1948 | 6509 | +234% |
| `script_94` | 1948 | 6529 | +235% |
| `script_95` | 1948 | 6524 | +235% |
| `script_96` | 2386 | 19550 | +719% |
| `script_97` | 1948 | 12997 | +567% |
| `script_98` | 1896 | 9341 | +393% |
| `script_99` | 1896 | 10026 | +429% |

> O modelo de custo foi ajustado com texto sintético e subestima os cards
> reais de forma consistente; serve para dimensionar um lote, não para SLA.

