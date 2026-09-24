# Discovery: Laya como classificador para triagem de migração SQL

Avaliação técnica de [Laya](https://github.com/NandhaKishorM/laya) — motor de
decisão não-autoregressivo, sem geração de texto — para triar um backlog de SQL
legado antes de uma migração.

**Pergunta:** quantos scripts podem ser classificados sem envolver um humano, e
com que confiabilidade?

**Corpus:** as 99 queries do TPC-DS · **12 experimentos** · 173 testes ·
execução em CPU.

📄 [Relatório visual](reports/discovery.html)
([online](https://claude.ai/code/artifact/6f7ffaeb-abbb-47c1-97b6-f662771470af)) ·
🧪 [Registro de experimentos](docs/experiments.md) ·
🔬 [Metodologia](docs/methodology.md) ·
⚠️ [Limitações](docs/limitations.md) ·
🔧 [Plano de fine-tune](docs/finetuning.md)

---

## Veredito

**Não adotar este checkpoint zero-shot para triagem de migração.** O modelo tem
capacidade real e mensurável, mas ela não aparece onde o negócio precisa.

| pergunta | melhor resultado | baseline | vs. regressão logística | serve? |
|---|---|---|---|---|
| `has_subquery` | **95%** (ensemble + limiar) | 58% | **+15,2 pts** | sim — mas o `sqlglot` faz de graça |
| `has_window_function` | 87% (ensemble) | 85% | +4,1 pts (ruído) | não |
| `multi_source` | 79% | 79% | +2,8 pts (ruído) | não |
| `migration_complexity` | **38–52%** em 3 bandas | 31% | não testado | **sim, para ordenar backlog** |
| `rewrite_strategy` | 55% = taxa-base | 55% | — | **não zero-shot** |
| `needs_human_review` | 75% | 70% | **−9,8 pts** | não |

### As três conclusões que importam

**1. Complexidade tem base utilizável.** AUC 0,86 separando `low` de `high`, e
**só 6% dos erros são de duas bandas** — 94% das vezes erra no máximo uma banda
adjacente. Chamar um `high` de `low` é o erro que estraga planejamento, e ele é
raro. Para ordenar um backlog e decidir por onde começar, serve.
([E11](docs/experiments.md#e11))

**2. Estratégia de reescrita não funciona zero-shot — e nunca deveria ter sido
testada assim.** Quatro formulações bem diferentes, todas colapsam em
`refactor`. Mas o rótulo depende do padrão de código da empresa: o que é
"refactor" numa casa é "lift and shift" em outra. O caminho é **fine-tune com o
histórico de decisões do cliente**. ([E11](docs/experiments.md#e11) ·
[plano](docs/finetuning.md))

**3. O desenho do experimento não valida a pergunta de negócio.** O cartão de
~100 tokens que o modelo lê **lista os fatos perguntados**, e o gabarito de
complexidade deriva dos mesmos números. Uma regressão logística com acesso a
essas features acerta 97–100%. As conclusões **negativas** deste estudo valem;
as **positivas** sobre automação, não.
([limitações](docs/limitations.md#circularidade))

### O caso de negócio, com números

Classificar 5.000 scripts nas duas perguntas de valor:

| | só o rótulo | com justificativa |
|---|---|---|
| Haiku 4.5 | $5,83 | $19 |
| Opus 5 | $20 | $94 |
| **Laya** | **~$0,13 de CPU** | — |

Relativamente 10–100× mais barato; em absoluto, dezenas de dólares. **Custo de
token sozinho não justifica um classificador pior.** Os dois eixos que
justificam são **residência de dado** (roda local, o SQL do cliente não sai do
perímetro) e **fine-tune por cliente** (um encoder de 421M você afina com
centenas de exemplos rotulados; Opus não). ([E12](docs/experiments.md#e12))

---

## O que este repositório entrega

**Bloco A — censo determinístico.** Vale por si só, independentemente do
veredito sobre o Laya: perfil objetivo das 99 queries, 47 features por script
extraídas do AST, grafo de joins, e uma rubrica de complexidade com limiares
derivados de percentis do corpus em vez de opinião. Roda em segundos, sem torch.

**Bloco B — avaliação do modelo.** Relatório por run com acurácia **e AUC**,
baseline de classe majoritária, baseline de regressão logística sobre as mesmas
features, McNemar, IC95, calibração, limiar validado em hold-out, matrizes de
confusão, cobertura×acurácia por resposta **e** por script, e latência.

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
mlaya report   --run-id full99                # runs/full99/report.md
```

Os outros onze experimentos e seus comandos estão em
[`docs/experiments.md`](docs/experiments.md).

### Auditoria e testes

```bash
pytest                                   # 173 testes
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
