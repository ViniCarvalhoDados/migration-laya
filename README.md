# Discovery: Laya como classificador para triagem de migração SQL

Avaliação técnica de [Laya](https://github.com/NandhaKishorM/laya) — motor de
decisão não-autoregressivo, sem geração de texto — para triar um backlog de SQL
legado antes de uma migração.

**Pergunta:** quantos scripts podem ser classificados sem envolver um humano, e
com que confiabilidade?

**Corpus:** as 99 queries do TPC-DS · **13 experimentos** · 191 testes ·
execução em CPU · **duas auditorias externas**, ambas com achados que mudaram
conclusões.

📄 [Relatório visual](reports/discovery.html)
([online](https://claude.ai/code/artifact/6f7ffaeb-abbb-47c1-97b6-f662771470af)) ·
🧪 [Registro de experimentos](docs/experiments.md) ·
🔬 [Metodologia](docs/methodology.md) ·
⚠️ [Limitações](docs/limitations.md) ·
🔧 [Plano de fine-tune](docs/finetuning.md)

---

## Veredito

**Não adotar este checkpoint zero-shot para triagem de migração.** O modelo
ordena o corpus melhor do que a acurácia sugere — mas não melhor do que a
aritmética que já roda no extrator.

Leia a tabela pela **última coluna de regressão**. A LR *limpa* não recebe as
features que definem o rótulo; a LR *mesma info* recebe — e é exatamente o que
o cartão de evidências entrega ao Laya. Medir só contra a limpa foi o erro que
a segunda auditoria encontrou ([E13](docs/experiments.md#e13)).

| pergunta | melhor resultado | baseline | vs. LR limpa | vs. LR mesma info | serve? |
|---|---|---|---|---|---|
| `has_subquery` | **97%** (ensemble + limiar) | 58% | +17,2 pts | **+3,3** (−4 a +14) | não — empata, e o `sqlglot` faz de graça |
| `has_window_function` | 88% (ensemble) | 86% | +3,6 pts | **−11,3** (−22 a −6) | não |
| `multi_source` | 80% | 78% | +3,8 pts | **−18,1** (−24 a −10) | não |
| `migration_complexity` | 40–54% em 3 bandas | **37%** | — | a rubrica acerta **100%** de graça | não |
| `rewrite_strategy` | 55% = taxa-base | 55% | — | — | **não zero-shot** |
| `needs_human_review` | 74% | 70% | −9,8 pts | −9,8 pts | não |

**Com a mesma informação que o cartão, o Laya não vence nenhuma das quatro.**

### As três conclusões que importam

**1. Complexidade: o modelo ordena, mas quem ordena o backlog é a rubrica.** O
score esperado separa `low` de `high` com AUC 0,87 e raramente erra feio — só
8% dos erros são de duas bandas. Mas o gabarito de complexidade **é a rubrica**,
uma função determinística e gratuita das features que o extrator já calcula:
ela acerta 100% em milissegundos, e o Laya reproduz 54% dela — só depois de
cortes ajustados em dados já rotulados. Sem esse ajuste o argmax é **constante
em `medium` nas 99 queries**, exatamente o baseline de 37%. Para ordenar
backlog, rode a rubrica. ([E11](docs/experiments.md#e11) ·
[E13](docs/experiments.md#e13))

**2. Estratégia de reescrita não funciona zero-shot — e nunca deveria ter sido
testada assim.** Quatro formulações bem diferentes, todas colapsam em
`refactor`. Mas o rótulo depende do padrão de código da empresa: o que é
"refactor" numa casa é "lift and shift" em outra. O caminho é **fine-tune com o
histórico de decisões do cliente**. ([E11](docs/experiments.md#e11) ·
[plano](docs/finetuning.md))

**3. O desenho do experimento não valida a pergunta de negócio.** O cartão de
~100 tokens que o modelo lê **lista os fatos perguntados**, e o gabarito de
complexidade deriva dos mesmos números. Uma regressão logística com acesso a
essas features acerta 94–100%. As conclusões **negativas** deste estudo valem —
e ficaram mais fortes, porque o comparador ficou mais duro. As **positivas**
sobre automação, não: das duas que existiam, nenhuma sobreviveu à segunda
auditoria. ([limitações](docs/limitations.md#circularidade) ·
[E13](docs/experiments.md#e13))

### E o custo, já que não é por aí

Classificar 5.000 scripts nas duas perguntas comerciais:

| | só o rótulo | com justificativa |
|---|---|---|
| Haiku 4.5 | $5,83 | $19 |
| Opus 5 | $20 | $94 |
| **Laya** | **~$0,13 de CPU** | — |

Relativamente 10–100× mais barato; em absoluto, dezenas de dólares. **Custo de
token sozinho não justifica um classificador pior** — e depois de
[E13](docs/experiments.md#e13) ele é, nas quatro perguntas medidas, pior.

Os dois eixos que ainda justificam olhar para um encoder local são outros:
**residência de dado** (roda no perímetro do cliente, o SQL não sai) e
**fine-tune por cliente** (um encoder de 421M você afina com centenas de
exemplos rotulados; Opus não). O segundo é o único teste que ainda pode virar o
resultado, porque é o único em que o gabarito deixa de ser uma função das
features e passa a ser a decisão real de alguém. ([E12](docs/experiments.md#e12) ·
[plano](docs/finetuning.md))

---

## O que este repositório entrega

**Bloco A — censo determinístico.** Vale por si só, independentemente do
veredito sobre o Laya: perfil objetivo das 99 queries, 47 features por script
extraídas do AST, grafo de joins, e uma rubrica de complexidade com limiares
derivados de percentis do corpus em vez de opinião. Roda em segundos, sem torch.

**Bloco B — avaliação do modelo.** Relatório por run com acurácia **e AUC**,
baseline de classe majoritária, **duas** regressões logísticas sobre as mesmas
features (com e sem as que definem o rótulo), comparação pareada em 200 splits
com tudo ajustado só no treino, McNemar, IC95, calibração, limiar validado em
hold-out, matrizes de confusão, cobertura×acurácia por resposta **e** por
script, e latência.

**Ferramentas para o próximo passo.** `derive-labels` recupera rótulos de uma
migração já concluída comparando os ASTs antes/depois; `export-training` emite
os JSONL no formato do notebook de fine-tune, com split por família para não
vazar quase-duplicatas entre treino e teste.

---

## Como rodar

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"

# Bloco A — sem Laya, sem torch, segundos
mlaya census --verify --emit-rubric   # 99 queries → censo + rubrica + relatório
mlaya sample --n 99 --seed 42         # gera repos/legacy/scripts/ + state/script_*.yml
mlaya card                            # evidence cards + orçamento de tokens

# Bloco B — Laya (baixa ~1 GB de pesos na primeira vez)
uv pip install laya
mlaya ask      --run-id full99 --no-purpose   # ~3min45s em CPU
mlaya decide   --run-id full99
mlaya baseline --run-id full99                # regressão logística vs Laya
mlaya paired   --run-id full99                # pareado, contra as duas LRs
mlaya report   --run-id full99                # runs/full99/report.md
```

Os outros doze experimentos e seus comandos estão em
[`docs/experiments.md`](docs/experiments.md) — incluindo `mlaya paired`
(comparação pareada contra as duas regressões) e `mlaya business` (as duas
perguntas comerciais), que fecham o que antes só existia em script solto.

### Auditoria e testes

```bash
pytest                                   # 191 testes
mlaya census --verify                    # falha se alguma das 99 não parsear
mlaya features corpus/tpcds/query23.sql  # dump de features para conferência manual
mlaya card --check                       # valida orçamento sem escrever
```

---

## Estrutura

```
corpus/tpcds/        99 queries originais, intocadas
config/              perguntas tipadas e rubrica (gerada do censo)
state/               censo, perfil, gabarito e um YAML por script
runs/<id>/           respostas brutas, decisões e relatório de cada experimento
reports/             perfil do corpus e relatório visual
docs/                metodologia, experimentos, limitações, fine-tune
src/migration_laya/  extrator, rubrica, cliente do Laya, métricas, baseline
```

---

## Procedência

Corpus: 99 queries TPC-DS via [agirish/tpcds](https://github.com/agirish/tpcds),
derivadas da especificação do Transaction Processing Performance Council — uso
de avaliação interna, procedência em `repos/legacy/scripts/NOTICE.md`. As cópias
em `repos/legacy/scripts/*.sql` não são versionadas: são saída de `mlaya sample`
e se regeneram com um comando.

Modelo: [convaiinnovations/laya](https://github.com/NandhaKishorM/laya) 0.3.10,
Apache 2.0, executado em CPU.
