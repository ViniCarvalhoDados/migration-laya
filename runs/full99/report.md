# Resultado — run `full99`

99 scripts · 6 perguntas · modelo `convaiinnovations/laya` em `cpu`

**Input:** evidence card (~100 tokens derivados do AST).

> **Aviso emitido pelo próprio runtime ao carregar o checkpoint:**
>
> ``huggingface_hub` cache-system uses symlinks by default to efficiently store duplicated files but your machine does not support them in C:\Users\Vinicius\.cache\huggingface\hub\models--convaiinnovations--laya. Caching files will still work but in a degraded version that might require more space on your disk. This warning can be disabled by setting the `HF_HUB_DISABLE_SYMLINKS_WARNING` environment variable. For more details, see https://huggingface.co/docs/huggingface_hub/how-to-cache#limitations.
To support symlinks on Windows, you either need to activate Developer Mode or to run Python as an administrator. In order to activate developer mode, see this article: https://docs.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development`
>
> `laya: this checkpoint ships invalid temperatures or values outside [0.5, 5]; using choice:11+=0.10058280825614929 -> 0.5. Treat confidence from the affected entries as uncalibrated.`
>
> Ou seja, os percentuais de confiança abaixo são declaradamente não
> calibrados pelo fornecedor. Isso não invalida as respostas — invalida
> lê-las pelo valor de face. É exatamente o que a seção de calibração mede.

## 1. Manchete

| desfecho | scripts | % | significado |
|---|---|---|---|
| `AUTO` | 0 | 0% | classificado sem humano |
| `HUMAN_REVIEW` | 99 | 100% | humano confere — erro pequeno ou baixa confiança |
| `ESCALATE` | 0 | 0% | **erro confiante** em fato verificável pelo AST |

