# Metodologia

Como o experimento foi montado e por que cada decisão. Os resultados estão em
[`experiments.md`](experiments.md); o que o estudo não decide, em
[`limitations.md`](limitations.md).

---

## O que o Laya é, e a restrição que define tudo

[Laya](https://github.com/NandhaKishorM/laya) não gera texto: responde perguntas
tipadas (`choice`, `score`, `noul`) devolvendo probabilidades. Isso o torna
atraente para triagem.

**Mas o checkpoint inglês tem 512 tokens de contexto por passagem.** Um script
de 300 linhas não cabe. Então o modelo nunca vê o SQL — vê um *evidence card* de
~100 tokens comprimido do AST.

Essa compressão é o artefato central do estudo, e também o seu problema: ver
[circularidade](limitations.md#circularidade).

---

## O pipeline

```
[0] censo — sqlglot nas 99 queries ──► distribuição do corpus
      │   percentis ──► limiares da rubrica ──► complexidade GOLD
      │   └─► amostragem estratificada ──► n scripts
      ▼
[1] extrator determinístico ──► features + grafo de joins  (verdade sintática)
[2] Claude ──► propósito de negócio + gabarito de julgamento
      │
      └──► evidence card (~100 tokens)  ◄── único input do Laya
                  │
[3] Laya ──► choice/score/noul + probabilidades
                  │
[4] árvore de decisão ──► AUTO / HUMAN_REVIEW / ESCALATE
                  │
[5] relatório ──► acurácia · AUC · ECE · Brier · cobertura×acurácia · latência
```

---

## Decisões de projeto

### Cascata de dialetos

99/99 parseiam com `spark → tsql`. O corpus é misto: query67 usa `SELECT TOP`
(T-SQL). **Qual dialeto foi necessário é registrado como marcador de
não-portabilidade** — é informação de migração, não ruído.

### Grafo de joins em dois níveis

*Footprint* (tabelas base, global) e *complexidade estrutural* (por escopo,
incluindo CTEs e derived tables) medem coisas diferentes e não podem ser
somadas.

Ler `connected_components` global como "risco de produto cartesiano" é errado:
escopos separados **devem** ser desconexos. Risco cartesiano é avaliado por
escopo — e só quando **todos** os predicados daquele escopo foram resolvidos.
Se algo ficou por resolver, um nó órfão pode simplesmente estar ligado por um
predicado que o resolvedor não entendeu, e afirmar cross join ali seria um
chute que este extrator não dá em nenhum outro lugar.

### Resolução de colunas sem schema

TPC-DS deixa colunas de join sem qualificação e usa convenção de abreviatura
(`ss_item_sk` → `store_sales`). A convenção é inferida genericamente dos nomes
em escopo — iniciais, iniciais sem sufixo de dimensão, truncamento (`inv_` →
`inventory`) — com desempate pelo restante do nome (`i_item_sk` → `item`, não
`inventory`).

Cobertura: **92,1%**. Os 7,9% restantes são ambiguidade real (`ws_` serve a
`web_sales` e `web_site`) e são **contados, nunca chutados**.

### Limiares vindos de percentis

`mlaya census --emit-rubric` deriva cada limiar de um percentil observado e
registra qual. "Por que 40 linhas?" vira "por que o percentil 66?" — uma
pergunta que o time consegue responder.

### Bandas pelo split mais equilibrado

Tercis puros quebram numa distribuição discreta com pico: um terço do corpus
empilhado em 5–6 pontos colapsaria a banda `medium` num único valor, e um ponto
de diferença decidiria o gabarito. O corte escolhido é o mais próximo de terços
iguais com `medium` cobrindo ≥2 valores.

### Perguntas que o AST já responde

`has_subquery`, `has_window_function` e `multi_source` são 100% verificáveis.
Isso dá gabarito objetivo para as 99 sem trabalho manual, e transforma um erro
confiante nelas no sinal negativo mais forte possível.

**Também é a origem da circularidade** — a decisão foi tomada sabendo do
trade-off, mas seu custo só ficou visível depois da auditoria.

### Identidade pela query de origem

O id sequencial é atribuído pelo amostrador e é reaproveitado para outra query
quando o tamanho da amostra muda. Por isso `gold_judgements.yml` é chaveado por
`query42`, e os JSONs de resposta guardam a origem — sem isso, re-pontuar um run
antigo o casa em silêncio com o gabarito errado.

### Dois comparadores, sempre os dois

A regressão logística é ajustada em duas versões, e as duas aparecem em toda
tabela:

- **limpa** — sem as features de que o rótulo é definido. Responde "dá para
  fazer isso com aritmética *sem* receber a resposta?".
- **mesma informação** — com elas. É o que o evidence card entrega ao Laya, que
  imprime `subqueries=0` e `window_fns=2` literalmente.

Reportar só a limpa foi o erro que [E13](experiments.md#e13) corrigiu: mede o
handicap dado ao comparador, não a capacidade do modelo. Reportar só a vazada
esconderia que parte do problema é a pergunta ser trivial. As duas juntas
delimitam o resultado por cima e por baixo.

### Tudo ajustado só no treino, sempre

No protocolo pareado (`mlaya paired`, `mlaya business`) cada braço tem exatamente
uma coisa ajustada, e sempre na metade de treino: o **limiar** do Laya, os
**coeficientes** da regressão, os **cortes** das bandas de complexidade, a
**classe** do baseline majoritário. A metade de teste nunca é vista por nenhum
deles.

Sem p-valor, de propósito: as metades de teste se sobrepõem entre splits, então
um teste pareado sobre elas seria anticonservador. A dispersão p05–p95 e a taxa
de vitórias são os resumos honestos.

### Latência vem do raw do próprio run

`mlaya ask` grava `measured_ms` no YAML do script, que por isso guarda sempre o
**último** run que passou por ali. O relatório lia de lá e mostrava o tempo de
outro experimento. A estimativa continua vindo do YAML — é função determinística
do tamanho do cartão —, mas a medição vem do JSON bruto daquele run.

### Cobertura por script, não só por resposta

As duas curvas estão no relatório porque a diferença entre elas é a conclusão:
um script só é triado sem humano quando **todas** as perguntas sobre ele passam
do corte, e a conjunção é muito mais dura que cada resposta isolada.

---

## A árvore de decisão

A distinção que importa não é certo-vs-errado, e sim *confiantemente errado
sobre algo que o AST já sabia*. Um classificador meramente errado é gerenciável;
um que erra e tem certeza, não.

| condição | saída |
|---|---|
| fato verificável errado com confiança ≥0,85, **ou** complexidade a 2 bandas | `ESCALATE` |
| 3 fatos certos e todos ≥0,85 | `AUTO` |
| resto | `HUMAN_REVIEW` |

Com o cartão ela nunca disparou `ESCALATE` em 99 scripts; com SQL bruto,
disparou em 80.

---

## Métricas, e por que cada uma entrou

Todas entraram porque a ausência dela produziu uma conclusão errada em algum
momento.

| métrica | o que corrige |
|---|---|
| **Baseline de classe majoritária** | Acurácia sozinha engana com classes desbalanceadas. Binária não tem acaso em 50%. |
| **AUC** | Um modelo pode ordenar bem e cortar errado. AUC <0,5 é sinal invertido, não ausência de sinal. |
| **McNemar** | Sem ele, ±2% vira "achado". |
| **IC de Wilson** | "7 scripts, 1 erro" é 86% — e o intervalo é 49–97%. |
| **Hold-out do limiar** | Corte ajustado no próprio dado é teto otimista. |
| **Duas variantes do baseline** | A regressão sem as features que definem o rótulo é fraca por construção; comparar só contra ela inflou a única vitória do estudo. |
| **Sensibilidade à paráfrase** | Reescrever uma pergunta moveu o AUC em 0,57. |
| **Teste de negação** | Se a resposta não inverte quando a pergunta inverte, o modelo não está lendo. |
| **Erro de duas bandas** | Em complexidade, errar adjacente é ruído; `high` → `low` estraga planejamento. |

---

## Procedência do gabarito

| pergunta | origem | cobertura |
|---|---|---|
| `has_subquery`, `has_window_function`, `multi_source` | AST (`sqlglot`) | 99, objetivo |
| `migration_complexity` | rubrica sobre features do AST | 99, objetivo — e **reproduzível de graça pela própria rubrica** |
| `rewrite_strategy`, `needs_human_review` | julgamento de Claude lendo cada SQL | 99, **um anotador só** |

Os **10 primeiros** julgamentos foram escritos antes de o Laya rodar; os **89
restantes**, depois de um run existir em disco (sem consultá-lo). Blindagem
procedimental, não estrutural — está registrado no cabeçalho de
`state/gold_judgements.yml`.

`manual_rewrite` tem **zero instâncias** nas 99: essa classe nunca pode ser
avaliada.
