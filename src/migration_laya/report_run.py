"""The study report: what Laya actually did, and whether it can be trusted."""

from __future__ import annotations

from pathlib import Path

from . import metrics
from .decide import AUTO, HUMAN_REVIEW, ESCALATE, VERIFIABLE

BANDS = ("low", "medium", "high")
STRATEGIES = ("lift_and_shift", "refactor", "redesign", "manual_rewrite")


def render(run: dict, decisions: list[dict], docs: dict, sample: dict,
           raw: dict | None = None, baseline: dict | None = None) -> str:
    out: list[str] = []
    a = out.append
    n = len(decisions)

    a(f"# Resultado — run `{run.get('run_id')}`\n")
    source = run.get("source", "card")
    described = {
        "card": "evidence card (~100 tokens derivados do AST)",
        "sql": "**SQL bruto**, partido em janelas do tamanho do contexto",
    }.get(source, source)
    a(f"{n} scripts · {run.get('n_questions')} perguntas · "
      f"modelo `{run.get('model')}` em `{run.get('device')}`\n")
    a(f"**Input:** {described}.\n")
    if source == "sql":
        a("> As regras de agregação entre janelas estão pré-registradas em\n"
          "> `chunks.AGGREGATION`, escritas antes de qualquer resultado. "
          "`multi_source`\n> pede uma contagem global de tabelas e é "
          "**estruturalmente irrespondível por\n> janela** — fica no run para "
          "que o custo do fatiamento apareça nos números.\n")

    # ---- 0. the runtime's own warning -----------------------------------
    warnings = run.get("runtime_warnings") or []
    if warnings:
        a("> **Aviso emitido pelo próprio runtime ao carregar o checkpoint:**\n>")
        for w in warnings:
            a(f"> `{w}`\n>")
        a("> Ou seja, os percentuais de confiança abaixo são declaradamente não\n"
          "> calibrados pelo fornecedor. Isso não invalida as respostas — invalida\n"
          "> lê-las pelo valor de face. É exatamente o que a seção de calibração mede.\n")

    # ---- 1. headline ----------------------------------------------------
    counts = metrics.outcome_counts(decisions)
    a("## 1. Manchete\n")
    a("| desfecho | scripts | % | significado |")
    a("|---|---|---|---|")
    for outcome, meaning in (
        (AUTO, "classificado sem humano"),
        (HUMAN_REVIEW, "humano confere — erro pequeno ou baixa confiança"),
        (ESCALATE, "**erro confiante** em fato verificável pelo AST"),
    ):
        c = counts.get(outcome, 0)
        a(f"| `{outcome}` | {c} | {100 * c / n:.0f}% | {meaning} |")

    auto = counts.get(AUTO, 0)
    escalate = counts.get(ESCALATE, 0)
    a(f"\n**{auto} de {n} scripts ({100 * auto / n:.0f}%) passariam sem revisão humana.**")
    if escalate:
        a(f"\n**{escalate} script(s) erraram com alta confiança um fato que o AST "
          f"já conhecia** — o modo de falha que quebra confiança em produção.")

    # ---- 2. sample coverage ---------------------------------------------
    coverage = (sample or {}).get("coverage") or {}
    if coverage:
        a("\n## 2. Representatividade da amostra\n")
        a(f"- {coverage.get('n_sampled')} de {coverage.get('n_corpus')} scripts do corpus.")
        a(f"- Bandas: {coverage.get('bands')}")
        a(f"- Pontos de rubrica cobertos: {coverage.get('rubric_points_range')} "
          f"de {coverage.get('corpus_points_range')} do corpus.")
        a("\n| script | origem | banda gold | pontos | percentil loc | percentil fontes |")
        a("|---|---|---|---|---|---|")
        for entry in (sample or {}).get("scripts", []):
            p = entry.get("corpus_percentile", {})
            a(f"| `{entry['id']}` | {entry['origin']} | {entry['rubric_band']} | "
              f"{entry['rubric_points']} | p{p.get('loc_code', 0)} | "
              f"p{p.get('source_tables', 0)} |")

    # ---- 3. per script ---------------------------------------------------
    a("\n## 3. Script a script\n")
    a("Confiança = maior massa de probabilidade. ✓ acerto · ✗ erro.\n")
    keys = _question_order(decisions)
    a("| script | desfecho | " + " | ".join(f"`{k}`" for k in keys) + " |")
    a("|---" * (len(keys) + 2) + "|")
    for d in decisions:
        by_key = {q["question"]: q for q in d["questions"]}
        cells = []
        for k in keys:
            q = by_key.get(k)
            if not q:
                cells.append("—")
                continue
            mark = "✓" if q["agree"] else "✗"
            cells.append(f"{mark} {_short(q['predicted'])} · {q['confidence']:.0%}")
        a(f"| `{d['script_id']}` | {_badge(d['outcome'])} | " + " | ".join(cells) + " |")

    a("\n**Gabarito, para conferência:**\n")
    a("| script | complexidade | estratégia | subquery | window | multi-fonte | revisão |")
    a("|---|---|---|---|---|---|---|")
    for d in decisions:
        g = (docs.get(d["script_id"], {}).get("gold") or {})
        a(f"| `{d['script_id']}` | {g.get('migration_complexity')} "
          f"({g.get('rubric_points')}pts) | {g.get('rewrite_strategy')} | "
          f"{g.get('has_subquery')} | {g.get('has_window_function')} | "
          f"{g.get('multi_source')} | {g.get('needs_human_review')} |")

    # ---- 4. per question -------------------------------------------------
    a("\n## 4. Acurácia por pergunta\n")
    summary = metrics.per_question(decisions)
    a("| pergunta | AST | acertos | acurácia | baseline | ganho | respostas distintas | conf. média | excesso |")
    a("|---|---|---|---|---|---|---|---|---|")
    for key in keys:
        s = summary.get(key)
        if not s:
            continue
        lift = s["lift_over_baseline"]
        lift_text = f"**{lift:+.0%}**" if lift <= 0 else f"{lift:+.0%}"
        a(f"| `{key}` | {'sim' if s['verifiable'] else 'não'} | "
          f"{s['correct']}/{s['n']} | {s['accuracy']:.0%} | "
          f"{s['majority_baseline']:.0%} | {lift_text} | "
          f"{s['distinct_predictions']} | "
          f"{s['mean_confidence']:.0%} | {s['overconfidence']:+.0%} |")
    a("\n> **baseline** = acurácia de sempre responder a classe majoritária do\n"
      "> gabarito. **ganho** = acurácia menos baseline; zero ou negativo significa\n"
      "> que a pergunta não carrega informação. **respostas distintas** = quantos\n"
      "> rótulos diferentes o modelo chegou a emitir; `1` é um preditor constante.\n")
    a("\n> _Excesso de confiança_ = confiança média menos acurácia. Positivo\n"
      "> significa que o modelo se diz mais certo do que de fato é.\n")

    verifiable_outcomes = [
        q for d in decisions for q in d["questions"] if q["question"] in VERIFIABLE
    ]
    hits, total, acc = metrics.accuracy(verifiable_outcomes)
    majority = sum(
        summary[k]["majority_baseline"] * summary[k]["n"]
        for k in VERIFIABLE if k in summary
    ) / max(1, sum(summary[k]["n"] for k in VERIFIABLE if k in summary))
    a(f"**Nas 3 perguntas que o AST responde sozinho: {hits}/{total} = {acc:.0%}, "
      f"contra um baseline de classe majoritária de {majority:.0%} — ganho de "
      f"{acc - majority:+.0%}.**\n")
    a("> Uma pergunta binária com classes desbalanceadas **não** tem acaso em 50%.\n"
      "> Comparar contra 50% infla o resultado; o número honesto é o ganho sobre\n"
      "> responder sempre a classe majoritária.\n")

    # ---- 4b. ranking quality --------------------------------------------
    a("## 4b. A acurácia esconde a qualidade do ranking\n")
    a("Acurácia responde *o limiar está certo?*. AUC responde *a ordenação está\n"
      "certa?*. As duas se separam aqui, e ler só a primeira leva à conclusão\n"
      "errada.\n")
    a("| pergunta | n | AUC | acc @0.5 | IC95 | baseline | McNemar p | "
      "melhor limiar | acc nele | leitura |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for key in VERIFIABLE + ("needs_human_review",):
        diag = metrics.binary_diagnostics(decisions, key)
        if not diag:
            continue
        lo, hi = diag["accuracy_ci95"]
        p_value = diag["mcnemar"]["p_value"]
        auc = diag["auc"]
        if auc is None:
            verdict = "—"
        elif auc < 0.35:
            verdict = "**sinal invertido**"
        elif auc >= 0.80 and p_value >= 0.05:
            verdict = "**ordena bem, limiar errado**"
        elif p_value < 0.05:
            verdict = "ganho real"
        else:
            verdict = "dentro do ruído"
        best = diag.get("best_threshold") or {}
        inv = " (inv.)" if best.get("inverted") else ""
        a(f"| `{key}` | {diag['n']} | **{auc:.2f}** | {diag['accuracy']:.0%} | "
          f"{lo:.0%}–{hi:.0%} | {diag['baseline']:.0%} | {p_value:.4f} | "
          f"{best.get('threshold', 0.5):.2f}{inv} | "
          f"**{best.get('accuracy', 0):.0%}** | {verdict} |")
    a("\n> **AUC** = probabilidade de um caso positivo receber score maior que um\n"
      "> negativo. 0.5 é o acaso. **Abaixo de 0.5 não é ausência de sinal — é\n"
      "> sinal apontando para o lado errado**, que um limiar invertido recuperaria.\n"
      "> **McNemar p** testa se a diferença para o baseline de classe majoritária\n"
      "> é maior que o acaso; p alto significa que o ganho (ou a perda) é ruído.\n")
    a("> ⚠️ **O melhor limiar foi ajustado nos mesmos 99 pontos em que é medido.**\n"
      "> É um teto otimista. A tabela seguinte é a versão implantável.\n")

    holdout_rows = []
    for key in VERIFIABLE + ("needs_human_review",):
        diag = metrics.binary_diagnostics(decisions, key)
        if diag.get("holdout"):
            holdout_rows.append((key, diag["holdout"]))
    if holdout_rows:
        a("\n**Limiar validado em hold-out** — divisões estratificadas repetidas, "
          "corte\nescolhido só na metade de treino e medido só na de teste:\n")
        a("| pergunta | acc @0,5 | acc hold-out | p05–p95 | limiar mediano | "
          "ganho sobre 0,5 | teto otimista | hindsight |")
        a("|---|---|---|---|---|---|---|---|")
        for key, h in holdout_rows:
            a(f"| `{key}` | {h['accuracy_at_half']:.0%} | "
              f"**{h['test_accuracy_mean']:.0%}** | "
              f"{h['test_accuracy_p05']:.0%}–{h['test_accuracy_p95']:.0%} | "
              f"{h['threshold_median']:.2f} | {h['gain_over_default']:+.0%} | "
              f"{h['optimistic_accuracy']:.0%} | {h['hindsight_gap']:+.0%} |")
        a("\n> **hindsight** = quanto do ganho aparente era escolha com o gabarito\n"
          "> na mão. Poucos pontos significa que a calibração sobrevive ao\n"
          "> hold-out; muitos significariam que o limiar ótimo era sorte.\n")
    a("> Todos os limiares ótimos caem **abaixo de 0.5**: o modelo subestima\n"
      "> P(true) de forma sistemática — é o aviso de temperatura inválida do\n"
      "> checkpoint aparecendo em números.\n")

    # ---- 4c. the baseline that actually matters --------------------------
    rows = (baseline or {}).get("results") or []
    if rows:
        a("## 4c. Contra uma regressão logística sobre as mesmas features\n")
        a("Superar a classe majoritária é uma barra baixa. A pergunta de um\n"
          "discovery é se um modelo de 421M parâmetros se paga contra algumas\n"
          "linhas de aritmética sobre features que já extraímos de graça.\n")
        a("Duas variantes, e a diferença entre elas é um resultado por si só:\n")
        a("- **leaky** — todas as features, inclusive aquelas de que o gabarito é\n"
          "  *definido*. Mede **quanto da pergunta o cartão simplesmente entrega**.")
        a("- **clean** — essas features removidas. É o baseline honesto.\n")
        a("Tudo avaliado *leave-one-out*, nunca ajustando e medindo nas mesmas\n"
          "linhas.\n")
        a("| pergunta | variante | feats | LR acc | LR AUC | Laya acc | "
          "Laya AUC | McNemar p | leitura |")
        a("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            p_value = (r.get("vs_laya") or {}).get("p_value")
            laya_acc = r.get("laya_accuracy")
            if p_value is None or laya_acc is None:
                verdict, shown = "—", "—"
            else:
                shown = f"{p_value:.4f}"
                if p_value >= 0.05:
                    verdict = "empate estatístico"
                elif laya_acc > r["accuracy"]:
                    verdict = "**Laya vence**"
                else:
                    verdict = "**LR vence**"
            a(f"| `{r['question']}` | {r['variant']} | {r['n_features']} | "
              f"{r['accuracy']:.0%} | {(r.get('auc') or 0):.2f} | "
              f"{(laya_acc or 0):.0%} | {(r.get('laya_auc') or 0):.2f} | "
              f"{shown} | {verdict} |")
        a("\n> A variante **leaky** chegando a 97–100% é a medida da circularidade\n"
          "> deste experimento: o cartão lista os fatos perguntados e uma regressão\n"
          "> logística os lê de volta. Nessas perguntas o Laya não tem como agregar\n"
          "> valor — e de fato fica **abaixo** da aritmética sobre o mesmo input.\n")
        a("> Na variante **clean** os dois empatam estatisticamente nas três\n"
          "> perguntas verificáveis: o Laya não perde, mas também não ganha.\n")

    # ---- 5. confusion ----------------------------------------------------
    a("## 5. Matriz de confusão — complexidade\n")
    matrix = metrics.confusion(decisions, "migration_complexity", BANDS)
    a("| gold \\ predito | " + " | ".join(BANDS) + " |")
    a("|---" * (len(BANDS) + 1) + "|")
    for gold in BANDS:
        row = matrix.get(gold, {})
        a(f"| **{gold}** | " + " | ".join(str(row.get(p, 0)) for p in BANDS) + " |")

    a("\n## 5b. Matriz de confusão — estratégia de reescrita\n")
    matrix = metrics.confusion(decisions, "rewrite_strategy", STRATEGIES)
    a("| gold \\ predito | " + " | ".join(STRATEGIES) + " |")
    a("|---" * (len(STRATEGIES) + 1) + "|")
    for gold in STRATEGIES:
        row = matrix.get(gold, {})
        if sum(row.values()) == 0 and gold not in {
            (docs.get(d["script_id"], {}).get("gold") or {}).get("rewrite_strategy")
            for d in decisions
        }:
            continue
        a(f"| **{gold}** | " + " | ".join(str(row.get(p, 0)) for p in STRATEGIES) + " |")

    # ---- 5c. ranking signal ----------------------------------------------
    signal = metrics.ranking_signal(raw or {}, docs)
    if signal:
        a("\n## 5c. O argmax travou — mas existe sinal de ordenação?\n")
        a("A matriz acima tem uma coluna só: o argmax caiu na mesma classe para "
          "todos os scripts.\nIsso *parece* ausência total de sinal. Mas a "
          "distribuição por trás do argmax\nnão é constante — ela se move na "
          "direção certa:\n")
        a(f"- Correlação de postos (Spearman, n={signal['n']}) entre os pontos de "
          f"rubrica e o **score esperado** do Laya: **rho = "
          f"{signal['rho_expected_score']:+.3f}**.")
        a(f"- Entre pontos de rubrica e P(high): rho = {signal['rho_p_high']:+.3f}.")
        a(f"- Entre pontos de rubrica e P(low): rho = {signal['rho_p_low']:+.3f}.")
        lo, hi = signal["expected_score_range"]
        a(f"- Mas o score esperado varia só de **{lo} a {hi}**, numa escala de 0 a 2"
          " — todo\n  o intervalo útil comprimido em torno da classe do meio.\n")
        a("| pontos gold | score esperado do Laya |")
        a("|---|---|")
        for points, score in signal["pairs"]:
            a(f"| {points:.0f} | {score:.3f} |")
        a("\n> Esta é a diferença entre *não ter sinal* e *não saber onde cortar*.\n"
          "> A primeira exigiria outras features; a segunda se resolve com\n"
          "> calibração de temperatura ou um limiar ajustado sobre o score\n"
          "> esperado — muito mais barato.\n")

    # ---- 6. calibration ---------------------------------------------------
    a("\n## 6. Calibração\n")
    all_outcomes = [q for d in decisions for q in d["questions"]]
    ece = metrics.expected_calibration_error(all_outcomes)
    a(f"**ECE = {ece['ece']:.3f}** sobre {ece['n']} decisões "
      "(0 = perfeitamente calibrado).\n")
    a("| faixa de confiança | n | confiança média | acurácia | lacuna |")
    a("|---|---|---|---|---|")
    for b in ece["bins"]:
        if not b["n"]:
            a(f"| {b['bin']} | 0 | — | — | — |")
            continue
        a(f"| {b['bin']} | {b['n']} | {b['mean_confidence']:.0%} | "
          f"{b['accuracy']:.0%} | {b['gap']:.0%} |")

    brier = metrics.brier_score(all_outcomes)
    if brier is not None:
        a(f"\n**Brier = {brier:.3f}** (0 = perfeito, 0.25 = chute a 50%).\n")

    # ---- 7. coverage curve ------------------------------------------------
    a("## 7. Cobertura × acurácia — onde colocar o corte\n")
    a("| limiar | respostas acima | cobertura | acurácia | erros |")
    a("|---|---|---|---|---|")
    for point in metrics.coverage_curve(decisions):
        acc_text = f"{point['accuracy']:.0%}" if point["accuracy"] is not None else "—"
        a(f"| {point['threshold']:.2f} | {point['n_kept']} | "
          f"{point['coverage']:.0%} | {acc_text} | {point['errors']} |")
    a("\n> Se a acurácia **não sobe** conforme o limiar aperta, a confiança não\n"
      "> carrega informação sobre estar certo — e nenhum corte torna o\n"
      "> classificador auto-operável.\n")

    a("## 7b. O mesmo corte, mas por script\n")
    a("A tabela acima conta **respostas**. Um script só é triado sem humano "
      "quando\n*todas* as perguntas sobre ele passam do corte ao mesmo tempo — "
      "e a conjunção\nde respostas independentes é muito mais dura que cada uma "
      "isolada.\n")
    a("| limiar | scripts com os 3 fatos acima do corte | cobertura | acurácia (IC95) | erros |")
    a("|---|---|---|---|---|")
    for point in metrics.script_level_coverage(decisions, VERIFIABLE):
        acc_text = f"{point['accuracy']:.0%}" if point["accuracy"] is not None else "—"
        kept = point["scripts_all_confident"]
        ci = ""
        if kept:
            lo, hi = metrics.wilson_interval(kept - point["errors"], kept)
            ci = f" ({lo:.0%}–{hi:.0%})"
        a(f"| {point['threshold']:.2f} | {kept} | "
          f"{point['coverage']:.0%} | {acc_text}{ci} | {point['errors']} |")
    all_right = sum(
        1 for d in decisions
        if all(q["agree"] for q in d["questions"] if q["question"] in VERIFIABLE)
    )
    a(f"\nSem exigir confiança nenhuma, **{all_right}/{n} scripts "
      f"({100 * all_right / n:.0f}%) acertam os três fatos verificáveis**. "
      "É a distância\nentre esse número e a coluna de cobertura acima que mede "
      "o custo da exigência\nde confiança — e é ela que zera o `AUTO`.\n")

    # ---- 8. error vs complexity ------------------------------------------
    a("## 8. Onde o modelo erra\n")
    a("| script | pontos gold | fontes | arestas | subq | erros de 6 |")
    a("|---|---|---|---|---|---|")
    for d in decisions:
        doc = docs.get(d["script_id"], {})
        f = doc.get("features") or {}
        errors = sum(1 for q in d["questions"] if not q["agree"])
        a(f"| `{d['script_id']}` | {(doc.get('gold') or {}).get('rubric_points')} | "
          f"{f.get('source_tables')} | {f.get('graph_edges')} | "
          f"{f.get('subquery_count')} | **{errors}** |")

    # ---- 9. latency -------------------------------------------------------
    a("\n## 9. Latência\n")
    lat = metrics.latency_summary(decisions)
    if lat:
        a(f"- Carga do modelo: **{run.get('load_seconds')} s** (uma vez).")
        a(f"- Por script ({run.get('n_questions')} perguntas): "
          f"**p50 = {lat['p50_ms']:.0f} ms · p95 = {lat['p95_ms']:.0f} ms** "
          f"(min {lat['min_ms']:.0f}, max {lat['max_ms']:.0f}).")
        a(f"- Lote completo: **{lat['total_s']} s** para {lat['n']} scripts.")
        per_q = lat["p50_ms"] / max(1, run.get("n_questions", 1))
        a(f"- Por pergunta: ~{per_q:.0f} ms.")
        a(f"\nExtrapolando para as 99 queries do corpus: "
          f"~{99 * lat['mean_ms'] / 1000:.0f} s de inferência em CPU.")

    a("\n| script | estimado (ms) | medido (ms) | erro |")
    a("|---|---|---|---|")
    for d in decisions:
        latency = docs.get(d["script_id"], {}).get("latency") or {}
        est, real = latency.get("estimated_ms"), latency.get("measured_ms")
        if est and real:
            a(f"| `{d['script_id']}` | {est:.0f} | {real:.0f} | {100 * (real - est) / est:+.0f}% |")
    a("\n> O modelo de custo foi ajustado com texto sintético e subestima os cards\n"
      "> reais de forma consistente; serve para dimensionar um lote, não para SLA.\n")

    return "\n".join(out) + "\n"


def _question_order(decisions: list[dict]) -> list[str]:
    seen: list[str] = []
    for d in decisions:
        for q in d["questions"]:
            if q["question"] not in seen:
                seen.append(q["question"])
    return seen


def _badge(outcome: str) -> str:
    return {AUTO: "**AUTO**", HUMAN_REVIEW: "REVIEW", ESCALATE: "**ESCALATE**"}.get(
        outcome, outcome
    )


def _short(value) -> str:
    text = str(value)
    return text if len(text) <= 14 else text[:13] + "…"


def write(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