**0 de 99 scripts (0%) passariam sem revisão humana.**

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
| `script_01` | REVIEW | ✗ medium · 54% | ✗ refactor · 55% | ✓ False · 76% | ✓ False · 86% | ✓ False · 67% | ✗ True · 79% |
| `script_02` | REVIEW | ✗ medium · 55% | ✗ refactor · 53% | ✓ False · 74% | ✓ False · 86% | ✓ False · 67% | ✗ True · 77% |
| `script_03` | REVIEW | ✗ medium · 55% | ✗ refactor · 54% | ✓ False · 76% | ✓ False · 86% | ✓ False · 69% | ✗ True · 77% |
| `script_04` | REVIEW | ✗ medium · 54% | ✗ refactor · 53% | ✓ False · 77% | ✓ False · 87% | ✓ False · 68% | ✗ True · 77% |
| `script_05` | REVIEW | ✗ medium · 52% | ✗ refactor · 52% | ✓ False · 77% | ✓ False · 88% | ✓ True · 88% | ✗ True · 71% |
| `script_06` | REVIEW | ✗ medium · 49% | ✗ refactor · 54% | ✓ False · 81% | ✓ False · 87% | ✓ True · 92% | ✗ True · 82% |
| `script_07` | REVIEW | ✗ medium · 52% | ✗ refactor · 62% | ✓ False · 82% | ✓ False · 86% | ✓ True · 91% | ✗ True · 51% |
| `script_08` | REVIEW | ✗ medium · 53% | ✗ refactor · 53% | ✓ False · 79% | ✓ False · 86% | ✓ True · 94% | ✓ True · 72% |
| `script_09` | REVIEW | ✗ medium · 55% | ✓ refactor · 49% | ✓ False · 65% | ✓ False · 84% | ✓ False · 80% | ✓ True · 72% |
| `script_10` | REVIEW | ✗ medium · 54% | ✗ refactor · 61% | ✓ False · 61% | ✗ False · 67% | ✓ False · 55% | ✗ True · 69% |
| `script_11` | REVIEW | ✗ medium · 52% | ✗ refactor · 62% | ✓ False · 82% | ✓ False · 86% | ✓ True · 91% | ✗ True · 51% |
| `script_12` | REVIEW | ✗ medium · 55% | ✗ refactor · 62% | ✓ False · 63% | ✗ False · 65% | ✓ False · 54% | ✗ True · 68% |
| `script_13` | REVIEW | ✗ medium · 54% | ✗ refactor · 61% | ✓ False · 61% | ✗ False · 67% | ✓ False · 55% | ✗ True · 69% |
| `script_14` | REVIEW | ✗ medium · 59% | ✓ refactor · 59% | ✓ True · 68% | ✓ False · 90% | ✓ True · 93% | ✓ True · 66% |
| `script_15` | REVIEW | ✗ medium · 52% | ✓ refactor · 52% | ✓ False · 73% | ✓ False · 89% | ✓ True · 87% | ✓ True · 73% |
| `script_16` | REVIEW | ✗ medium · 53% | ✗ refactor · 51% | ✓ False · 74% | ✓ False · 88% | ✓ True · 87% | ✗ True · 71% |
| `script_17` | REVIEW | ✗ medium · 53% | ✗ refactor · 51% | ✓ False · 74% | ✓ False · 88% | ✓ True · 87% | ✗ True · 71% |
| `script_18` | REVIEW | ✗ medium · 62% | ✓ refactor · 53% | ✓ False · 80% | ✗ False · 61% | ✗ True · 51% | ✗ False · 57% |
| `script_19` | REVIEW | ✗ medium · 63% | ✓ refactor · 62% | ✓ False · 77% | ✓ False · 89% | ✓ False · 63% | ✓ True · 60% |
| `script_20` | REVIEW | ✗ medium · 62% | ✓ refactor · 57% | ✓ True · 63% | ✓ False · 89% | ✓ False · 58% | ✓ True · 63% |
| `script_21` | REVIEW | ✗ medium · 58% | ✓ refactor · 59% | ✓ True · 83% | ✓ False · 88% | ✗ True · 67% | ✗ False · 68% |
| `script_22` | REVIEW | ✗ medium · 53% | ✗ refactor · 56% | ✓ False · 74% | ✓ False · 88% | ✗ False · 58% | ✗ True · 73% |
| `script_23` | REVIEW | ✗ medium · 52% | ✗ refactor · 55% | ✓ False · 79% | ✓ False · 85% | ✓ True · 80% | ✓ True · 63% |
| `script_24` | REVIEW | ✗ medium · 64% | ✓ refactor · 62% | ✓ True · 51% | ✓ False · 91% | ✓ True · 91% | ✗ False · 51% |
| `script_25` | REVIEW | ✗ medium · 56% | ✗ refactor · 58% | ✓ True · 86% | ✓ False · 88% | ✓ True · 69% | ✗ True · 69% |
| `script_26` | REVIEW | ✗ medium · 59% | ✓ refactor · 51% | ✓ False · 81% | ✓ True · 53% | ✓ True · 92% | ✗ False · 53% |
| `script_27` | REVIEW | ✗ medium · 64% | ✓ refactor · 62% | ✗ False · 52% | ✓ False · 92% | ✓ True · 89% | ✗ False · 57% |
| `script_28` | REVIEW | ✗ medium · 63% | ✓ refactor · 69% | ✓ True · 70% | ✓ False · 87% | ✓ False · 86% | ✓ True · 54% |
| `script_29` | REVIEW | ✗ medium · 63% | ✓ refactor · 61% | ✗ False · 54% | ✓ False · 92% | ✓ True · 91% | ✗ False · 53% |
| `script_30` | REVIEW | ✗ medium · 58% | ✗ refactor · 58% | ✓ True · 51% | ✓ False · 91% | ✓ True · 94% | ✗ True · 60% |
| `script_31` | REVIEW | ✗ medium · 58% | ✓ refactor · 60% | ✓ True · 82% | ✓ False · 87% | ✗ True · 67% | ✗ False · 65% |
| `script_32` | REVIEW | ✓ medium · 61% | ✗ refactor · 57% | ✓ True · 72% | ✓ False · 88% | ✓ True · 73% | ✗ True · 63% |
| `script_33` | REVIEW | ✓ medium · 63% | ✗ refactor · 64% | ✗ False · 57% | ✓ False · 87% | ✓ True · 90% | ✗ False · 67% |
| `script_34` | REVIEW | ✓ medium · 59% | ✓ refactor · 50% | ✓ False · 53% | ✓ False · 81% | ✓ True · 75% | ✓ True · 57% |
| `script_35` | REVIEW | ✓ medium · 65% | ✓ refactor · 63% | ✗ False · 70% | ✗ False · 79% | ✗ True · 53% | ✗ False · 52% |
| `script_36` | REVIEW | ✓ medium · 61% | ✓ refactor · 55% | ✓ True · 63% | ✓ True · 67% | ✓ True · 95% | ✓ True · 67% |
| `script_37` | REVIEW | ✓ medium · 59% | ✗ refactor · 56% | ✓ True · 67% | ✓ False · 89% | ✓ True · 66% | ✗ True · 62% |
| `script_38` | REVIEW | ✓ medium · 56% | ✓ refactor · 53% | ✓ False · 73% | ✓ False · 89% | ✗ False · 52% | ✓ True · 71% |
| `script_39` | REVIEW | ✓ medium · 58% | ✗ refactor · 53% | ✓ True · 74% | ✗ False · 69% | ✓ True · 96% | ✗ True · 53% |
| `script_40` | REVIEW | ✓ medium · 56% | ✓ refactor · 53% | ✓ False · 68% | ✓ False · 84% | ✓ True · 83% | ✓ True · 55% |
| `script_41` | REVIEW | ✓ medium · 62% | ✓ refactor · 64% | ✓ True · 82% | ✓ False · 91% | ✓ True · 87% | ✓ True · 55% |
| `script_42` | REVIEW | ✓ medium · 61% | ✓ refactor · 57% | ✗ False · 62% | ✓ False · 92% | ✓ True · 89% | ✓ True · 55% |
| `script_43` | REVIEW | ✓ medium · 61% | ✗ refactor · 67% | ✓ True · 72% | ✓ True · 70% | ✗ True · 67% | ✓ True · 71% |
| `script_44` | REVIEW | ✓ medium · 60% | ✗ refactor · 55% | ✓ True · 77% | ✗ False · 66% | ✓ True · 96% | ✗ True · 59% |
| `script_45` | REVIEW | ✓ medium · 54% | ✗ refactor · 55% | ✓ False · 75% | ✓ False · 88% | ✗ False · 57% | ✗ True · 76% |
| `script_46` | REVIEW | ✓ medium · 59% | ✓ refactor · 49% | ✓ False · 74% | ✓ False · 84% | ✓ True · 89% | ✓ True · 52% |
| `script_47` | REVIEW | ✓ medium · 59% | ✗ refactor · 55% | ✓ True · 70% | ✗ False · 70% | ✓ True · 95% | ✗ True · 59% |
| `script_48` | REVIEW | ✓ medium · 64% | ✓ refactor · 61% | ✓ False · 81% | ✓ False · 88% | ✓ True · 92% | ✓ True · 53% |
| `script_49` | REVIEW | ✓ medium · 64% | ✓ refactor · 63% | ✓ True · 56% | ✓ False · 90% | ✗ False · 55% | ✓ True · 63% |
| `script_50` | REVIEW | ✓ medium · 58% | ✓ refactor · 49% | ✓ False · 64% | ✓ False · 85% | ✓ True · 82% | ✓ True · 55% |
| `script_51` | REVIEW | ✓ medium · 64% | ✓ refactor · 59% | ✗ False · 51% | ✓ False · 92% | ✓ True · 83% | ✓ True · 58% |
| `script_52` | REVIEW | ✓ medium · 58% | ✗ refactor · 50% | ✓ False · 78% | ✓ False · 88% | ✗ False · 68% | ✓ True · 68% |
| `script_53` | REVIEW | ✓ medium · 52% | ✓ refactor · 51% | ✗ False · 58% | ✓ False · 87% | ✓ True · 87% | ✗ False · 63% |
| `script_54` | REVIEW | ✓ medium · 58% | ✗ refactor · 59% | ✓ True · 81% | ✓ False · 90% | ✗ False · 51% | ✗ True · 64% |
| `script_55` | REVIEW | ✓ medium · 64% | ✓ refactor · 63% | ✗ False · 52% | ✓ False · 89% | ✓ False · 79% | ✓ True · 53% |
| `script_56` | REVIEW | ✓ medium · 54% | ✗ refactor · 52% | ✓ False · 74% | ✓ False · 89% | ✗ False · 51% | ✗ True · 74% |
| `script_57` | REVIEW | ✓ medium · 52% | ✓ refactor · 51% | ✗ False · 51% | ✓ False · 87% | ✓ True · 88% | ✗ False · 59% |
| `script_58` | REVIEW | ✓ medium · 55% | ✓ refactor · 55% | ✓ False · 72% | ✓ False · 88% | ✗ False · 54% | ✓ True · 81% |
| `script_59` | REVIEW | ✓ medium · 55% | ✗ refactor · 55% | ✓ False · 73% | ✓ False · 88% | ✗ False · 51% | ✗ True · 80% |
| `script_60` | REVIEW | ✓ medium · 53% | ✗ refactor · 51% | ✓ False · 73% | ✓ False · 88% | ✓ True · 60% | ✗ True · 74% |
| `script_61` | REVIEW | ✓ medium · 66% | ✓ refactor · 62% | ✓ True · 51% | ✓ False · 91% | ✗ False · 55% | ✓ True · 61% |
| `script_62` | REVIEW | ✓ medium · 60% | ✗ refactor · 58% | ✓ True · 61% | ✓ False · 91% | ✓ True · 76% | ✗ True · 63% |
| `script_63` | REVIEW | ✓ medium · 57% | ✗ refactor · 57% | ✓ True · 80% | ✓ False · 89% | ✓ True · 53% | ✗ True · 65% |
| `script_64` | REVIEW | ✓ medium · 66% | ✓ refactor · 62% | ✓ False · 81% | ✓ False · 88% | ✓ True · 93% | ✓ True · 51% |
| `script_65` | REVIEW | ✓ medium · 60% | ✓ refactor · 65% | ✓ False · 68% | ✗ False · 78% | ✓ True · 94% | ✓ True · 67% |
| `script_66` | REVIEW | ✓ medium · 63% | ✓ refactor · 49% | ✗ False · 55% | ✗ False · 65% | ✗ True · 78% | ✗ False · 64% |
| `script_67` | REVIEW | ✓ medium · 59% | ✓ refactor · 65% | ✓ True · 79% | ✓ False · 79% | ✓ False · 73% | ✓ True · 70% |
| `script_68` | REVIEW | ✓ medium · 59% | ✓ refactor · 64% | ✓ False · 69% | ✗ False · 78% | ✓ True · 94% | ✓ True · 68% |
| `script_69` | REVIEW | ✗ medium · 65% | ✗ refactor · 62% | ✓ True · 54% | ✓ False · 91% | ✗ False · 59% | ✗ True · 63% |
| `script_70` | REVIEW | ✗ medium · 61% | ✓ refactor · 61% | ✓ False · 73% | ✓ False · 91% | ✗ False · 65% | ✓ True · 63% |
| `script_71` | REVIEW | ✗ medium · 65% | ✓ refactor · 71% | ✓ False · 74% | ✓ False · 89% | ✓ True · 95% | ✓ True · 59% |
| `script_72` | REVIEW | ✗ medium · 65% | ✓ refactor · 59% | ✗ False · 54% | ✓ False · 92% | ✓ True · 83% | ✓ True · 57% |
| `script_73` | REVIEW | ✗ medium · 50% | ✓ refactor · 46% | ✗ False · 81% | ✓ False · 91% | ✓ True · 82% | ✗ False · 58% |
| `script_74` | REVIEW | ✗ medium · 66% | ✗ refactor · 64% | ✓ True · 70% | ✓ False · 77% | ✓ False · 88% | ✓ True · 67% |
| `script_75` | REVIEW | ✗ medium · 59% | ✗ refactor · 48% | ✓ False · 79% | ✓ False · 90% | ✗ False · 69% | ✓ True · 69% |
| `script_76` | REVIEW | ✗ medium · 64% | ✓ refactor · 69% | ✓ True · 58% | ✓ False · 76% | ✓ False · 65% | ✗ False · 54% |
| `script_77` | REVIEW | ✗ medium · 57% | ✓ refactor · 56% | ✗ False · 66% | ✓ False · 91% | ✓ True · 86% | ✓ True · 67% |
| `script_78` | REVIEW | ✗ medium · 63% | ✓ refactor · 59% | ✓ True · 72% | ✓ False · 88% | ✓ True · 90% | ✓ True · 70% |
| `script_79` | REVIEW | ✗ medium · 56% | ✓ refactor · 52% | ✓ True · 71% | ✓ False · 89% | ✓ True · 84% | ✓ True · 55% |
| `script_80` | REVIEW | ✗ medium · 70% | ✓ refactor · 57% | ✓ True · 62% | ✓ False · 92% | ✓ True · 83% | ✓ True · 59% |
| `script_81` | REVIEW | ✗ medium · 62% | ✗ refactor · 61% | ✓ True · 57% | ✓ False · 91% | ✗ False · 69% | ✗ True · 67% |
| `script_82` | REVIEW | ✗ medium · 70% | ✓ refactor · 59% | ✓ True · 68% | ✓ False · 91% | ✓ True · 84% | ✓ True · 59% |
| `script_83` | REVIEW | ✗ medium · 57% | ✓ refactor · 53% | ✓ False · 56% | ✓ False · 82% | ✗ False · 56% | ✓ True · 66% |
| `script_84` | REVIEW | ✗ medium · 74% | ✓ refactor · 51% | ✗ False · 62% | ✓ False · 82% | ✓ True · 92% | ✗ False · 50% |
| `script_85` | REVIEW | ✗ medium · 60% | ✓ refactor · 61% | ✗ False · 74% | ✓ False · 91% | ✓ True · 88% | ✓ True · 65% |
| `script_86` | REVIEW | ✗ medium · 64% | ✗ refactor · 64% | ✓ False · 78% | ✓ False · 89% | ✗ False · 68% | ✓ True · 65% |
| `script_87` | REVIEW | ✗ medium · 67% | ✗ refactor · 60% | ✗ False · 54% | ✗ False · 81% | ✓ True · 76% | ✓ True · 67% |
| `script_88` | REVIEW | ✗ medium · 74% | ✓ refactor · 60% | ✗ False · 64% | ✓ False · 86% | ✓ True · 69% | ✓ True · 59% |
| `script_89` | REVIEW | ✗ medium · 64% | ✓ refactor · 59% | ✓ True · 56% | ✓ False · 91% | ✓ True · 71% | ✓ True · 52% |
| `script_90` | REVIEW | ✗ medium · 66% | ✓ refactor · 51% | ✓ True · 69% | ✓ False · 84% | ✗ False · 73% | ✓ True · 53% |
| `script_91` | REVIEW | ✗ medium · 68% | ✗ refactor · 62% | ✓ False · 84% | ✓ False · 87% | ✓ True · 67% | ✗ False · 50% |
| `script_92` | REVIEW | ✗ medium · 62% | ✗ refactor · 61% | ✓ True · 56% | ✓ False · 87% | ✓ True · 88% | ✓ True · 53% |
| `script_93` | REVIEW | ✗ medium · 67% | ✓ refactor · 57% | ✓ True · 58% | ✓ False · 91% | ✓ True · 83% | ✓ True · 55% |
| `script_94` | REVIEW | ✗ medium · 65% | ✓ refactor · 57% | ✓ True · 62% | ✓ False · 91% | ✓ True · 83% | ✓ True · 57% |
| `script_95` | REVIEW | ✗ medium · 65% | ✓ refactor · 58% | ✓ True · 57% | ✓ False · 91% | ✓ True · 84% | ✓ True · 59% |
| `script_96` | REVIEW | ✗ medium · 74% | ✗ refactor · 54% | ✗ False · 69% | ✓ False · 80% | ✓ True · 83% | ✓ True · 55% |
| `script_97` | REVIEW | ✗ medium · 77% | ✗ refactor · 59% | ✗ False · 63% | ✓ False · 87% | ✓ True · 60% | ✓ True · 63% |
| `script_98` | REVIEW | ✗ medium · 60% | ✗ refactor · 55% | ✗ False · 62% | ✓ False · 85% | ✓ True · 70% | ✓ True · 54% |
| `script_99` | REVIEW | ✗ medium · 65% | ✗ refactor · 59% | ✓ True · 53% | ✓ False · 87% | ✓ True · 68% | ✓ True · 56% |

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
| `migration_complexity` | não | 37/99 | 37% | 37% | **+0%** | 1 | 60% | +23% |
| `rewrite_strategy` | não | 54/99 | 55% | 55% | **+0%** | 1 | 57% | +3% |
| `has_subquery` | sim | 79/99 | 80% | 58% | +22% | 2 | 68% | -12% |
| `has_window_function` | sim | 87/99 | 88% | 85% | +3% | 2 | 85% | -3% |
| `multi_source` | sim | 76/99 | 77% | 79% | **-2%** | 2 | 76% | -1% |
| `needs_human_review` | não | 53/99 | 54% | 70% | **-16%** | 2 | 63% | +9% |

