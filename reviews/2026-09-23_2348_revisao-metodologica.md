# Revisão metodológica: 2026-09-23 23:48 (−03:00)

| | |
|---|---|
| **Commit avaliado** | `b6fc738`: Atualiza o relatório visual com E11, E12 e o caminho de fine-tune |
| **Escopo** | README, `docs/`, `config/`, `src/migration_laya/`, `state/`, `runs/` |
| **Pergunta do estudo** | O Laya classifica scripts de migração SQL com acerto suficiente e custo menor que as alternativas? |
| **Revisor** | Claude Opus 5.5, a pedido de Vinicius Carvalho, no papel de pesquisador de engenharia de software |

> **Aviso sobre o working tree.** Durante a revisão apareceram no working tree
> alterações que não fazem parte do commit avaliado: `paired.py`, `business.py`,
> `runs/*/paired_*.yml`, `runs/business/business.yml`, testes novos e edições
> em `README.md` e `docs/`. Esta revisão avalia o `b6fc738`. Os números do braço
> "LR leaky" em R01 vieram desses arquivos não commitados e precisam ser
> confirmados quando eles forem commitados.

---

## Síntese

O processo é melhor que a média da literatura aplicada. Ele corrige a si mesmo
(E3→E2, E8→E6, E9→E7/E8), registra previsões antes de rodar (E5, E9), faz
controle de confundidor (E5), usa baseline de classe majoritária, AUC, IC de
Wilson, hold-out de limiar, teste de paráfrase e teste de negação, e documenta
as limitações. A engenharia de dados também é cuidadosa: identidade pela query
de origem, rubrica derivada de percentis, cross join avaliado por escopo e split
por família no `export-training`.

O problema está nas **conclusões positivas**. Elas não passam por baselines
triviais que o próprio estudo já tinha em mãos:

| conclusão do README | situação |
|---|---|
| 1. Complexidade tem base utilizável | **Não se sustenta.** Contar linhas é melhor (R02). |
| 2. Estratégia não funciona zero-shot | A direção está certa, mas a afirmação é forte demais (R09, R14). |
| 3. O desenho não valida a pergunta de negócio | **Sustenta-se.** É a conclusão mais importante do estudo. |
| Veredito: não adotar o zero-shot | **Mantido, e mais forte**: neste desenho, o Laya não supera nenhum baseline determinístico. |

---

## Pontos graves

### R01: A comparação Laya × LR é assimétrica {#r01}

