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

## Ainda em aberto

| pergunta | por quê | custo |
|---|---|---|
| **O gabarito pode ser independente do input?** | Enquanto não for, nenhum resultado positivo é conclusivo. Precisa de esforço real medido, anotadores humanos, kappa. | alto — exige gente |
| **TPC-DS representa legado real?** | Não. Precisa de PL/SQL procedural e dialeto de destino explícito. | médio — exige corpus |
| **Quanto do resultado é viés de formulação?** | [E9](experiments.md#e9) mediu 0,28 de AUC médio. [E10](experiments.md#e10) mostrou que agregar resolve nas binárias — mas não nas ordinais. | baixo — feito parcialmente |
| **Um encoder de código mudaria o quadro?** | [E5](experiments.md#e5) sugere que sim: o fracasso com SQL bruto foi de distribuição, não de capacidade. Mas já é outro produto. | fora de escopo |
| **Fine-tune com dados de cliente funciona?** | O único teste que decide o caso de `rewrite_strategy`, porque é o único em que o gabarito não é a minha opinião. | ver [`finetuning.md`](finetuning.md) |

---

## Ressalvas menores, mas registradas

- **`has_window_function` tem só 15 positivos** em 99. Toda métrica dela tem
  intervalo largo.
- **Comparar 4 redações e apontar a melhor já é seleção.** Em
  [E11](experiments.md#e11) o intervalo defensável para complexidade é 38–52%,
  não os 52% da melhor.
- **O "melhor limiar" sem hold-out é teto otimista**, e está marcado como tal em
  todo lugar onde aparece.
- **Ensemble de paráfrases custa 3,5×** em tempo de CPU.
- **CPU, não GPU** — latências ~20× as do benchmark em T4 do README do Laya.
- **Licença** — queries derivadas da spec TPC-DS; procedência em
  `repos/legacy/scripts/NOTICE.md`. As cópias em `repos/legacy/scripts/*.sql`
  não são versionadas: são saída de `mlaya sample` e se regeneram com um
  comando, o que limita a redistribuição sem custar reprodutibilidade.