> **baseline** = acurácia de sempre responder a classe majoritária do
> gabarito. **ganho** = acurácia menos baseline; zero ou negativo significa
> que a pergunta não carrega informação. **respostas distintas** = quantos
> rótulos diferentes o modelo chegou a emitir; `1` é um preditor constante.


> _Excesso de confiança_ = confiança média menos acurácia. Positivo
> significa que o modelo se diz mais certo do que de fato é.

**Nas 3 perguntas que o AST responde sozinho: 242/297 = 81%, contra um baseline de classe majoritária de 74% — ganho de +8%.**

> Uma pergunta binária com classes desbalanceadas **não** tem acaso em 50%.
> Comparar contra 50% infla o resultado; o número honesto é o ganho sobre
> responder sempre a classe majoritária.

## 4b. A acurácia esconde a qualidade do ranking

Acurácia responde *o limiar está certo?*. AUC responde *a ordenação está
certa?*. As duas se separam aqui, e ler só a primeira leva à conclusão
errada.

| pergunta | n | AUC | acc @0.5 | IC95 | baseline | McNemar p | melhor limiar | acc nele | leitura |
|---|---|---|---|---|---|---|---|---|---|
| `has_subquery` | 99 | **0.95** | 80% | 71%–87% | 58% | 0.0072 | 0.34 | **89%** | ganho real |
| `has_window_function` | 99 | **0.99** | 88% | 80%–93% | 85% | 0.2500 | 0.21 | **97%** | **ordena bem, limiar errado** |
| `multi_source` | 99 | **0.88** | 77% | 68%–84% | 79% | 0.8600 | 0.35 | **84%** | **ordena bem, limiar errado** |
| `needs_human_review` | 99 | **0.22** | 54% | 44%–63% | 70% | 0.0000 | 0.69 (inv.) | **78%** | **sinal invertido** |