**Onde:** E8, E10, tabela de veredito do README (`has_subquery`: "+15,2 pts vs
regressão logística").

**Problema.** O Laya lê o cartão, que imprime `subqueries=N`,
`window_fns=N` e `sources=N`. A LR usada na comparação é a **clean**, da qual
`baseline.LEAKY` remove justamente essas features. Um lado tem a resposta e o
outro não. O braço justo é a LR **leaky**, que tem a mesma informação do cartão.

**Evidência.** `runs/ensemble/paired_ensemble.yml` (não commitado), 200 splits:

| pergunta | Laya 6× | LR clean | LR leaky | Laya − leaky |
|---|---|---|---|---|
| `has_subquery` | 96,8% | ~80% | 93,5% | +3,3 |
| `has_window_function` | 88,2% | ~83% | 99,5% | **−11,3** |
| `multi_source` | 79,9% | ~77% | 97,9% | **−18,1** |
| `needs_human_review` | 74,1% | ~84% | 83,9% | −9,8 |

Teto mais simples: regras de uma linha que leem o próprio cartão acertam
**99/99** cada uma (`subquery_count>0`, `window_function_count>0`,
`source_tables>=4`). Ver o [script de reprodução](#reproducao).

**Recomendação.** Na tabela de veredito, comparar contra a LR leaky e contra a
regra trivial. Reescrever "única vitória sólida do Laya" (E10) como "empate com
a aritmética sobre o mesmo input; abaixo da regra trivial".

### R02: Complexidade não bate o baseline trivial {#r02}

**Onde:** E11, conclusão nº 1 do README ("AUC 0,86… para ordenar backlog,
serve") e a linha "vs. regressão logística: não testado".

**Problema.** O gabarito de complexidade é função determinística das features,
e o próprio `limitations.md` registra ρ = 0,82 com contagem de linhas. O
baseline óbvio não foi rodado.

**Evidência** (calculada nesta revisão sobre `state/script_*.yml`):

| preditor | AUC low↔high | 3 bandas | erro de 2 bandas |
|---|---|---|---|
| Laya p1 (a melhor de 4 redações) | 0,86 | 52% hold-out / 58% | 6% |
| **só `loc_code`** | **0,98** | **71%** | **1%** |
| só `max_nesting_depth` | 0,89 | — | — |
| só `subquery_count` | 0,83 | — | — |
| sempre `medium` | 0,50 | 37% | 0% |

As 3 bandas de `loc_code` usam cortes nos quantis do gabarito, dentro da
amostra. É o mesmo critério da tabela "estrutura do erro" do E11, então os dois
números são comparáveis.

**Recomendação.** Rebaixar a conclusão nº 1 para "há sinal, mas abaixo de
contar linhas". Incluir `loc_code` e a LR leaky como baselines obrigatórios de
`migration_complexity` no `mlaya report`.

### R03: Resultados sem código de análise commitado {#r03}

**Onde:** E8, E10, E11 e E12. O `docs/experiments.md` diz que "todos os números
são regeneráveis pelos comandos indicados".

**Problema.**

- **E11:** não havia código de análise. `mlaya ensemble` só trata perguntas
  `noul`, e "3 bandas (hold-out)" e "AUC low↔high" existiam só no texto.
- **E12:** não há script de custo. Os preços, a premissa de tokens
  (167/517/+250) e o custo de CPU (~$1,28 para 50k) não são auditáveis.
- **E8/E10 pareados:** não havia código no commit que publicou os números.
- **Dois números para o mesmo modelo no E11:** 52% ("hold-out") e 58% ("banda
  exata", com cortes nos quantis do gabarito). O documento não explica a
  diferença, e a segunda usa a distribuição do gabarito para fixar os cortes.

**Estado observado.** Há trabalho em andamento no working tree (`business.py`,
`paired.py`). Isso só resolve o ponto quando estiver commitado **e** os números
publicados baterem com a saída desses comandos.

### R04: O caso de custo não mede o acerto do LLM {#r04}

**Onde:** E12 e a seção "O caso de negócio" do README.

**Problema.** O objetivo do estudo é **custo e acerto**. O E12 mede o custo do
LLM, mas nunca o acerto dele. Sem isso não existe fronteira custo × acerto.

**Recomendações.**

1. Rodar o Haiku 4.5 e o Sonnet 5 lendo o SQL bruto nas 6 perguntas e nas 99
   queries. Custa poucos dólares.
2. Trocar o custo por token por um modelo de custo total:
   `custo = c_inferência + P(HUMAN_REVIEW)·c_hora_engenheiro + P(erro|AUTO)·c_retrabalho`.
   Com 0% de `AUTO` (E3), o custo efetivo do Laya hoje é revisar 100% dos
   scripts manualmente.
3. Testar os dois eixos que o estudo usa para defender o Laya contra
   alternativas que também os têm:
   - **Residência de dado:** um LLM aberto de 7–14B rodando local também não
     tira o SQL do perímetro.
   - **Fine-tune:** um encoder de código (CodeBERT/UniXcoder) ou uma LR/GBM
     sobre as 47 features também se afina com centenas de exemplos.

---

## Pontos moderados

### R05: Near-duplicates atravessam os splits de avaliação {#r05}

O `finetuning.md` identifica 82 famílias em 99 scripts, mas o split por família
só existe no `export-training`. E7, E8 e E10 usam metades estratificadas
aleatórias, então gêmeos como q33/q56/q60 caem em lados opostos. Isso infla os
modelos ajustados (LR e limiar) mais do que o Laya zero-shot. **Recomendação:**
usar split por família também nos hold-outs de avaliação.

### R06: A dispersão entre splits é reportada como IC {#r06}

O "IC90" de E8 e E10 é o p05–p95 de 200 metades que se sobrepõem, e isso
subestima a variância. **Recomendação:** usar o *corrected resampled t-test*
(Nadeau & Bengio, 2003) ou bootstrap por família.

### R07: Caminhos de análise demais para n = 99 {#r07}

São 12 experimentos, 4 a 6 redações por pergunta, limiar invertido e escolha de
variante. O E11 reconhece a seleção (38–52%), mas o raciocínio não é aplicado ao
estudo inteiro. Exemplo: inverter o limiar de `needs_human_review` porque o AUC
saiu 0,22 é uma decisão tirada do dado. O ganho (75% contra 70% de baseline)
está dentro do ruído, e a pergunta falhou no teste de negação (E9).
**Recomendação:** tratar como exploratórios os resultados que dependem de
escolhas feitas depois de ver o dado, e reservar um conjunto confirmatório.

### R08: A árvore de decisão usa confiança não calibrada {#r08}

O checkpoint avisa que as temperaturas são inválidas. Mesmo assim, `AUTO` exige
≥ 0,85 fixo, então "0/99 AUTO" é um artefato da falta de calibração, não uma
medida de capacidade. **Recomendação:** calibrar (Platt ou isotônica) em
hold-out antes de aplicar a árvore, e reportar a cobertura por script de novo.

### R09: `rewrite_strategy` foi avaliada só por argmax {#r09}

As binárias foram salvas por limiar ajustado, mas a pergunta `choice` não teve
tratamento equivalente. **Recomendação:** aplicar correção de prior ou uma
multinomial sobre as 4 probabilidades, em hold-out, e reportar AUC one-vs-rest.
Até lá, "ausência de capacidade zero-shot" deve virar "o argmax colapsa numa
classe". E, como o gabarito é de um único LLM (R14), o resultado é
indeterminado nos dois sentidos.

### R10: Interferência e truncamento com várias perguntas na mesma chamada {#r10}

O E9 envia 12 variantes por chamada, o E10 envia 24 e o E11 envia 8. Não está
verificado se o runtime do Laya codifica cada pergunta separadamente com o
cartão ou se todas dividem os 512 tokens. O segundo caso contamina exatamente os
experimentos de paráfrase. O orçamento em `cards.py` também é uma estimativa
por palavras, não o tokenizer real. **Recomendação:** confirmar no código do
`laya`, e repetir um subconjunto do E10 com uma pergunta por chamada para
comparar.

---

## Pontos menores

### R11: A procedência do gabarito se contradiz {#r11}

O cabeçalho de `state/gold_judgements.yml` diz *"written… BEFORE any Laya call
was made"*. O `docs/methodology.md` diz que 89 dos 99 foram escritos depois de um
run existir. Um dos dois precisa ser corrigido.

### R12: O teste pré-registrado do E11 não teve resultado reportado {#r12}

O `config/questions_business.yml` registra uma hipótese sobre rótulos nus (p4)
contra a redação que ecoa o cartão (p1). O resultado saiu (p1 52%, p4 41%), mas
o `experiments.md` não diz o que isso implica para a hipótese de eco lexical.

### R13: "6% de erro de 2 bandas" aparece sem baseline {#r13}

Um preditor constante `medium` tem 0% de erro de duas bandas, e `loc_code` tem
1%. A métrica só informa algo junto com a acurácia e com esses baselines (R02).

---

## Validade de construto e externa

### R14: O que o estudo não pode responder {#r14}

**Estado: aceito.** Os pontos já estão documentados em `docs/limitations.md` e
são registrados aqui para acompanhamento.

- **Construto:** a rubrica mede tamanho e estrutura, não esforço de migração, e
  a pergunta não informa dialeto de origem nem de destino.
- **Corpus:** TPC-DS é SQL analítico portável por construção. O legado que
  motiva a triagem (PL/SQL, T-SQL procedural, SQL dinâmico) está ausente.
- **Gabarito:** um único anotador, que é um LLM, sem kappa. Isso invalida
  conclusões sobre `needs_human_review` e `rewrite_strategy` nos dois sentidos.
- **`derive-labels`:** "8 de 9 saem `refactor`" valida o detector de diff, não o
  significado do rótulo. Isso exige concordância com o líder da migração.

---

## Próximos passos, por custo-benefício

| # | ação | fecha | custo |
|---|---|---|---|
| 1 | Baseline de LLM lendo SQL bruto (Haiku, Sonnet e um modelo aberto local) nas 6 perguntas | R04 | baixo |
| 2 | Cartão cego: retirar do cartão o fato perguntado em cada pergunta | R01, circularidade | baixo |
| 3 | Commitar `business.py`, `paired.py` e o script de custo, com split por família e teste corrigido; republicar a tabela de veredito contra a LR leaky e as regras triviais | R01, R02, R03, R05, R06, R13 | baixo |
| 4 | Calibrar as probabilidades e reavaliar a árvore de decisão | R08 | baixo |
| 5 | Gabarito humano: 2 a 3 engenheiros em ~30 scripts, com kappa entre eles e contra o Claude | R14, R09 | médio |
| 6 | Corpus procedural com dialeto de destino explícito | R14 | médio |
| 7 | Fine-tune com a regra trivial e o LLM few-shot como braços obrigatórios no critério de aceite | R04, R09 | alto |

---

## Reprodução dos números desta revisão {#reproducao}

Rode na raiz do repositório com o `.venv` do projeto:

```python
import glob, yaml

docs = [yaml.safe_load(open(p, encoding="utf-8")) for p in glob.glob("state/script_*.yml")]
B = {"low": 0, "medium": 1, "high": 2}

def auc(pos, neg):
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))

for f in ("loc_code", "max_nesting_depth", "subquery_count"):
    lo = [d["features"][f] for d in docs if d["gold"]["migration_complexity"] == "low"]
    hi = [d["features"][f] for d in docs if d["gold"]["migration_complexity"] == "high"]
    print(f, "AUC low-vs-high", round(auc(hi, lo), 3))

# 3 bandas por loc_code, cortes nos quantis do gabarito (mesmo critério do E11)
items = sorted(docs, key=lambda d: d["features"]["loc_code"])
n = {b: sum(d["gold"]["migration_complexity"] == b for d in docs) for b in B}
pred = [0] * n["low"] + [1] * n["medium"] + [2] * n["high"]
gold = [B[d["gold"]["migration_complexity"]] for d in items]
print("loc 3 bandas", sum(p == g for p, g in zip(pred, gold)) / len(docs),
      "erro 2 bandas", sum(abs(p - g) == 2 for p, g in zip(pred, gold)) / len(docs))

for feat, q, rule in (("subquery_count", "has_subquery", lambda v: v > 0),
                      ("window_function_count", "has_window_function", lambda v: v > 0),
                      ("source_tables", "multi_source", lambda v: v >= 4)):
    print(q, sum(rule(d["features"][feat]) == d["gold"][q] for d in docs), "/", len(docs))
```

Saída obtida em 2026-09-23 23:48:

```
loc_code AUC low-vs-high 0.979
max_nesting_depth AUC low-vs-high 0.893
subquery_count AUC low-vs-high 0.832
loc 3 bandas 0.707 erro 2 bandas 0.01
has_subquery 99 / 99
has_window_function 99 / 99
multi_source 99 / 99
```
