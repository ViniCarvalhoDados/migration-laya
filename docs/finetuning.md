# Fine-tune do Laya com dados de um cliente

Como sair de "o zero-shot não classifica estratégia de reescrita" para um
classificador que serve para o padrão de código de **um** cliente.

O gargalo não é compute nem código. É de onde vêm os rótulos.

---

## 1. A ideia central: o rótulo já existe, no diff

Todo rótulo do discovery foi opinião minha — e por isso uma regressão logística
conseguiu reproduzi-lo a partir das mesmas features do AST de que ele
implicitamente derivava. Um fine-tune treinado nesse gabarito aprenderia a minha
opinião: uma forma cara de reimplementar o extrator.

**Uma migração já concluída não tem esse problema.** O cliente decidiu, script a
script, o quanto cada um precisou mudar, e a decisão está registrada no diff
entre o arquivo legado e o migrado. Comparar os dois ASTs recupera o rótulo do
que *foi de fato feito*.

```bash
mlaya derive-labels --legacy repo_legado/sql --migrated repo_novo/sql
```

Regras (em `src/migration_laya/labels.py`, deliberadamente grosseiras e
auditáveis — um líder de migração precisa conseguir discordar de um caso):

| condição no diff dos ASTs | rótulo |
|---|---|
| mesmas tabelas, mesma forma; só dialeto/cosmético mudou | `lift_and_shift` |
| mesmas tabelas, forma mudou (1–3 contadores estruturais) | `refactor` |
| mesmas tabelas, forma mudou muito (≥4 contadores) | `redesign` |
| passou a ler ou deixou de ler tabelas | `redesign` |
| trocou a maioria das fontes | `manual_rewrite` |
| um dos lados não parseia | `manual_rewrite`, confiança baixa → revisão humana |

Validado num par antes/depois real (`modified/` do repo TPC-DS): 8 de 9 saem
`refactor` porque a versão migrada envolve a query original numa derived table,
e o detector aponta exatamente `derived_table_count: 0 → 1`.

**E a complexidade?** Não venha do diff — venha do esforço real: horas
apontadas, story points, número de commits naquele arquivo, ciclos de review no
PR. É o único jeito de o rótulo não ser função das features de entrada. Se o
cliente não mediu esforço, essa pergunta não tem gabarito honesto e é melhor
deixá-la de fora do treino.

---

## 2. Quantos exemplos

Referência do próprio notebook do Laya: **1.200 casos → 6.000 decisões**, com
400 itens separados só para calibrar temperaturas no fim.

```bash
mlaya export-training --out-dir training
```

O comando imprime o que você precisa checar antes de gastar GPU:

```
casos por split : {'train': 69, 'calibration': 10, 'test': 20}
decisoes totais : 594  (referencia do notebook: 6000)
rewrite_strategy {'lift_and_shift': 35, 'refactor': 54, 'redesign': 10}   CLASSES MAGRAS: ['redesign']
```

Dois alertas que o corpus TPC-DS já dispara e um cliente vai disparar também:

- **Escala.** 594 decisões contra 6.000 de referência. Um backlog de 300 scripts
  migrados × 6 perguntas dá ~1.800 — fino, mas não absurdo. Abaixo de ~150
  scripts eu não começaria.
- **Classes magras.** `redesign` com 10 exemplos não se aprende, e o modelo
  nunca vai prevê-la. Ou você junta classes (`redesign` + `manual_rewrite` viram
  "reescrever"), ou aceita um classificador de 3 classes.

---

## 3. A armadilha do split, que este corpus me ensinou

O TPC-DS tem queries quase idênticas — q33, q56 e q60 diferem só numa coluna de
agrupamento. Um split aleatório coloca uma no treino e a gêmea no teste, e a
acurácia reportada é em parte memorização.

**Backlogs de cliente são piores**: o mesmo relatório copiado por região, por
ano, por unidade de negócio.

`export-training` agrupa scripts por uma impressão digital estrutural e manda
**famílias inteiras** para um lado só do split. O relatório traz
`family_overlap`, que precisa sair vazio:

```
familias        : {'train': 52, 'calibration': 10, 'test': 20}
vazamento entre splits: nenhum (split por familia)
```

Nas 99 queries, 82 famílias — ou seja, 17 scripts são quase-duplicatas de
algum outro. Num split aleatório isso teria inflado o resultado.

---

## 4. Treinar

O pacote `pip install laya` é **só inferência**. O treino vive no notebook do
repositório:

```
notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb
```

O que ele faz, do que importa saber:

- Arquitetura: encoder ModernBERT-large (421M) + cabeças por tipo de pergunta,
  com gradient checkpointing para caber em T4.
- Perda: policy gradient tipo GRPO com *proper scoring rule* + cross-entropy
  como guia. Não é classificação supervisionada comum.
- Hiperparâmetros: 4 épocas, LR 2,5e-5 no encoder e 1e-4 nas cabeças, batch
  efetivo 64, ruído de exploração 0,4 → 0,1, `max_len` 1.024.
- **Calibra temperaturas no fim, sobre o hold-out.** É esse passo que faz a
  confiança significar alguma coisa — pular reproduz no seu modelo o aviso que o
  checkpoint de fábrica emite sobre confianças não calibradas.

Infra: 2× T4 via `torchrun --nproc_per_node=2`. Cabe no tier gratuito do Kaggle.
Na escala do notebook o treino leva minutos, não horas.

Você só precisa apontar o carregador de dados para os seus `train.jsonl` /
`calibration.jsonl` — o formato de três colunas (`state`, `questions`, `gold`) é
exatamente o que `export-training` emite.

---

## 5. Validar — sem repetir os erros deste estudo

Isto não é opcional. Todo número abaixo eu já reportei errado uma vez.

| verificação | por quê | comando |
|---|---|---|
| **Baseline de classe majoritária** | Acurácia sem ele engana. Eu comparei binárias contra "50% de acaso" quando o acaso real era 74%. | no `mlaya report` |
| **Regressão logística nas mesmas features** | Se ela empata com o modelo afinado, você não aprendeu nada além do extrator. | `mlaya baseline` |
| **AUC, não só acurácia** | Um modelo pode ordenar bem e cortar errado. Eu concluí "sem informação" de um AUC 0,99. | no `mlaya report` |
| **Limiar em hold-out** | Corte ajustado no próprio dado é teto otimista, não configuração. | no `mlaya report` |
| **Robustez à paráfrase** | Reescrever uma pergunta moveu o AUC em 0,57. | `mlaya variants` |
| **Teste de negação** | Se a resposta não inverte quando a pergunta inverte, o modelo não está lendo. | `mlaya variants` |
| **Erro de duas bandas** | Em complexidade, errar adjacente é ruído; errar `high` → `low` estraga planejamento. | no `mlaya report` |

Critério de aceite que eu proporia ao cliente, antes de treinar:

> O modelo afinado precisa bater a regressão logística sobre as mesmas features
> do AST, em hold-out por família, com IC90 que não cruze zero — e manter isso
> sob pelo menos duas formulações diferentes da pergunta.

Se não bater, o entregável é a regressão logística: ela é mais barata, roda em
milissegundos e é explicável coeficiente a coeficiente.

---

## 6. Ordem de execução

1. Pegar um repositório de migração **concluída** do cliente: pasta legada e
   pasta migrada, nomes de arquivo correspondentes.
2. `mlaya derive-labels` → revisar com o líder da migração os casos de confiança
   baixa e uma amostra dos de confiança alta. **Esse review é o produto**: é o
   único momento em que o conhecimento do cliente entra no gabarito.
3. Buscar o esforço real (horas, pontos, commits) para rotular complexidade. Sem
   isso, treinar só `rewrite_strategy`.
4. `mlaya census` + `mlaya sample --n <tudo>` + `mlaya card` no corpus do cliente.
5. `mlaya export-training` → conferir escala, classes magras e `family_overlap`.
6. Rodar o notebook apontando para os seus JSONL.
7. `mlaya ask` com o checkpoint novo → `mlaya baseline` → `mlaya variants`.
8. Decidir com a tabela da seção 5 na mesa.

---

## 7. O que pode dar errado

- **A migração passada foi inconsistente.** Duas pessoas classificaram o mesmo
  padrão de formas diferentes. O review do passo 2 é onde isso aparece — e se
  aparecer muito, o rótulo não é aprendível.
- **Ruído do derivador.** As regras são grosseiras de propósito. Se o cliente
  reformatou tudo com um linter na migração, diferenças cosméticas viram ruído.
  Normalize antes de comparar.
- **Poucos scripts.** Abaixo de ~150, o fine-tune vai overfittar e o hold-out
  por família vai ficar pequeno demais para medir qualquer coisa.
- **O cliente quer aplicar em outro cliente.** Não dá — o modelo aprendeu o
  padrão de código *daquela* casa. Isso é uma feature, não um bug, mas precisa
  estar claro na proposta comercial.