> **AUC** = probabilidade de um caso positivo receber score maior que um
> negativo. 0.5 é o acaso. **Abaixo de 0.5 não é ausência de sinal — é
> sinal apontando para o lado errado**, que um limiar invertido recuperaria.
> **McNemar p** testa se a diferença para o baseline de classe majoritária
> é maior que o acaso; p alto significa que o ganho (ou a perda) é ruído.

> ⚠️ **O melhor limiar foi ajustado nos mesmos 99 pontos em que é medido.**
> É um teto otimista. A tabela seguinte é a versão implantável.


**Limiar validado em hold-out** — divisões estratificadas repetidas, corte
escolhido só na metade de treino e medido só na de teste:

| pergunta | acc @0,5 | acc hold-out | p05–p95 | limiar mediano | ganho sobre 0,5 | teto otimista | hindsight |
|---|---|---|---|---|---|---|---|
| `has_subquery` | 80% | **86%** | 80%–90% | 0.36 | +6% | 89% | +3% |
| `has_window_function` | 88% | **95%** | 92%–98% | 0.21 | +7% | 97% | +2% |
| `multi_source` | 77% | **79%** | 72%–84% | 0.41 | +3% | 84% | +4% |
| `needs_human_review` | 54% | **75%** | 70%–80% | 0.73 | +22% | 78% | +3% |

