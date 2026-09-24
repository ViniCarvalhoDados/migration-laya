"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import census as census_mod
from . import report_census
from .features import extract_features
from .rubric import score_features, load_rubric

DEFAULT_CORPUS = "corpus/tpcds"
DEFAULT_RUBRIC = "config/rubric.yml"
CENSUS_CSV = "state/corpus_census.csv"
PROFILE_YML = "state/corpus_profile.yml"
CENSUS_MD = "reports/census.md"
QUESTIONS_YML = "config/questions.yml"
SAMPLE_YML = "state/sample.yml"
LATENCY_YML = "state/latency_model.yml"
JUDGEMENTS_YML = "state/gold_judgements.yml"


def cmd_census(args: argparse.Namespace) -> int:
    corpus = Path(args.corpus)
    if not corpus.is_dir():
        print(f"corpus directory not found: {corpus}", file=sys.stderr)
        return 2

    pairs = census_mod.run_census(corpus)
    if not pairs:
        print(f"no .sql files in {corpus}", file=sys.stderr)
        return 2
    rows = [flat for _, flat in pairs]
    n = len(rows)

    failed = [r for r in rows if not r["parse_ok"]]
    if args.verify and failed:
        print(f"parse failed for {len(failed)}/{n} scripts:", file=sys.stderr)
        for r in failed:
            print(f"  {r['name']}: {r.get('parse_error', '')[:160]}", file=sys.stderr)
        return 1

    profile = census_mod.build_profile(rows)

    # The rubric is derived from this corpus unless the caller pins an existing
    # one, so that a re-run cannot silently move the goalposts under results
    # that were already reported.
    rubric_path = Path(args.rubric)
    if args.emit_rubric or not rubric_path.exists():
        rubric = census_mod.emit_rubric(profile, rows, corpus.as_posix(), n)
        census_mod.write_yaml(rubric, rubric_path)
        print(f"wrote {rubric_path}  (thresholds derived from n={n})")
    else:
        rubric = load_rubric(rubric_path)
        print(f"using existing {rubric_path}  (pass --emit-rubric to regenerate)")

    for row in rows:
        score = score_features(census_mod._nest(row), rubric)
        row["rubric_points"] = score.points
        row["rubric_band"] = score.band
        row["rubric_reasons"] = score.reasons

    census_mod.write_csv(rows, args.out_csv)
    census_mod.write_yaml(profile, args.out_profile)
    report_census.write(
        args.out_report,
        report_census.render(rows, profile, rubric, corpus.as_posix()),
    )

    print(f"wrote {args.out_csv}        ({n} rows)")
    print(f"wrote {args.out_profile}")
    print(f"wrote {args.out_report}")

    bands = {}
    for row in rows:
        bands[row["rubric_band"]] = bands.get(row["rubric_band"], 0) + 1
    summary = " · ".join(f"{k}={v}" for k, v in sorted(bands.items()))
    print(f"\nparse ok: {n - len(failed)}/{n}   bands: {summary}")
    return 0


def cmd_sample(args: argparse.Namespace) -> int:
    import csv
    import shutil

    from . import sample as sampler

    census_path = Path(args.census)
    if not census_path.exists():
        print(f"census not found: {census_path} — run `mlaya census` first", file=sys.stderr)
        return 2
    rubric_path = Path(args.rubric)
    if not rubric_path.exists():
        print(f"rubric not found: {rubric_path} — run `mlaya census --emit-rubric`", file=sys.stderr)
        return 2

    with census_path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    rubric = load_rubric(rubric_path)

    picked = sampler.select(rows, args.n, rubric, seed=args.seed)
    coverage = sampler.summarise_coverage(picked, rows)
    by_name = {r["name"]: r for r in rows}

    scripts_dir = Path(args.scripts_dir)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    corpus = Path(args.corpus)

    for entry in picked:
        src = corpus / f"{entry['origin']}.sql"
        dest = scripts_dir / f"{entry['id']}_{entry['origin']}.sql"
        shutil.copyfile(src, dest)
        entry["source_path"] = dest.as_posix()

    census_mod.write_yaml(
        {"meta": {"seed": args.seed, "census": census_path.as_posix(),
                  "rubric": rubric_path.as_posix()},
         "coverage": coverage,
         "scripts": picked},
        args.out,
    )
    _write_state_files(picked, by_name, Path(args.state_dir), args.questions)
    _write_notice(scripts_dir, picked)

    print(f"wrote {args.out}")
    print(f"copied {len(picked)} scripts into {scripts_dir}/")
    print(f"wrote {args.state_dir}/script_*.yml")
    print(f"\ncoverage: bands={coverage['bands']}  "
          f"points {coverage['rubric_points_range']} of corpus "
          f"{coverage['corpus_points_range']}")
    for entry in picked:
        print(f"  {entry['id']}  {entry['origin']:10} "
              f"{entry['rubric_band']:<7} {entry['rubric_points']:>2}pts  "
              f"{entry['selected_because'][0]}")
    return 0


def _write_state_files(picked, by_name, state_dir: Path, questions_path: str) -> None:
    """One YAML per sampled script: the contract the rest of the study reads."""
    import yaml

    categories = []
    qpath = Path(questions_path)
    if qpath.exists():
        categories = list(yaml.safe_load(qpath.read_text(encoding="utf-8")) or {})

    for entry in picked:
        row = by_name[entry["origin"]]
        features = {
            k: _coerce(v, k) for k, v in row.items()
            if k not in ("name", "rubric_points", "rubric_band")
        }
        doc = {
            "id": entry["id"],
            "name": entry["origin"],
            "source_path": entry["source_path"],
            "origin": f"tpc-ds {entry['origin']}",
            "dialect": row.get("parse_dialect", ""),
            "selected_because": entry["selected_because"],
            # Filled in by `mlaya card` before any Laya call.
            "evidence_card": {"purpose": None, "structure": None, "facts": None},
            "features": features,
            "corpus_percentile": entry["corpus_percentile"],
            "categories_to_verify": categories,
            "gold": {
                "migration_complexity": entry["rubric_band"],
                "rubric_points": entry["rubric_points"],
                "has_subquery": _coerce(row.get("subquery_count", 0), "subquery_count") > 0,
                "has_window_function": _coerce(row.get("window_function_count", 0), "window_function_count") > 0,
                "multi_source": _coerce(row.get("source_tables", 0), "source_tables") >= 4,
                # Judgement calls, written by Claude before the Laya run.
                "rewrite_strategy": None,
                "needs_human_review": None,
                "rationale": None,
                "source": "deterministic",
            },
            "latency": {"estimated_ms": None, "measured_ms": None},
        }
        census_mod.write_yaml(doc, state_dir / f"{entry['id']}.yml")


