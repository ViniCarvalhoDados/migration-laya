# Limitações e pontos em aberto

O que este estudo **não** decide, e o que faria decidir.

---

## O defeito de desenho {#circularidade}

**O cartão entrega a resposta.** Ele lista os fatos perguntados — literalmente
`subqueries=0`, "No CTE, subquery…" — e o gabarito de complexidade é uma função
determinística dos mesmos números.

Quatro das seis perguntas viram, portanto, um teste de leitura. A medida disso
está em [E6](experiments.md#e6): uma regressão logística com acesso à feature
que define o rótulo acerta **97–100%**.

**Consequência.** As conclusões **negativas** deste estudo valem para este
cartão e este prompt. As conclusões **positivas** sobre automação não se
sustentam.

Isso está dito aqui e no topo do README de propósito, não enterrado no rodapé.

### O corolário que demorei a tirar

Se o cartão entrega os fatos, então a regressão que **não** os recebe é um
comparador fraco por construção. E8 e E10 mediram o Laya contra ela e chamaram a
diferença de vitória. Contra a regressão com a **mesma informação que o cartão**,
o Laya empata em `has_subquery` e perde nas outras duas
([E13](experiments.md#e13)).

A mesma coisa vale para complexidade: o gabarito é a rubrica, e a rubrica é uma
função determinística das features que o extrator já calcula. Ela acerta 100% em
milissegundos. Qualquer número abaixo disso — inclusive os 54% do Laya — é uma
cópia pior de algo que já existe de graça.

---

## A rubrica não mede dificuldade de migração

A rubrica de complexidade tem **ρ = 0,82 com contagem de linhas**. Ela mede
tamanho e estrutura, não esforço.

Agravantes:

- O TPC-DS foi escrito para rodar em qualquer engine.
- A pergunta não informa dialeto de origem nem de destino.
- A opção "trivial – only dialect syntax needs changing" não corresponde ao que
  a banda `low` de fato mede.

**Como resolver.** O rótulo de complexidade tem que vir do esforço real —
horas apontadas, story points, commits no arquivo, ciclos de review. Ver
[`finetuning.md`](finetuning.md).

---

## O modelo reage ao que está escrito no cartão

O score esperado de complexidade correlaciona **mais** com `max_nesting_depth`
(0,67) e `subquery_count` (0,66) do que com os pontos da rubrica (0,59) — e
esses dois números estão impressos literalmente no cartão.

E `multi_source` **não faz a comparação numérica** que a pergunta pede
("≥4 fontes"): P(true) sobe até 4 fontes (0,92) e depois **cai** — 0,56 em 6,
0,32 em 13.

---

## O gabarito de julgamento tem um anotador só, que é um LLM

`rewrite_strategy` e `needs_human_review` são julgamentos de Claude lendo cada
SQL, **sem concordância humana medida**. E os 89 últimos foram escritos depois
de um run existir em disco (sem consultá-lo — mas isso é afirmação
procedimental, não garantia estrutural).

**Pior:** uma regressão logística reproduz esses julgamentos com AUC 0,94 a
partir de features do AST ([E6](experiments.md#e6)). Ou seja, eles são em grande
parte função das features — não do julgamento que deveriam trazer.

`manual_rewrite` tem **zero instâncias** nas 99: a classe nunca pode ser
avaliada, nem o modelo penalizado por evitá-la.

---

## Domínio único

TPC-DS é analytics em SQL ANSI. Não cobre PL/SQL procedural, cursores, SQL
dinâmico, nem pacotes. A pipeline aceita um segundo corpus sem alteração
estrutural, mas nada aqui fala sobre legado procedural.

---

## Pontos de revisão declarados, não corrigidos

A segunda auditoria levantou oito pontos que **não** mudam uma conclusão
publicada e que ficaram registrados em vez de corrigidos. Estão aqui para que
ninguém precise reencontrá-los:

| ponto | por que importa | por que não foi corrigido |
|---|---|---|
| **Near-duplicates atravessam os splits.** `finetuning.md` identifica 82 famílias em 99 scripts, mas o split por família só existe no `export-training`; os hold-outs de avaliação usam metades estratificadas aleatórias, então gêmeos como q33/q56/q60 caem em lados opostos. | Infla os braços **ajustados** (a LR e o limiar) mais que o Laya zero-shot — ou seja, favorece o comparador, não o modelo. A conclusão de [E13](experiments.md#e13) fica conservadora, não otimista. | mudaria os números sem mudar o sinal |
| **A dispersão entre splits sobrepostos é reportada como se fosse intervalo.** | Subestima a variância; o correto seria o *corrected resampled t-test* (Nadeau & Bengio, 2003) ou bootstrap por família. | rótulo corrigido em todo lugar; o teste, não |
| **Caminhos de análise demais para n = 99.** Treze experimentos, 4–6 redações por pergunta, limiar invertido, escolha de variante. | Inverter o limiar de `needs_human_review` porque o AUC saiu 0,22 é decisão tirada do dado; o ganho (74% contra 70%) está dentro do ruído e a pergunta falha no teste de negação. | exigiria um conjunto confirmatório separado |
| **O caso de custo não mede o acerto do LLM.** [E12](experiments.md#e12) compara preços, nunca qualidade: nenhum LLM foi rodado nas seis perguntas. | "10–100× mais barato" só vira argumento com a acurácia do outro lado na mesa. | é um experimento, não uma correção |
| **A árvore de decisão usa confiança não calibrada.** ECE 0,085, e o próprio README do Laya diz que o checkpoint sai *over-confident*. | Os cortes de 0,85 da árvore são sobre um número que não é probabilidade. | ver [`finetuning.md`](finetuning.md) |
| **`rewrite_strategy` foi avaliada só por argmax.** Nunca recebeu cortes ajustados nem ensemble, ao contrário das binárias. | A afirmação "ausência de capacidade zero-shot" é mais forte do que o teste sustenta. | e zero-shot não é o teste certo para ela de todo modo |
| **Não foi verificado se várias perguntas na mesma chamada interferem entre si.** Seis a 24 perguntas vão juntas, num contexto de 512 tokens. | Truncamento silencioso explicaria parte dos resultados ruins sem envolver capacidade. | ablação simples, ainda não feita |
| **A procedência do gabarito se contradiz entre arquivos.** | `methodology.md` e o cabeçalho de `state/gold_judgements.yml` não dizem exatamente a mesma coisa sobre quando os 89 últimos foram escritos. | conferir e unificar |

---

## Ainda em aberto

| pergunta | por quê | custo |
|---|---|---|
| **O gabarito pode ser independente do input?** | Enquanto não for, nenhum resultado positivo é conclusivo. Precisa de esforço real medido, anotadores humanos, kappa. | alto — exige gente |
| **TPC-DS representa legado real?** | Não. Precisa de PL/SQL procedural e dialeto de destino explícito. | médio — exige corpus |
| **Quanto do resultado é viés de formulação?** | [E9](experiments.md#e9) mediu 0,28 de AUC médio. [E10](experiments.md#e10) mostrou que agregar resolve nas binárias — mas não nas ordinais. | baixo — feito parcialmente |
| **O Laya bate a aritmética quando os dois veem a mesma coisa?** | [E13](experiments.md#e13) diz que não nas quatro perguntas medidas. O que falta é uma pergunta em que a aritmética **não** possa competir — e nesta rubrica não existe. | médio — exige outro gabarito |
| **Um encoder de código mudaria o quadro?** | [E5](experiments.md#e5) sugere que sim: o fracasso com SQL bruto foi de distribuição, não de capacidade. Mas já é outro produto. | fora de escopo |
| **Fine-tune com dados de cliente funciona?** | O único teste que decide o caso de `rewrite_strategy`, porque é o único em que o gabarito não é a minha opinião. | ver [`finetuning.md`](finetuning.md) |

---

## Ressalvas menores, mas registradas

- **`has_window_function` tem só 15 positivos** em 99. Toda métrica dela tem
  intervalo largo.
- **Comparar 4 redações e apontar a melhor já é seleção.** Em
  [E11](experiments.md#e11) o intervalo defensável para complexidade é 40–54%,
  não os 54% da melhor.
- **Redações escritas depois de ver os erros.** A formulação de `has_subquery`
  foi ajustada depois que a auditoria mostrou onde o modelo errava (AUC 0,84 →
  0,95), e as seis paráfrases de [E10](experiments.md#e10) foram escritas depois
  de [E9](experiments.md#e9). A motivação é legítima — a pergunta era
  genuinamente ambígua para um `WITH` — mas isso é **margem de manobra do
  pesquisador**, e o resultado não é o mesmo que teria saído de um conjunto de
  redações registrado antes de rodar. O teste limpo seria um corpus separado, ou
  redações escritas às cegas.
- **`derive-labels` foi validado em um par só.** Um antes/depois, 8 de 9
  rótulos corretos. É suficiente para mostrar que o mecanismo funciona, e
  insuficiente para afirmar que a derivação é confiável.
- **O "melhor limiar" sem hold-out é teto otimista**, e está marcado como tal em
  todo lugar onde aparece.
- **Ensemble de paráfrases custa 3,5×** em tempo de CPU.
- **CPU, não GPU** — latências ~20× as do benchmark em T4 do README do Laya.
- **Licença** — queries derivadas da spec TPC-DS; procedência em
  `repos/legacy/scripts/NOTICE.md`. As cópias em `repos/legacy/scripts/*.sql`
  não são versionadas: são saída de `mlaya sample` e se regeneram com um
  comando, o que limita a redistribuição sem custar reprodutibilidade.