> **hindsight** = quanto do ganho aparente era escolha com o gabarito
> na mão. Poucos pontos significa que a calibração sobrevive ao
> hold-out; muitos significariam que o limiar ótimo era sorte.

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
| `has_subquery` | leaky | 32 | 97% | 0.97 | 80% | 0.95 | 0.0005 | **LR vence** |
| `has_subquery` | clean | 26 | 85% | 0.88 | 80% | 0.95 | 0.4731 | empate estatístico |
| `has_window_function` | leaky | 32 | 100% | 1.00 | 88% | 0.99 | 0.0005 | **LR vence** |
| `has_window_function` | clean | 30 | 85% | 0.92 | 88% | 0.99 | 0.5078 | empate estatístico |
| `multi_source` | leaky | 32 | 100% | 1.00 | 77% | 0.88 | 0.0000 | **LR vence** |
| `multi_source` | clean | 20 | 80% | 0.64 | 77% | 0.88 | 0.7428 | empate estatístico |
| `needs_human_review` | leaky | 32 | 89% | 0.94 | 54% | 0.22 | 0.0000 | **LR vence** |
| `needs_human_review` | clean | 32 | 89% | 0.94 | 54% | 0.22 | 0.0000 | **LR vence** |

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
| **medium** | 0 | 37 | 0 |
| **high** | 0 | 31 | 0 |

## 5b. Matriz de confusão — estratégia de reescrita

| gold \ predito | lift_and_shift | refactor | redesign | manual_rewrite |
|---|---|---|---|---|
| **lift_and_shift** | 0 | 35 | 0 | 0 |
| **refactor** | 0 | 54 | 0 | 0 |
| **redesign** | 0 | 10 | 0 | 0 |

## 5c. O argmax travou — mas existe sinal de ordenação?

A matriz acima tem uma coluna só: o argmax caiu na mesma classe para todos os scripts.
Isso *parece* ausência total de sinal. Mas a distribuição por trás do argmax
não é constante — ela se move na direção certa:

- Correlação de postos (Spearman, n=99) entre os pontos de rubrica e o **score esperado** do Laya: **rho = +0.593**.
- Entre pontos de rubrica e P(high): rho = +0.183.
- Entre pontos de rubrica e P(low): rho = -0.647.
- Mas o score esperado varia só de **0.789 a 1.118**, numa escala de 0 a 2 — todo
  o intervalo útil comprimido em torno da classe do meio.

| pontos gold | score esperado do Laya |
|---|---|
| 0 | 0.816 |
| 0 | 0.834 |
| 0 | 0.834 |
| 0 | 0.845 |
| 1 | 0.795 |
| 1 | 0.809 |
| 2 | 0.834 |
| 2 | 0.841 |
| 2 | 0.846 |
| 2 | 0.846 |
| 2 | 0.847 |
| 2 | 0.847 |
| 2 | 0.935 |
| 3 | 0.789 |
| 3 | 0.829 |
| 3 | 0.829 |
| 3 | 0.848 |
| 3 | 0.872 |
| 3 | 0.914 |
| 3 | 0.925 |
| 4 | 0.817 |
| 4 | 0.819 |
| 4 | 0.860 |
| 4 | 0.883 |
| 4 | 0.889 |
| 4 | 0.929 |
| 4 | 0.939 |
| 4 | 0.944 |
| 4 | 0.945 |
| 4 | 0.986 |
| 4 | 1.016 |
| 5 | 0.826 |
| 5 | 0.836 |
| 5 | 0.838 |
| 5 | 0.853 |
| 5 | 0.869 |
| 5 | 0.869 |
| 5 | 0.870 |
| 5 | 0.874 |
| 5 | 0.876 |
| 5 | 0.891 |
| 5 | 0.895 |
| 5 | 0.912 |
| 5 | 0.932 |
| 5 | 0.953 |
| 5 | 0.965 |
| 5 | 1.037 |
| 6 | 0.807 |
| 6 | 0.815 |
| 6 | 0.822 |
| 6 | 0.833 |
| 6 | 0.842 |
| 6 | 0.860 |
| 6 | 0.861 |
| 6 | 0.864 |
| 6 | 0.874 |
| 6 | 0.882 |
| 6 | 0.887 |
| 6 | 0.906 |
| 6 | 0.909 |
| 6 | 0.910 |
| 6 | 0.925 |
| 6 | 0.929 |
| 6 | 0.945 |
| 6 | 0.965 |
| 6 | 0.982 |
| 6 | 0.984 |
| 6 | 0.993 |
| 7 | 0.850 |
| 7 | 0.876 |
| 7 | 0.884 |
| 7 | 0.896 |
| 7 | 0.913 |
| 7 | 0.927 |
| 7 | 0.954 |
| 7 | 0.966 |
| 7 | 0.976 |
| 7 | 1.009 |
| 8 | 0.861 |
| 9 | 0.918 |
| 9 | 1.010 |
| 9 | 1.022 |
| 9 | 1.032 |
| 10 | 0.934 |
| 10 | 1.051 |
| 11 | 0.886 |
| 11 | 0.901 |
| 11 | 0.950 |
| 11 | 1.091 |
| 12 | 0.917 |
| 12 | 0.940 |
| 12 | 1.032 |
| 13 | 0.970 |
| 13 | 0.990 |
| 13 | 0.995 |
| 14 | 1.073 |
| 14 | 1.118 |
| 15 | 1.019 |
| 15 | 1.030 |