# Columns the census writes as "|"-joined lists. They must come back as lists
# even when they hold a single element, or downstream code that slices them
# silently iterates the string character by character.
_LIST_COLUMNS = frozenset(
    {"distinct_sources", "distinct_aggregates", "nonportable_markers",
     "distinct_functions", "rubric_reasons", "node_names"}
)


def _coerce(value, column: str | None = None):
    """CSV gives everything back as a string; restore numbers, bools and lists."""
    if not isinstance(value, str):
        return value
    if column in _LIST_COLUMNS:
        return [part for part in value.split("|") if part]
    if value in ("True", "False"):
        return value == "True"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _write_notice(scripts_dir: Path, picked) -> None:
    lines = [
        "# Procedência",
        "",
        "Os scripts desta pasta são queries do benchmark **TPC-DS**, obtidas de",
        "<https://github.com/agirish/tpcds> e copiadas sem alteração de conteúdo",
        "(apenas renomeadas para `script_NN_<origem>.sql`).",
        "",
        "As queries derivam da especificação TPC-DS, de propriedade do",
        "Transaction Processing Performance Council. Uso aqui restrito a",
        "avaliação técnica interna. Não redistribuir sem verificar os termos do TPC.",
        "",
        "| arquivo | origem |",
        "|---|---|",
    ]
    lines += [f"| `{e['id']}_{e['origin']}.sql` | TPC-DS {e['origin']} |" for e in picked]
    (scripts_dir / "NOTICE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _state_files(state_dir: str) -> list[Path]:
    return sorted(Path(state_dir).glob("script_*.yml"))


def cmd_card(args: argparse.Namespace) -> int:
    """Generate the deterministic half of each evidence card and check budgets."""
    import yaml

    from . import cards

    files = _state_files(args.state_dir)
    if not files:
        print(f"no script_*.yml in {args.state_dir} — run `mlaya sample` first",
              file=sys.stderr)
        return 2

    # Claude's blind judgements, written after reading the SQL and before any
    # Laya call. Kept in one reviewable file rather than scattered per script.
    judgements = {}
    jpath = Path(args.judgements)
    if jpath.exists():
        judgements = yaml.safe_load(jpath.read_text(encoding="utf-8")) or {}

    fit = {}
    lpath = Path(args.latency_model)
    if lpath.exists():
        fit = (yaml.safe_load(lpath.read_text(encoding="utf-8")) or {}).get("model_fit", {})

    over_budget = []
    for path in files:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        features = _nest_features(doc.get("features") or {})
        card = doc.setdefault("evidence_card", {})
        card["facts"] = cards.build_facts(features)
        card["structure"] = cards.build_structure(features)

        # Keyed by origin query, not by script id: ids are assigned by the
        # sampler and shift whenever the sample size changes.
        judgement = judgements.get(doc["name"]) or {}
        if judgement.get("purpose"):
            card["purpose"] = judgement["purpose"].strip()
        card.setdefault("purpose", None)

        gold = doc.setdefault("gold", {})
        for key in ("rewrite_strategy", "needs_human_review", "rationale"):
            if judgement.get(key) is not None:
                gold[key] = judgement[key]
        if judgement:
            gold["source"] = "deterministic+claude"

        ok, tokens = cards.check_budget(card)
        card["approx_tokens"] = tokens
        if not ok:
            over_budget.append((doc["id"], tokens))

        if fit:
            from .laya_client import estimate_ms
            doc.setdefault("latency", {})["estimated_ms"] = estimate_ms(tokens, fit)

        if not args.check:
            census_mod.write_yaml(doc, path)

        state = "OK " if ok else "OVER"
        missing = "" if card.get("purpose") else "   (purpose pending)"
        eta = doc.get("latency", {}).get("estimated_ms")
        eta_text = f"  ~{eta:>6.0f} ms est" if eta else ""
        print(f"  {state} {doc['id']}  ~{tokens:>3} tokens{eta_text}{missing}")

    if over_budget:
        print(f"\n{len(over_budget)} card(s) over the {cards.TOKEN_BUDGET}-token "
              f"budget: {over_budget}", file=sys.stderr)
        return 1
    print(f"\nall {len(files)} cards within the {cards.TOKEN_BUDGET}-token budget")
    return 0


def _nest_features(flat: dict) -> dict:
    """State files store features flat; cards.py expects the join graph nested."""
    return {
        **flat,
        "join_graph": {
            "edges": flat.get("graph_edges", 0),
            "max_scope_sources": flat.get("graph_max_scope_sources", 0),
            "widest_scope_shape": flat.get("graph_shape", "single"),
            "cross_join_risk": flat.get("cross_join_risk", 0),
        },
    }


def cmd_calibrate(args: argparse.Namespace) -> int:
    """Measure Laya's latency on this machine and fit a cost model."""
    import yaml

    from .laya_client import LayaClient, calibrate_latency

    questions = yaml.safe_load(Path(args.questions).read_text(encoding="utf-8"))
    client = LayaClient(model=args.model, device=args.device)

    print(f"loading {args.model} on {args.device} ...")
    client.load()
    print(f"loaded in {client.load_seconds}s")
    for w in client.warnings:
        print(f"  RUNTIME WARNING: {w}", file=sys.stderr)

    print(f"calibrating over {len(questions)} questions ...")
    result = calibrate_latency(client, questions)
    census_mod.write_yaml(result, args.out)

    print(f"\n  {'card_tok':>9} {'tok/quest':>10} {'median ms':>10} "
          f"{'ms/quest':>9} {'fits':>5}")
    for s in result["samples"]:
        print(f"  {s['card_tokens']:>9} {s['tokens_per_question']:>10} "
              f"{s['ms_median']:>10} {s['ms_per_question']:>9} "
              f"{'yes' if s['fits_context'] else 'NO':>5}")
    fit = result["model_fit"]
    print(f"\n  {fit['formula']}")
    print(f"  intercept_ms={fit['intercept_ms']}  "
          f"ms_per_card_token={fit['ms_per_card_token']}")
    if result["card_sizes_overflowing_context"]:
        print(f"  WARNING: card sizes over the "
              f"{result['context_limit_per_question']}-token context: "
              f"{result['card_sizes_overflowing_context']}")
    print(f"\nwrote {args.out}")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    """Run the sampled scripts through Laya and record raw answers plus timing."""
    import json
    import yaml

    from . import cards
    from .laya_client import LayaClient

    files = _state_files(args.state_dir)
    if args.only:
        files = [p for p in files if p.stem in args.only]
    if not files:
        print("no state files to ask about", file=sys.stderr)
        return 2

    questions = yaml.safe_load(Path(args.questions).read_text(encoding="utf-8"))
    docs = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in files]

    missing = [d["id"] for d in docs if not (d.get("evidence_card") or {}).get("purpose")]
    if missing and args.source == "card" and not (
            args.allow_incomplete or args.no_purpose):
        print(f"evidence cards without a purpose: {missing}\n"
              "Run `mlaya card` after filling state/gold_judgements.yml, or pass "
              "--allow-incomplete.", file=sys.stderr)
        return 2

    run_dir = Path(args.runs_dir) / args.run_id
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)

    client = LayaClient(model=args.model, device=args.device)
    print(f"loading {args.model} on {args.device} ...")
    client.load()
    print(f"loaded in {client.load_seconds}s")
    for w in client.warnings:
        print(f"  RUNTIME WARNING: {w}", file=sys.stderr)

    print(f"\n  {'script':11} {'est ms':>8} {'real ms':>8} {'delta':>7} {'tokens':>7}")
    predictions = []
    for path, doc in zip(files, docs):
        if args.source == "sql":
            prediction = _ask_over_sql(client, doc, questions)
        else:
            card = doc.get("evidence_card") or {}
            if args.no_purpose:
                # Ablation: hand Laya only the AST-derived half of the card, to
                # see whether the hand-written business purpose contributes.
                card = {**card, "purpose": ""}
            prediction = client.predict(doc["id"], cards.render_state(card),
                                        questions, origin=doc.get("name", ""))
        predictions.append(prediction)

        (run_dir / "raw" / f"{doc['id']}.json").write_text(
            json.dumps(prediction.as_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        estimated = (doc.get("latency") or {}).get("estimated_ms")
        doc.setdefault("latency", {})
        doc["latency"]["measured_ms"] = prediction.elapsed_ms
        doc["latency"]["ms_per_question"] = prediction.ms_per_question
        doc["latency"]["input_tokens"] = prediction.input_tokens
        doc["latency"]["device"] = args.device
        census_mod.write_yaml(doc, path)

        delta = f"{prediction.elapsed_ms - estimated:+.0f}" if estimated else "-"
        windows = getattr(prediction, "n_windows", 1)
        suffix = f"  {windows} janela(s)" if args.source == "sql" else ""
        print(f"  {doc['id']:11} {estimated or 0:>8.0f} "
              f"{prediction.elapsed_ms:>8.0f} {delta:>7} "
              f"{prediction.input_tokens:>7}{suffix}")

    census_mod.write_yaml(
        {"run_id": args.run_id,
         "model": args.model,
         "device": args.device,
         "load_seconds": client.load_seconds,
         "n_scripts": len(predictions),
         "n_questions": len(questions),
         "purpose_ablated": bool(args.no_purpose),
         "source": args.source,
         # Material to every conclusion drawn from these numbers.
         "runtime_warnings": client.warnings,
         "questions": questions},
        run_dir / "run.yml",
    )

    total = sum(p.elapsed_ms for p in predictions)
    print(f"\n{len(predictions)} scripts in {total / 1000:.1f}s "
          f"({total / len(predictions):.0f} ms each)")
    print(f"wrote {run_dir}/raw/*.json and {run_dir}/run.yml")
    return 0


def _load_run(args):
    import json
    import yaml

    run_dir = Path(args.runs_dir) / args.run_id
    run = yaml.safe_load((run_dir / "run.yml").read_text(encoding="utf-8"))
    docs = {}
    for path in _state_files(args.state_dir):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        docs[doc["id"]] = doc
    raw = {}
    for path in sorted((run_dir / "raw").glob("*.json")):
        raw[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return run_dir, run, docs, raw


def cmd_decide(args: argparse.Namespace) -> int:
    """Apply the decision tree to a finished run."""
    import csv

    from .decide import decide

    run_dir, run, docs, raw = _load_run(args)
    if not raw:
        print(f"no raw answers in {run_dir}/raw — run `mlaya ask` first", file=sys.stderr)
        return 2

    rubric = load_rubric(args.rubric)
    thresholds = rubric.get("confidence_bands", {"high": 0.85, "medium": 0.60})

    # Match answers to gold by origin query, falling back to the script id only
    # for runs recorded before origins were stored.
    by_origin = {d.get("name"): d for d in docs.values() if d.get("name")}
    stale = []

    decisions = []
    for script_id in sorted(raw):
        prediction = raw[script_id]
        origin = prediction.get("origin")
        if origin:
            doc = by_origin.get(origin)
            if doc is None:
                stale.append(f"{script_id} ({origin}): not in the current sample")
                continue
        else:
            doc = docs.get(script_id) or {}
            stale.append(f"{script_id}: run predates origin tracking")
        gold = doc.get("gold") or {}
        decisions.append(decide(
            script_id, gold, prediction.get("answers", {}), thresholds,
            elapsed_ms=prediction.get("elapsed_ms", 0.0),
        ).as_dict())

    census_mod.write_yaml(
        {"run_id": args.run_id, "confidence_bands": thresholds,
         "decisions": decisions},
        run_dir / "decisions.yml",
    )

    csv_path = run_dir / "decisions.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["script_id", "outcome", "question", "gold", "predicted",
                         "agree", "confidence", "confidence_band"])
        for d in decisions:
            for q in d["questions"]:
                writer.writerow([d["script_id"], d["outcome"], q["question"],
                                 q["gold"], q["predicted"], q["agree"],
                                 q["confidence"], q["confidence_band"]])

    if stale:
        print(f"WARNING: {len(stale)} script(s) could not be matched by origin "
              f"query; scores below may be paired with the wrong gold:",
              file=sys.stderr)
        for line in stale[:5]:
            print(f"  {line}", file=sys.stderr)

    counts = {}
    for d in decisions:
        counts[d["outcome"]] = counts.get(d["outcome"], 0) + 1
    for d in decisions:
        print(f"  {d['script_id']:11} {d['outcome']:<13} {d['reasons'][0][:88]}")
    print()
    print(counts)
    print(f"wrote {csv_path} and {run_dir}/decisions.yml")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    import yaml

    from . import report_run

    run_dir, run, docs, raw = _load_run(args)
    decisions_path = run_dir / "decisions.yml"
    if not decisions_path.exists():
        print(f"no decisions in {run_dir} — run `mlaya decide` first", file=sys.stderr)
        return 2
    decisions = yaml.safe_load(decisions_path.read_text(encoding="utf-8"))["decisions"]

    sample = {}
    sample_path = Path(args.sample)
    if sample_path.exists():
        sample = yaml.safe_load(sample_path.read_text(encoding="utf-8")) or {}

    baseline = {}
    baseline_path = run_dir / "baseline.yml"
    if baseline_path.exists():
        baseline = yaml.safe_load(baseline_path.read_text(encoding="utf-8")) or {}

    out = run_dir / "report.md"
    report_run.write(
        out, report_run.render(run, decisions, docs, sample, raw, baseline))
    print(f"wrote {out}")
    return 0


def cmd_baseline(args: argparse.Namespace) -> int:
    """Fit a logistic regression on the same features and compare it to Laya."""
    from . import baseline as lr
    from . import metrics
    from .decide import VERIFIABLE

    run_dir, run, docs, raw = _load_run(args)
    if not raw:
        print(f"no raw answers in {run_dir}/raw - run `mlaya ask` first",
              file=sys.stderr)
        return 2

    by_origin = {d.get("name"): d for d in docs.values() if d.get("name")}
    laya_score = {}
    for prediction in raw.values():
        doc = by_origin.get(prediction.get("origin")) or docs.get(
            prediction.get("script_id"), {})
        if not doc:
            continue
        for question, answer in (prediction.get("answers") or {}).items():
            if answer.get("type") != "noul":
                continue
            laya_score.setdefault(question, {})[doc["id"]] = float(
                answer.get("value") or 0.0)

    questions = list(VERIFIABLE) + ["needs_human_review"]
    results = []
    for question in questions:
        for drop_leaky in (False, True):
            result = lr.build_baseline(docs, question, drop_leaky=drop_leaky)
            if not result:
                continue
            ids = sorted(result["labels"])
            labels = [result["labels"][i] for i in ids]
            lr_probability = [result["probabilities"][i] for i in ids]
            lr_correct = [(p >= 0.5) == g for p, g in zip(lr_probability, labels)]

            enriched = [
                {"score": p, "gold_bool": g, "gradable": True}
                for p, g in zip(lr_probability, labels)
            ]
            result["auc"] = metrics.roc_auc(enriched)
            result["accuracy_ci95"] = metrics.wilson_interval(
                sum(lr_correct), len(lr_correct))

            scores = laya_score.get(question, {})
            if all(i in scores for i in ids):
                laya_correct = [(scores[i] >= 0.5) == g
                                for i, g in zip(ids, labels)]
                result["laya_accuracy"] = round(
                    sum(laya_correct) / len(laya_correct), 4)
                result["laya_auc"] = metrics.roc_auc([
                    {"score": scores[i], "gold_bool": g, "gradable": True}
                    for i, g in zip(ids, labels)
                ])
                result["vs_laya"] = metrics.mcnemar(laya_correct, lr_correct)
            results.append({k: v for k, v in result.items()
                            if k not in ("probabilities", "labels")})

    census_mod.write_yaml(
        {"run_id": args.run_id, "features": list(lr.FEATURES),
         "method": "logistic regression, leave-one-out, L2=1.0",
         "results": results},
        run_dir / "baseline.yml",
    )

    print(f"  {'pergunta':22}{'variante':>9}{'feat':>6}{'LR acc':>8}{'LR AUC':>8}"
          f"{'Laya acc':>10}{'Laya AUC':>10}{'McNemar':>9}")
    for r in results:
        print(f"  {r['question']:22}{r['variant']:>9}{r['n_features']:>6}"
              f"{r['accuracy']:>8.0%}{(r.get('auc') or 0):>8.2f}"
              f"{(r.get('laya_accuracy') or 0):>10.0%}"
              f"{(r.get('laya_auc') or 0):>10.2f}"
              f"{(r.get('vs_laya') or {}).get('p_value', 1):>9.4f}")
    print(f"\nwrote {run_dir}/baseline.yml")
    return 0


def _ask_over_sql(client, doc, questions):
    """Ask every question of every window of the raw SQL, then aggregate.

    Returns a Prediction shaped exactly like the card path so `decide` and
    `report` need to know nothing about chunking.
    """
    from . import chunks
    from .laya_client import Prediction

    sql = Path(doc["source_path"]).read_text(encoding="utf-8")
    windows = chunks.split_sql(sql)
    if not windows:
        windows = [sql]

    per_question: dict[str, list[dict]] = {}
    elapsed = tokens = 0.0
    for index, window in enumerate(windows):
        state = chunks.render_window(window, index, len(windows))
        part = client.predict(doc["id"], state, questions,
                              origin=doc.get("name", ""))
        elapsed += part.elapsed_ms
        tokens += part.input_tokens
        for key, answer in part.answers.items():
            per_question.setdefault(key, []).append(answer)

    answers = {
        key: chunks.aggregate(key, values) for key, values in per_question.items()
    }
    prediction = Prediction(
        script_id=doc["id"],
        origin=doc.get("name", ""),
        answers=answers,
        input_tokens=int(tokens),
        elapsed_ms=round(elapsed, 1),
        ms_per_question=round(elapsed / max(1, len(answers)), 1),
    )
    prediction.n_windows = len(windows)
    return prediction


def cmd_compare(args: argparse.Namespace) -> int:
    """Head-to-head of two runs over the same gold — e.g. card vs raw SQL."""
    import json

    from . import metrics
    from .chunks import STRUCTURALLY_GLOBAL
    from .decide import VERIFIABLE

    docs = {}
    for path in _state_files(args.state_dir):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if doc.get("name"):
            docs[doc["name"]] = doc

    def load(run_id):
        out = {}
        for path in sorted((Path(args.runs_dir) / run_id / "raw").glob("*.json")):
            answer = json.loads(path.read_text(encoding="utf-8"))
            out[answer.get("origin") or answer["script_id"]] = answer
        return out

    left, right = load(args.left), load(args.right)
    shared = sorted(set(left) & set(right) & set(docs))
    if not shared:
        print("the two runs share no scripts with gold", file=sys.stderr)
        return 2

    rows = []
    for question in list(VERIFIABLE) + ["needs_human_review"]:
        gold = [bool(docs[n]["gold"][question]) for n in shared]
        measured = {}
        for label, run in ((args.left, left), (args.right, right)):
            scores = [float(run[n]["answers"][question]["value"]) for n in shared]
            correct = [(s >= 0.5) == g for s, g in zip(scores, gold)]
            measured[label] = {
                "accuracy": round(sum(correct) / len(correct), 4),
                "auc": metrics.roc_auc([
                    {"score": s, "gold_bool": g, "gradable": True}
                    for s, g in zip(scores, gold)
                ]),
                "mean_p_true": round(sum(scores) / len(scores), 4),
                "correct": correct,
            }
        test = metrics.mcnemar(measured[args.right]["correct"],
                               measured[args.left]["correct"])
        rows.append({
            "question": question,
            "gold_positive_rate": round(sum(gold) / len(gold), 4),
            "structurally_global": question in STRUCTURALLY_GLOBAL,
            args.left: {k: v for k, v in measured[args.left].items() if k != "correct"},
            args.right: {k: v for k, v in measured[args.right].items() if k != "correct"},
            "mcnemar": test,
        })

    out_path = Path(args.runs_dir) / args.right / f"compare_vs_{args.left}.yml"
    census_mod.write_yaml(
        {"left": args.left, "right": args.right, "n": len(shared), "results": rows},
        out_path,
    )

    print(f"{len(shared)} scripts em comum")
    print()
    print(f"  {'pergunta':21}{'gold+':>7}"
          f"{args.left[:9] + ' acc':>14}{'AUC':>6}{'P(t)':>6}"
          f"{args.right[:9] + ' acc':>14}{'AUC':>6}{'P(t)':>6}{'McNemar':>10}")
    for r in rows:
        a_, b_ = r[args.left], r[args.right]
        flag = " *" if r["structurally_global"] else ""
        print(f"  {r['question']:21}{r['gold_positive_rate']:>7.0%}"
              f"{a_['accuracy']:>14.0%}{(a_['auc'] or 0):>6.2f}{a_['mean_p_true']:>6.2f}"
              f"{b_['accuracy']:>14.0%}{(b_['auc'] or 0):>6.2f}{b_['mean_p_true']:>6.2f}"
              f"{r['mcnemar']['p_value']:>10.4f}{flag}")
    if any(r["structurally_global"] for r in rows):
        print()
        print("  * pergunta de contagem global - uma janela nao ve o script inteiro")
    print()
    print(f"wrote {out_path}")
    return 0


def cmd_variants(args: argparse.Namespace) -> int:
    """Report how much each answer moves when the question is reworded."""
    import json

    from . import variants as probe

    docs = {}
    for path in _state_files(args.state_dir):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if doc.get("name"):
            docs[doc["name"]] = doc

    run_dir = Path(args.runs_dir) / args.run_id
    raw = {}
    for path in sorted((run_dir / "raw").glob("*.json")):
        answer = json.loads(path.read_text(encoding="utf-8"))
        raw[answer.get("origin") or answer["script_id"]] = answer
    if not raw:
        print(f"no raw answers in {run_dir}/raw", file=sys.stderr)
        return 2

    rows = probe.analyse(raw, docs, args.questions)
    if not rows:
        print("no question had all three variants in this run", file=sys.stderr)
        return 2
    summary = probe.summarise(rows)
    census_mod.write_yaml({"run_id": args.run_id, "summary": summary,
                           "results": rows}, run_dir / "variants.yml")

    print(f"  {'pergunta':22}{'v1':>7}{'v2':>7}{'|d|':>7}"
          f"{'v3 previsto':>13}{'v3 obtido':>11}  negacao")
    for r in rows:
        neg = r.get("negation", {})
        print(f"  {r['question']:22}{r['v1']['auc']:>7.2f}{r['v2']['auc']:>7.2f}"
              f"{r.get('paraphrase_shift', 0):>7.2f}"
              f"{neg.get('predicted_auc', 0):>13.2f}{neg.get('observed_auc', 0):>11.2f}"
              f"  {'inverteu' if neg.get('inverted') else 'NAO inverteu'}")
    print()
    print(f"  deslocamento medio por reescrita: {summary['mean_paraphrase_shift']:.2f} AUC"
          f"  (max {summary['max_paraphrase_shift']:.2f})")
    print(f"  inverteram sob negacao: {summary['inverted_under_negation']}"
          f"/{summary['inverted_under_negation'] + summary['failed_to_invert']}")
    print()
    print(f"wrote {run_dir}/variants.yml")
    return 0


def cmd_ensemble(args: argparse.Namespace) -> int:
    """Compare single wordings against aggregations over several paraphrases."""
    import json

    from . import ensemble as ens

    docs = {}
    for path in _state_files(args.state_dir):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if doc.get("name"):
            docs[doc["name"]] = doc

    run_dir = Path(args.runs_dir) / args.run_id
    raw = {}
    for path in sorted((run_dir / "raw").glob("*.json")):
        answer = json.loads(path.read_text(encoding="utf-8"))
        raw[answer.get("origin") or answer["script_id"]] = answer
    if not raw:
        print(f"no raw answers in {run_dir}/raw", file=sys.stderr)
        return 2

    any_answer = next(iter(raw.values())).get("answers") or {}
    rows = []
    for question in args.questions:
        keys = sorted(k for k in any_answer if k.startswith(question + "_p"))
        if len(keys) < 2:
            continue
        row = ens.analyse(raw, docs, question, keys)
        if row:
            row["verdict"] = ens.verdict(row)
            rows.append(row)
    if not rows:
        print("no question had several paraphrases in this run", file=sys.stderr)
        return 2

    census_mod.write_yaml({"run_id": args.run_id, "results": rows},
                          run_dir / "ensemble.yml")

    print(f"  {'pergunta':22}{'paraf.':>7}{'AUC pior':>10}{'AUC melhor':>12}"
          f"{'amplitude':>11}{'media':>8}{'ENSEMBLE':>10}{'hold-out':>10}  leitura")
    for r in rows:
        agg = r["aggregated"]["mean"]
        ho = agg.get("holdout_accuracy")
        print(f"  {r['question']:22}{r['n_paraphrases']:>7}"
              f"{r['single_auc_min']:>10.2f}{r['single_auc_max']:>12.2f}"
              f"{r['single_auc_spread']:>11.2f}{r['single_auc_mean']:>8.2f}"
              f"{agg['auc']:>10.2f}"
              f"{(f'{ho:.0%}' if ho is not None else '-'):>10}  {r['verdict']}")
    print()
    print("  AUC melhor = oraculo: escolhido com o gabarito na mao, teto e nao estrategia.")
    print("  ENSEMBLE   = media de P(true) entre as parafrases; nao olha o gabarito.")
    print()
    print(f"wrote {run_dir}/ensemble.yml")
    return 0


def cmd_paired(args: argparse.Namespace) -> int:
    """Laya against both logistic-regression variants, all fitted on train only.

    `--paraphrases` averages every `<question>_pN` wording present in the run,
    which is the E10 ensemble; without it the single wording is scored, which is
    E8. Either way the two regressions get the same splits, so the three arms
    are directly comparable.
    """
    from . import paired as pr

    run_dir, _run, docs, raw = _load_run(args)
    if not raw:
        print(f"no raw answers in {run_dir}/raw - run `mlaya ask` first",
              file=sys.stderr)
        return 2

    any_answer = next(iter(raw.values())).get("answers") or {}
    rows = []
    for question in args.questions:
        if args.paraphrases:
            keys = sorted(k for k in any_answer if k.startswith(question + "_p"))
            if len(keys) < 2:
                continue
        else:
            keys = [question] if question in any_answer else []
            if not keys:
                continue
        scores = pr.aggregate_scores(raw, docs, question, keys)
        row = pr.compare(docs, question, scores, splits=args.splits,
                         seed=args.seed)
        if row:
            row["wordings"] = keys
            rows.append(row)

    if not rows:
        print("no question could be scored in this run", file=sys.stderr)
        return 2

    label = "ensemble" if args.paraphrases else "single"
    census_mod.write_yaml(
        {"run_id": args.run_id, "arm": label, "splits": args.splits,
         "seed": args.seed,
         "protocol": "stratified half-splits; threshold, coefficients and "
                     "majority class all fitted on the training half only",
         "results": rows},
        run_dir / f"paired_{label}.yml",
    )

    print(f"  {'pergunta':22}{'Laya':>7}{'LR limpa':>10}{'LR vazada':>11}"
          f"{'base':>7}   {'Laya-limpa':>22}   {'Laya-vazada':>22}")
    for r in rows:
        acc = r["accuracy"]
        clean = r["differences"]["laya_minus_lr_clean"]
        leaky = r["differences"]["laya_minus_lr_leaky"]
        print(f"  {r['question']:22}"
              f"{acc['laya']['mean']:>7.0%}{acc['lr_clean']['mean']:>10.0%}"
              f"{acc['lr_leaky']['mean']:>11.0%}{acc['majority']['mean']:>7.0%}"
              f"   {_delta(clean):>22}   {_delta(leaky):>22}")
    print()
    print("  LR limpa  = sem as features que definem o rotulo (piso honesto).")
    print("  LR vazada = com elas, ou seja, a mesma informacao que o cartao da"
          " ao Laya.")
    print()
    print(f"wrote {run_dir}/paired_{label}.yml")
    return 0


def _delta(summary: dict) -> str:
    return (f"{100 * summary['mean']:+.1f} "
            f"[{100 * summary['p05']:+.0f},{100 * summary['p95']:+.0f}] "
            f"{summary['verdict']}")


def cmd_business(args: argparse.Namespace) -> int:
    """Score the two commercial questions across every wording in a run."""
    from . import business as biz

    run_dir, _run, docs, raw = _load_run(args)
    if not raw:
        print(f"no raw answers in {run_dir}/raw - run `mlaya ask` first",
              file=sys.stderr)
        return 2

    by_id = {p.get("origin") or p["script_id"]: p for p in raw.values()}
    any_answer = next(iter(raw.values())).get("answers") or {}

    complexity, strategy = [], []
    for key in sorted(any_answer):
        if key.startswith("migration_complexity"):
            row = biz.complexity(raw, docs, key, splits=args.splits,
                                 seed=args.seed)
            if row:
                complexity.append(row)
        elif key.startswith("rewrite_strategy"):
            row = biz.strategy(raw, docs, key)
            if row:
                strategy.append(row)

    wordings = sorted(k for k in any_answer
                      if k.startswith("migration_complexity"))
    if len(wordings) > 1:
        row = biz.complexity(raw, docs, wordings, splits=args.splits,
                             seed=args.seed)
        if row:
            complexity.append(row)

    if not complexity and not strategy:
        print("no business question in this run", file=sys.stderr)
        return 2

    trivial = biz.trivial_baselines(docs, splits=args.splits, seed=args.seed)

    census_mod.write_yaml(
        {"run_id": args.run_id, "splits": args.splits, "seed": args.seed,
         "note": "the complexity gold is a deterministic function of the "
                 "extracted features, so the rubric itself scores 100% for "
                 "free and single features are strong baselines",
         "migration_complexity": complexity,
         "trivial_baselines": trivial,
         "rewrite_strategy": strategy},
        run_dir / "business.yml",
    )

    if complexity:
        base = complexity[0]["majority_baseline"]
        print(f"  migration_complexity   (base = classe majoritaria "
              f"{base:.0%}, rubrica = 100%)")
        print(f"    {'redacao':24}{'AUC low-high':>14}{'argmax':>8}{'rotulos':>9}"
              f"{'hold-out':>10}{'[p05,p95]':>16}{'teto':>7}{'2 bandas':>10}")
        for r in complexity:
            ho = r["holdout_accuracy"]
            print(f"    {r['wording']:24}"
                  f"{(r['auc_low_vs_high'] or 0):>14.2f}"
                  f"{r['argmax_accuracy']:>8.0%}{r['distinct_argmax_labels']:>9}"
                  f"{ho['mean']:>10.0%}"
                  f"{f'[{ho["p05"]:.0%},{ho["p95"]:.0%}]':>16}"
                  f"{r['optimistic_accuracy']:>7.0%}"
                  f"{r['error_structure_holdout']['two_bands']:>10.0%}")

    if trivial:
        print()
        print("  regras triviais sobre uma feature so, mesmo protocolo")
        print(f"    {'preditor':24}{'AUC low-high':>14}{'hold-out':>26}"
              f"{'teto':>7}{'2 bandas':>10}")
        for r in trivial:
            auc = r["auc_low_vs_high"]
            es = r.get("error_structure_holdout") or r["error_structure_optimistic"]
            print(f"    {r['predictor']:24}"
                  f"{(f'{auc:.2f}' if auc is not None else '-'):>14}"
                  f"{r['holdout_accuracy']['mean']:>26.0%}"
                  f"{r['optimistic_accuracy']:>7.0%}{es['two_bands']:>10.0%}")

    if strategy:
        base = strategy[0]["majority_baseline"]
        print()
        print(f"  rewrite_strategy       (base = classe majoritaria {base:.0%})")
        print(f"    {'redacao':24}{'acuracia':>10}{'IC95':>18}   classes previstas")
        for r in strategy:
            low, high = r["accuracy_ci95"]
            print(f"    {r['wording']:24}{r['accuracy']:>10.0%}"
                  f"{f'[{low:.0%},{high:.0%}]':>18}   "
                  f"{', '.join(r['distinct_predictions'])}")

    print()
    print(f"wrote {run_dir}/business.yml")
    return 0


def cmd_derive_labels(args: argparse.Namespace) -> int:
    """Label a finished migration by diffing legacy against migrated SQL."""
    from . import labels as lab

    legacy_dir, migrated_dir = Path(args.legacy), Path(args.migrated)
    if not legacy_dir.is_dir() or not migrated_dir.is_dir():
        print("both --legacy and --migrated must be directories", file=sys.stderr)
        return 2

    pairs = []
    for path in sorted(legacy_dir.glob("*.sql")):
        counterpart = migrated_dir / path.name
        if counterpart.exists():
            pairs.append((path.as_posix(), counterpart.as_posix()))
    if not pairs:
        print(f"no file in {legacy_dir} has a match by name in {migrated_dir}",
              file=sys.stderr)
        return 2

    rows = lab.derive_many(pairs)
    summary = lab.summarise(rows)
    census_mod.write_yaml(
        {"summary": summary, "derivations": [r.as_dict() for r in rows]},
        args.out,
    )

    print(f"  {'script':24}{'estrategia':18}{'confianca':12} motivo")
    for row in rows:
        print(f"  {row.name[:23]:24}{row.strategy:18}{row.confidence:12}"
              f"{row.reasons[0][:44] if row.reasons else ''}")
    print()
    print(f"  {summary['n']} pares  ->  {summary['by_strategy']}")
    print(f"  confianca: {summary['by_confidence']}")
    if summary["thin_classes"]:
        print(f"  CLASSES MAGRAS (<20 exemplos): {summary['thin_classes']}")
        print("  um fine-tune nunca vai prever uma classe que quase nao viu.")
    if summary["needs_human_review"]:
        print(f"  precisam de revisao humana: {len(summary['needs_human_review'])}")
    print()
    print(f"wrote {args.out}")
    return 0


def cmd_export_training(args: argparse.Namespace) -> int:
    """Emit train/calibration/test JSONL in the fine-tune notebook's format."""
    from . import training as tr

    questions = yaml.safe_load(Path(args.questions).read_text(encoding="utf-8"))
    cases = []
    for path in _state_files(args.state_dir):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        case = tr.build_case(doc, questions, doc.get("gold") or {})
        if case:
            cases.append(case)
    if not cases:
        print("no state file had both an evidence card and gold labels",
              file=sys.stderr)
        return 2

    splits = tr.split_by_family(cases, seed=args.seed)
    out_dir = Path(args.out_dir)
    for name, rows in splits.items():
        tr.write_jsonl(rows, out_dir / f"{name}.jsonl")

    summary = tr.report(splits, questions)
    census_mod.write_yaml(summary, out_dir / "dataset.yml")

    print(f"  casos por split : {summary['cases']}")
    print(f"  familias        : {summary['families']}")
    print(f"  decisoes totais : {summary['decisions_total']}"
          f"  (referencia do notebook: {summary['reference_scale']['decisions']})")
    if summary["family_overlap"]:
        print(f"  VAZAMENTO: familias repetidas entre splits "
              f"{summary['family_overlap']}", file=sys.stderr)
    else:
        print("  vazamento entre splits: nenhum (split por familia)")
    print()
    for qid, counts in summary["label_counts"].items():
        thin = [k for k, v in counts.items() if v < 20]
        flag = f"   CLASSES MAGRAS: {thin}" if thin else ""
        print(f"  {qid:24}{counts}{flag}")
    print()
    print(f"wrote {out_dir}/train.jsonl, calibration.jsonl, test.jsonl "
          f"and dataset.yml")
    return 0


def cmd_features(args: argparse.Namespace) -> int:
    """Print the extracted features for one file — the manual-audit tool."""
    f = extract_features(args.path)
    data = f.as_dict()
    if args.rubric and Path(args.rubric).exists():
        score = score_features(data, load_rubric(args.rubric))
        data["rubric"] = score.as_dict()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mlaya", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("census", help="profile every script in the corpus")
    c.add_argument("--corpus", default=DEFAULT_CORPUS)
    c.add_argument("--rubric", default=DEFAULT_RUBRIC)
    c.add_argument("--emit-rubric", action="store_true",
                   help="regenerate rubric thresholds from this corpus")
    c.add_argument("--verify", action="store_true",
                   help="exit non-zero if any script fails to parse")
    c.add_argument("--out-csv", default=CENSUS_CSV)
    c.add_argument("--out-profile", default=PROFILE_YML)
    c.add_argument("--out-report", default=CENSUS_MD)
    c.set_defaults(func=cmd_census)

    s = sub.add_parser("sample", help="draw the study set from the census")
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--seed", type=int, default=42)
    s.add_argument("--census", default=CENSUS_CSV)
    s.add_argument("--rubric", default=DEFAULT_RUBRIC)
    s.add_argument("--corpus", default=DEFAULT_CORPUS)
    s.add_argument("--questions", default=QUESTIONS_YML)
    s.add_argument("--scripts-dir", default="repos/legacy/scripts")
    s.add_argument("--state-dir", default="state")
    s.add_argument("--out", default=SAMPLE_YML)
    s.set_defaults(func=cmd_sample)

    c2 = sub.add_parser("card", help="build evidence cards and check token budget")
    c2.add_argument("--state-dir", default="state")
    c2.add_argument("--judgements", default=JUDGEMENTS_YML)
    c2.add_argument("--latency-model", default=LATENCY_YML)
    c2.add_argument("--check", action="store_true",
                    help="validate without writing; non-zero exit if over budget")
    c2.set_defaults(func=cmd_card)

    cal = sub.add_parser("calibrate", help="measure Laya latency on this machine")
    cal.add_argument("--questions", default=QUESTIONS_YML)
    cal.add_argument("--model", default="convaiinnovations/laya")
    cal.add_argument("--device", default="cpu")
    cal.add_argument("--out", default=LATENCY_YML)
    cal.set_defaults(func=cmd_calibrate)

    a = sub.add_parser("ask", help="run the sampled scripts through Laya")
    a.add_argument("--run-id", required=True)
    a.add_argument("--state-dir", default="state")
    a.add_argument("--questions", default=QUESTIONS_YML)
    a.add_argument("--runs-dir", default="runs")
    a.add_argument("--model", default="convaiinnovations/laya")
    a.add_argument("--device", default="cpu")
    a.add_argument("--only", nargs="*", default=None,
                   help="limit to these script ids (e.g. script_01)")
    a.add_argument("--allow-incomplete", action="store_true",
                   help="run even if some evidence cards have no purpose")
    a.add_argument("--no-purpose", action="store_true",
                   help="ablation: send only the AST-derived half of each card")
    a.add_argument("--source", choices=("card", "sql"), default="card",
                   help="card: the compressed evidence card (default); "
                        "sql: the raw SQL, split into context-sized windows")
    a.set_defaults(func=cmd_ask)

    d = sub.add_parser("decide", help="apply the decision tree to a run")
    d.add_argument("--run-id", required=True)
    d.add_argument("--runs-dir", default="runs")
    d.add_argument("--state-dir", default="state")
    d.add_argument("--rubric", default=DEFAULT_RUBRIC)
    d.set_defaults(func=cmd_decide)

    r = sub.add_parser("report", help="render the study report for a run")
    r.add_argument("--run-id", required=True)
    r.add_argument("--runs-dir", default="runs")
    r.add_argument("--state-dir", default="state")
    r.add_argument("--sample", default=SAMPLE_YML)
    r.set_defaults(func=cmd_report)

    b = sub.add_parser("baseline",
                       help="logistic regression on the same features, vs Laya")
    b.add_argument("--run-id", required=True)
    b.add_argument("--runs-dir", default="runs")
    b.add_argument("--state-dir", default="state")
    b.set_defaults(func=cmd_baseline)

    cmp_ = sub.add_parser("compare", help="two runs head to head over the same gold")
    cmp_.add_argument("left")
    cmp_.add_argument("right")
    cmp_.add_argument("--runs-dir", default="runs")
    cmp_.add_argument("--state-dir", default="state")
    cmp_.set_defaults(func=cmd_compare)

    v = sub.add_parser("variants", help="prompt-sensitivity and negation probe")
    v.add_argument("--run-id", required=True)
    v.add_argument("--runs-dir", default="runs")
    v.add_argument("--state-dir", default="state")
    v.add_argument("--questions", nargs="*",
                   default=["has_subquery", "has_window_function",
                            "multi_source", "needs_human_review"])
    v.set_defaults(func=cmd_variants)

    e = sub.add_parser("ensemble",
                       help="single wordings vs aggregation over paraphrases")
    e.add_argument("--run-id", required=True)
    e.add_argument("--runs-dir", default="runs")
    e.add_argument("--state-dir", default="state")
    e.add_argument("--questions", nargs="*",
                   default=["has_subquery", "has_window_function",
                            "multi_source", "needs_human_review"])
    e.set_defaults(func=cmd_ensemble)

    pd_ = sub.add_parser("paired",
                         help="Laya vs both logistic-regression variants, "
                              "fitted on train only")
    pd_.add_argument("--run-id", required=True)
    pd_.add_argument("--runs-dir", default="runs")
    pd_.add_argument("--state-dir", default="state")
    pd_.add_argument("--paraphrases", action="store_true",
                     help="average every <question>_pN wording (the E10 ensemble)")
    pd_.add_argument("--splits", type=int, default=200)
    pd_.add_argument("--seed", type=int, default=42)
    pd_.add_argument("--questions", nargs="*",
                     default=["has_subquery", "has_window_function",
                              "multi_source", "needs_human_review"])
    pd_.set_defaults(func=cmd_paired)

    bz = sub.add_parser("business",
                        help="score migration_complexity and rewrite_strategy")
    bz.add_argument("--run-id", required=True)
    bz.add_argument("--runs-dir", default="runs")
    bz.add_argument("--state-dir", default="state")
    bz.add_argument("--splits", type=int, default=200)
    bz.add_argument("--seed", type=int, default=42)
    bz.set_defaults(func=cmd_business)

    dl = sub.add_parser("derive-labels",
                        help="label a finished migration from legacy/migrated diffs")
    dl.add_argument("--legacy", required=True, help="directory of original .sql")
    dl.add_argument("--migrated", required=True, help="directory of migrated .sql")
    dl.add_argument("--out", default="state/derived_labels.yml")
    dl.set_defaults(func=cmd_derive_labels)

    et = sub.add_parser("export-training",
                        help="emit JSONL splits for the fine-tune notebook")
    et.add_argument("--state-dir", default="state")
    et.add_argument("--questions", default=QUESTIONS_YML)
    et.add_argument("--out-dir", default="training")
    et.add_argument("--seed", type=int, default=42)
    et.set_defaults(func=cmd_export_training)

    f = sub.add_parser("features", help="dump features for one SQL file")
    f.add_argument("path")
    f.add_argument("--rubric", default=DEFAULT_RUBRIC)
    f.set_defaults(func=cmd_features)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