> Esta é a diferença entre *não ter sinal* e *não saber onde cortar*.
> A primeira exigiria outras features; a segunda se resolve com
> calibração de temperatura ou um limiar ajustado sobre o score
> esperado — muito mais barato.


## 6. Calibração

**ECE = 0.085** sobre 594 decisões (0 = perfeitamente calibrado).

| faixa de confiança | n | confiança média | acurácia | lacuna |
|---|---|---|---|---|
| 0.0-0.2 | 0 | — | — | — |
| 0.2-0.4 | 0 | — | — | — |
| 0.4-0.6 | 204 | 55% | 50% | 5% |
| 0.6-0.8 | 242 | 68% | 58% | 10% |
| 0.8-1.0 | 148 | 88% | 98% | 10% |

**Brier = 0.196** (0 = perfeito, 0.25 = chute a 50%).

## 7. Cobertura × acurácia — onde colocar o corte

| limiar | respostas acima | cobertura | acurácia | erros |
|---|---|---|---|---|
| 0.50 | 585 | 98% | 65% | 204 |
| 0.60 | 390 | 66% | 73% | 105 |
| 0.70 | 223 | 38% | 88% | 27 |
| 0.80 | 148 | 25% | 98% | 3 |
| 0.85 | 109 | 18% | 100% | 0 |
| 0.90 | 45 | 8% | 100% | 0 |
| 0.95 | 4 | 1% | 100% | 0 |

> Se a acurácia **não sobe** conforme o limiar aperta, a confiança não
> carrega informação sobre estar certo — e nenhum corte torna o
> classificador auto-operável.

## 7b. O mesmo corte, mas por script

A tabela acima conta **respostas**. Um script só é triado sem humano quando
*todas* as perguntas sobre ele passam do corte ao mesmo tempo — e a conjunção
de respostas independentes é muito mais dura que cada uma isolada.

| limiar | scripts com os 3 fatos acima do corte | cobertura | acurácia (IC95) | erros |
|---|---|---|---|---|
| 0.50 | 99 | 100% | 51% (41%–60%) | 49 |
| 0.60 | 59 | 60% | 63% (50%–74%) | 22 |
| 0.70 | 21 | 21% | 90% (71%–97%) | 2 |
| 0.80 | 7 | 7% | 86% (49%–97%) | 1 |
| 0.85 | 0 | 0% | — | 0 |
| 0.90 | 0 | 0% | — | 0 |

Sem exigir confiança nenhuma, **50/99 scripts (51%) acertam os três fatos verificáveis**. É a distância
entre esse número e a coluna de cobertura acima que mede o custo da exigência
de confiança — e é ela que zera o `AUTO`.

## 8. Onde o modelo erra

| script | pontos gold | fontes | arestas | subq | erros de 6 |
|---|---|---|---|---|---|
| `script_01` | 0 | 3 | 2 | 0 | **3** |
| `script_02` | 0 | 3 | 2 | 0 | **3** |
| `script_03` | 0 | 3 | 2 | 0 | **3** |
| `script_04` | 0 | 3 | 2 | 0 | **3** |
| `script_05` | 1 | 4 | 3 | 0 | **3** |
| `script_06` | 1 | 4 | 3 | 0 | **3** |
| `script_07` | 2 | 4 | 3 | 0 | **3** |
| `script_08` | 2 | 4 | 3 | 0 | **2** |
| `script_09` | 2 | 3 | 2 | 0 | **1** |
| `script_10` | 2 | 3 | 2 | 0 | **4** |
| `script_11` | 2 | 4 | 3 | 0 | **3** |
| `script_12` | 2 | 3 | 2 | 0 | **4** |
| `script_13` | 2 | 3 | 2 | 0 | **4** |
| `script_14` | 3 | 4 | 1 | 3 | **1** |
| `script_15` | 3 | 5 | 4 | 0 | **1** |
| `script_16` | 3 | 5 | 4 | 0 | **3** |
| `script_17` | 3 | 5 | 4 | 0 | **3** |
| `script_18` | 3 | 3 | 2 | 0 | **4** |
| `script_19` | 3 | 3 | 2 | 0 | **1** |
| `script_20` | 3 | 3 | 2 | 1 | **1** |
| `script_21` | 4 | 3 | 2 | 1 | **3** |
| `script_22` | 4 | 6 | 5 | 0 | **4** |
| `script_23` | 4 | 5 | 4 | 0 | **2** |
| `script_24` | 4 | 4 | 2 | 1 | **2** |
| `script_25` | 4 | 5 | 3 | 1 | **3** |
| `script_26` | 4 | 4 | 3 | 0 | **2** |
| `script_27` | 4 | 4 | 1 | 1 | **3** |
| `script_28` | 4 | 1 | 0 | 1 | **1** |
| `script_29` | 4 | 4 | 2 | 1 | **3** |
| `script_30` | 4 | 4 | 3 | 2 | **3** |
| `script_31` | 4 | 3 | 2 | 1 | **3** |
| `script_32` | 5 | 5 | 3 | 1 | **2** |
| `script_33` | 5 | 4 | 3 | 1 | **3** |
| `script_34` | 5 | 5 | 0 | 0 | **0** |
| `script_35` | 5 | 3 | 2 | 2 | **4** |
| `script_36` | 5 | 4 | 3 | 2 | **0** |
| `script_37` | 5 | 5 | 3 | 1 | **2** |
| `script_38` | 5 | 6 | 5 | 0 | **1** |
| `script_39` | 5 | 4 | 3 | 1 | **3** |
| `script_40` | 5 | 5 | 4 | 0 | **0** |
| `script_41` | 5 | 5 | 4 | 1 | **0** |
| `script_42` | 5 | 5 | 4 | 2 | **1** |
| `script_43` | 5 | 2 | 0 | 8 | **2** |
| `script_44` | 5 | 4 | 3 | 1 | **3** |
| `script_45` | 5 | 6 | 5 | 0 | **3** |
| `script_46` | 5 | 4 | 4 | 0 | **0** |
| `script_47` | 5 | 4 | 3 | 1 | **3** |
| `script_48` | 6 | 4 | 4 | 0 | **0** |
| `script_49` | 6 | 5 | 6 | 1 | **1** |
| `script_50` | 6 | 5 | 4 | 0 | **0** |
| `script_51` | 6 | 7 | 5 | 3 | **1** |
| `script_52` | 6 | 6 | 6 | 0 | **2** |
| `script_53` | 6 | 5 | 3 | 2 | **2** |
| `script_54` | 6 | 6 | 5 | 1 | **3** |
| `script_55` | 6 | 3 | 1 | 2 | **1** |
| `script_56` | 6 | 6 | 7 | 0 | **3** |
| `script_57` | 6 | 5 | 3 | 2 | **2** |
| `script_58` | 6 | 7 | 6 | 0 | **1** |
| `script_59` | 6 | 7 | 6 | 0 | **3** |
| `script_60` | 6 | 6 | 7 | 0 | **2** |
| `script_61` | 6 | 5 | 6 | 1 | **1** |
| `script_62` | 6 | 6 | 3 | 1 | **2** |
| `script_63` | 6 | 6 | 5 | 1 | **2** |
| `script_64` | 6 | 4 | 4 | 0 | **0** |
| `script_65` | 6 | 4 | 3 | 0 | **1** |
| `script_66` | 6 | 3 | 2 | 2 | **4** |
| `script_67` | 6 | 1 | 0 | 6 | **0** |
| `script_68` | 6 | 4 | 3 | 0 | **1** |
| `script_69` | 7 | 5 | 6 | 1 | **4** |
| `script_70` | 7 | 7 | 6 | 0 | **2** |
| `script_71` | 7 | 4 | 4 | 0 | **1** |
| `script_72` | 7 | 7 | 5 | 3 | **2** |
| `script_73` | 7 | 5 | 3 | 2 | **3** |
| `script_74` | 7 | 2 | 0 | 15 | **2** |
| `script_75` | 7 | 6 | 7 | 0 | **3** |
| `script_76` | 7 | 3 | 0 | 3 | **2** |
| `script_77` | 7 | 5 | 3 | 3 | **2** |
| `script_78` | 7 | 4 | 3 | 8 | **1** |
| `script_79` | 8 | 7 | 5 | 3 | **1** |
| `script_80` | 9 | 5 | 6 | 6 | **1** |
| `script_81` | 9 | 7 | 6 | 2 | **4** |
| `script_82` | 9 | 5 | 6 | 6 | **1** |
| `script_83` | 9 | 9 | 9 | 0 | **2** |
| `script_84` | 10 | 4 | 3 | 2 | **3** |
| `script_85` | 10 | 8 | 2 | 3 | **2** |
| `script_86` | 11 | 13 | 15 | 0 | **3** |
| `script_87` | 11 | 7 | 6 | 6 | **4** |
| `script_88` | 11 | 6 | 5 | 2 | **2** |
| `script_89` | 11 | 8 | 9 | 1 | **1** |
| `script_90` | 12 | 6 | 8 | 1 | **2** |
| `script_91` | 12 | 5 | 6 | 0 | **3** |
| `script_92` | 12 | 10 | 1 | 4 | **2** |
| `script_93` | 13 | 6 | 9 | 4 | **1** |
| `script_94` | 13 | 6 | 9 | 4 | **1** |
| `script_95` | 13 | 6 | 9 | 4 | **1** |
| `script_96` | 14 | 5 | 6 | 19 | **3** |
| `script_97` | 14 | 6 | 7 | 14 | **3** |
| `script_98` | 15 | 12 | 10 | 1 | **3** |
| `script_99` | 15 | 9 | 10 | 1 | **2** |

## 9. Latência

- Carga do modelo: **6.878 s** (uma vez).
- Por script (6 perguntas): **p50 = 2263 ms · p95 = 2505 ms** (min 2026, max 2556).
- Lote completo: **225.8 s** para 99 scripts.
- Por pergunta: ~377 ms.

Extrapolando para as 99 queries do corpus: ~226 s de inferência em CPU.

| script | estimado (ms) | medido (ms) | erro |
|---|---|---|---|
| `script_01` | 1969 | 2209 | +12% |
| `script_02` | 1687 | 2249 | +33% |
| `script_03` | 1687 | 2273 | +35% |
| `script_04` | 1687 | 2092 | +24% |
| `script_05` | 1687 | 2099 | +24% |
| `script_06` | 1687 | 2238 | +33% |
| `script_07` | 1718 | 2344 | +36% |
| `script_08` | 1718 | 2240 | +30% |
| `script_09` | 1718 | 2259 | +31% |
| `script_10` | 1760 | 2349 | +33% |
| `script_11` | 1718 | 2254 | +31% |
| `script_12` | 1760 | 2322 | +32% |
| `script_13` | 1760 | 2285 | +30% |
| `script_14` | 1781 | 2310 | +30% |
| `script_15` | 1687 | 2149 | +27% |
| `script_16` | 1687 | 2062 | +22% |
| `script_17` | 1687 | 2026 | +20% |
| `script_18` | 1812 | 2304 | +27% |
| `script_19` | 1823 | 2213 | +21% |
| `script_20` | 1823 | 2176 | +19% |
| `script_21` | 1948 | 2505 | +29% |
| `script_22` | 1687 | 2154 | +28% |
| `script_23` | 2031 | 2233 | +10% |
| `script_24` | 1927 | 2319 | +20% |
| `script_25` | 1781 | 2169 | +22% |
| `script_26` | 1812 | 2311 | +28% |
| `script_27` | 1927 | 2341 | +21% |
| `script_28` | 1885 | 2360 | +25% |
| `script_29` | 1927 | 2293 | +19% |
| `script_30` | 1781 | 2209 | +24% |
| `script_31` | 1948 | 2556 | +31% |
| `script_32` | 1823 | 2249 | +23% |
| `script_33` | 1865 | 2335 | +25% |
| `script_34` | 1760 | 2224 | +26% |
| `script_35` | 1854 | 2264 | +22% |
| `script_36` | 1885 | 2449 | +30% |
| `script_37` | 1823 | 2240 | +23% |
| `script_38` | 1969 | 2148 | +9% |
| `script_39` | 1844 | 2230 | +21% |
| `script_40` | 2000 | 2261 | +13% |
| `script_41` | 1885 | 2321 | +23% |
| `script_42` | 1885 | 2330 | +24% |
| `script_43` | 1927 | 2300 | +19% |
| `script_44` | 1844 | 2204 | +20% |
| `script_45` | 1687 | 2160 | +28% |
| `script_46` | 1760 | 2296 | +30% |
| `script_47` | 1844 | 2249 | +22% |
| `script_48` | 1844 | 2263 | +23% |
| `script_49` | 1823 | 2228 | +22% |
| `script_50` | 1760 | 2301 | +31% |
| `script_51` | 1885 | 2398 | +27% |
| `script_52` | 1718 | 2240 | +30% |
| `script_53` | 1948 | 2513 | +29% |
| `script_54` | 1781 | 2255 | +27% |
| `script_55` | 1844 | 2242 | +22% |
| `script_56` | 1687 | 2138 | +27% |
| `script_57` | 1948 | 2514 | +29% |
| `script_58` | 1687 | 2180 | +29% |
| `script_59` | 1687 | 2180 | +29% |
| `script_60` | 2031 | 2198 | +8% |
| `script_61` | 1823 | 2265 | +24% |
| `script_62` | 1823 | 2229 | +22% |
| `script_63` | 1781 | 2181 | +22% |
| `script_64` | 1844 | 2247 | +22% |
| `script_65` | 1844 | 2280 | +24% |
| `script_66` | 2011 | 2498 | +24% |
| `script_67` | 1781 | 2255 | +27% |
| `script_68` | 2115 | 2249 | +6% |
| `script_69` | 2136 | 2213 | +4% |
| `script_70` | 1781 | 2195 | +23% |
| `script_71` | 1823 | 2288 | +26% |
| `script_72` | 1885 | 2293 | +22% |
| `script_73` | 1979 | 2506 | +27% |
| `script_74` | 1927 | 2378 | +23% |
| `script_75` | 1718 | 2229 | +30% |
| `script_76` | 1854 | 2267 | +22% |
| `script_77` | 1823 | 2217 | +22% |
| `script_78` | 1781 | 2217 | +24% |
| `script_79` | 1927 | 2490 | +29% |
| `script_80` | 1927 | 2326 | +21% |
| `script_81` | 1781 | 2232 | +25% |
| `script_82` | 1927 | 2362 | +23% |
| `script_83` | 1760 | 2271 | +29% |
| `script_84` | 1885 | 2384 | +26% |
| `script_85` | 1948 | 2390 | +23% |
| `script_86` | 2188 | 2170 | -1% |
| `script_87` | 1844 | 2226 | +21% |
| `script_88` | 1927 | 2362 | +23% |
| `script_89` | 1844 | 2275 | +23% |
| `script_90` | 2104 | 2232 | +6% |
| `script_91` | 1844 | 2256 | +22% |
| `script_92` | 1896 | 2408 | +27% |
| `script_93` | 1948 | 2371 | +22% |
| `script_94` | 1948 | 2324 | +19% |
| `script_95` | 1948 | 2322 | +19% |
| `script_96` | 2386 | 2406 | +1% |
| `script_97` | 1948 | 2392 | +23% |
| `script_98` | 1896 | 2386 | +26% |
| `script_99` | 1896 | 2356 | +24% |

> O modelo de custo foi ajustado com texto sintético e subestima os cards
> reais de forma consistente; serve para dimensionar um lote, não para SLA.

