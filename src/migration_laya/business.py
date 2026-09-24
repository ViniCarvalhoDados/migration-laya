"""The two questions a consultancy would pay for, scored honestly.

`migration_complexity` (three ordered bands) and `rewrite_strategy` (four
classes) are the only questions in this study with commercial value, and both
are multi-class, so none of the binary machinery applies to them directly.

Three things this module is careful about, each because the first version of the
analysis got one of them wrong:

1. **The baseline is the majority class, counted on this corpus.** The bands
   come out 31 / 37 / 31, so the number to beat is **37%**, not the 31% that a
   "three bands, so one third" reflex produces. A wording that scores 38% is
   level with the baseline, not above it.

2. **Cut-points are fitted on a training half and scored on the held-out half.**
   The argmax of a `score` question is a constant here (always the middle band),
   so any usable accuracy comes from re-cutting the expected value — and a cut
   chosen on the same rows it is scored on is hindsight, not performance.

3. **The trivial rules are baselines, not curiosities.** A single feature —
   line count — cut into three bands reaches AUC 0.98 where the model reaches
   0.87. An error structure quoted alone ("only 8% are two-band errors") says
   nothing: a constant `medium` predictor makes *zero* two-band errors. So every
   number the model gets is reported beside the same number for `loc_code`,
   `max_nesting_depth` and the constant.

4. **The gold is the rubric, and the rubric is free.** `migration_complexity`
   gold is a deterministic function of features the extractor already computes,
   so anything that merely reproduces it adds nothing: the rubric itself scores
   100% at zero cost. That is reported next to every number here, because
   without it a 55% looks like a result instead of a worse copy of arithmetic
   that runs in milliseconds.
"""

from __future__ import annotations

import random

from . import metrics

BANDS: tuple[str, ...] = ("low", "medium", "high")
DEFAULT_SPLITS = 200
DEFAULT_SEED = 42


def _expected_level(probabilities: dict, order: list[str]) -> float:
    """Ordinal expected value: Σ P(level) × rank(level), rank starting at 0."""
    return sum(float(probabilities.get(name, 0.0)) * i
               for i, name in enumerate(order))


def _cut(value: float, thresholds: tuple[float, float]) -> int:
    low, high = thresholds
    if value < low:
        return 0
    return 1 if value < high else 2


# Expected levels are rounded to this many places before anything is compared
# to anything: the cut-point grid is built from the same numbers the cut is then
# applied to, so a value cannot land on the wrong side of a threshold it is
# exactly equal to. (1.6 stored as 1.5999999999999999 did precisely that, and
# quietly cost three bands of accuracy.)
PLACES = 3


def _fit_cuts(values: list[float], gold: list[int]) -> tuple[float, float]:
    """The pair of cut-points that maximises accuracy on these rows only."""
    grid = sorted(set(values))
    if len(grid) < 3:
        return (0.0, 0.0)
    best, best_hits = (grid[0], grid[-1]), -1
    for i, low in enumerate(grid):
        for high in grid[i:]:
            hits = sum(_cut(v, (low, high)) == g for v, g in zip(values, gold))
            if hits > best_hits:
                best_hits, best = hits, (low, high)
    return best


def _error_structure(predicted: list[int], gold: list[int]) -> dict:
    distances = [abs(p - g) for p, g in zip(predicted, gold)]
    n = len(distances)
    return {
        "exact": round(sum(d == 0 for d in distances) / n, 4),
        "one_band": round(sum(d == 1 for d in distances) / n, 4),
        "two_bands": round(sum(d == 2 for d in distances) / n, 4),
        "within_one": round(sum(d <= 1 for d in distances) / n, 4),
    }


def complexity(raw: dict, docs: dict, wording: str | list[str], *,
               splits: int = DEFAULT_SPLITS, seed: int = DEFAULT_SEED) -> dict:
    """Score one wording of the three-band complexity question.

    Returns argmax accuracy (what the model says unaided), the low-vs-high AUC
    (whether the expected value orders the corpus at all), and the accuracy of
    fitted cut-points measured only on held-out rows.

    Passing several wordings averages their expected levels — the E10 treatment
    applied to an ordinal question. The average never looks at the gold label.
    """
    wordings = [wording] if isinstance(wording, str) else list(wording)
    by_origin = {d.get("name"): d for d in docs.values() if d.get("name")}

    values, gold, labels, order = [], [], [], None
    for prediction in raw.values():
        doc = by_origin.get(prediction.get("origin"))
        if not doc:
            continue
        answers = [(prediction.get("answers") or {}).get(w) for w in wordings]
        band = (doc.get("gold") or {}).get("migration_complexity")
        if any(a is None for a in answers) or band not in BANDS:
            continue
        levels = []
        for answer in answers:
            probabilities = answer.get("probabilities") or {}
            if len(probabilities) != 3:
                return {}
            levels.append(_expected_level(probabilities, list(probabilities)))
        if order is None:
            order = list(answers[0].get("probabilities") or {})
        values.append(round(sum(levels) / len(levels), PLACES))
        gold.append(BANDS.index(band))
        # The argmax of an average is undefined; for several wordings the
        # unaided answer is reported as the majority vote across them.
        votes = [a.get("label") for a in answers]
        labels.append(max(set(votes), key=votes.count))

    if len(values) < 20:
        return {}

    counts = [gold.count(i) for i in range(3)]
    majority = max(counts) / len(gold)

    # What the model answers with no help: the raw argmax of the three levels.
    argmax_band = [order.index(label) if label in order else 1 for label in labels]
    argmax_accuracy = sum(p == g for p, g in zip(argmax_band, gold)) / len(gold)

    # Does the expected value order the corpus, ignoring where it cuts?
    extremes = [(v, g) for v, g in zip(values, gold) if g != 1]
    auc = metrics.roc_auc([
        {"score": v, "gold_bool": g == 2, "gradable": True}
        for v, g in extremes
    ]) if extremes else None

    # Fitted cut-points, scored only on rows the fit never saw.
    rng = random.Random(seed)
    by_band = {i: [j for j, g in enumerate(gold) if g == i] for i in range(3)}
    holdout, structures = [], []
    for _ in range(splits):
        train, test = [], []
        for members in by_band.values():
            shuffled = list(members)
            rng.shuffle(shuffled)
            cut = max(1, round(len(shuffled) * 0.5))
            train.extend(shuffled[:cut])
            test.extend(shuffled[cut:])
        if not test:
            continue
        thresholds = _fit_cuts([values[i] for i in train],
                               [gold[i] for i in train])
        predicted = [_cut(values[i], thresholds) for i in test]
        actual = [gold[i] for i in test]
        holdout.append(sum(p == g for p, g in zip(predicted, actual)) / len(test))
        structures.append(_error_structure(predicted, actual))

    ordered = sorted(holdout)
    in_sample_cuts = _fit_cuts(values, gold)
    in_sample = [_cut(v, in_sample_cuts) for v in values]

    return {
        "wording": wordings[0] if len(wordings) == 1 else "ensemble",
        "n": len(gold),
        "n_wordings": len(wordings),
        "distinct_argmax_labels": len(set(labels)),
        "band_counts": dict(zip(BANDS, counts)),
        "majority_baseline": round(majority, 4),
        "argmax_accuracy": round(argmax_accuracy, 4),
        "auc_low_vs_high": auc,
        "holdout_accuracy": {
            "mean": round(sum(ordered) / len(ordered), 4),
            "p05": round(ordered[int(0.05 * len(ordered))], 4),
            "p95": round(ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))], 4),
        },
        # Cut fitted and scored on the same 99 rows: a ceiling, never a result.
        "optimistic_accuracy": round(
            sum(p == g for p, g in zip(in_sample, gold)) / len(gold), 4),
        "error_structure_holdout": {
            key: round(sum(s[key] for s in structures) / len(structures), 4)
            for key in ("exact", "one_band", "two_bands", "within_one")
        },
        "error_structure_optimistic": _error_structure(in_sample, gold),
        # The gold is a deterministic function of the extracted features, so
        # the rubric that defines it is a free classifier that never errs.
        "rubric_accuracy": 1.0,
    }


def strategy(raw: dict, docs: dict, wording: str) -> dict:
    """Score one wording of the four-class rewrite-strategy question."""
    by_origin = {d.get("name"): d for d in docs.values() if d.get("name")}

    predicted, gold = [], []
    for prediction in raw.values():
        doc = by_origin.get(prediction.get("origin"))
        if not doc:
            continue
        answer = (prediction.get("answers") or {}).get(wording)
        label = (doc.get("gold") or {}).get("rewrite_strategy")
        if not answer or not label:
            continue
        predicted.append(answer.get("label"))
        gold.append(label)

    if len(gold) < 20:
        return {}

    counts: dict[str, int] = {}
    for label in gold:
        counts[label] = counts.get(label, 0) + 1
    hits = sum(p == g for p, g in zip(predicted, gold))

    return {
        "wording": wording,
        "n": len(gold),
        "distinct_predictions": sorted(set(predicted)),
        "gold_counts": dict(sorted(counts.items())),
        "majority_baseline": round(max(counts.values()) / len(gold), 4),
        "accuracy": round(hits / len(gold), 4),
        "accuracy_ci95": metrics.wilson_interval(hits, len(gold)),
    }


TRIVIAL: tuple[str, ...] = ("loc_code", "max_nesting_depth", "subquery_count",
                            "source_tables", "graph_edges")


def trivial_baselines(docs: dict, *, splits: int = DEFAULT_SPLITS,
                      seed: int = DEFAULT_SEED) -> list[dict]:
    """Score single AST features as three-band predictors of complexity.

    Same protocol as the model: cut-points fitted on a training half, scored on
    the held-out half. Without these rows, "AUC 0.87" and "only 8% two-band
    errors" read as achievements; beside `loc_code` at 0.98, and beside a
    constant `medium` that makes zero two-band errors by construction, they read
    as what they are.
    """
    ids = [k for k, d in sorted(docs.items())
           if (d.get("gold") or {}).get("migration_complexity") in BANDS]
    if len(ids) < 20:
        return []
    gold = [BANDS.index(docs[i]["gold"]["migration_complexity"]) for i in ids]

    rows = []
    for feature in TRIVIAL:
        values = [round(float((docs[i].get("features") or {}).get(feature, 0) or 0),
                        PLACES) for i in ids]
        if len(set(values)) < 3:
            continue
        rows.append(_score_ordinal(values, gold, feature, splits=splits,
                                   seed=seed))

    # The constant predictor: right 37% of the time, and never off by two bands.
    constant = [1] * len(gold)
    rows.append({
        "predictor": "constante `medium`",
        "auc_low_vs_high": None,
        "holdout_accuracy": {"mean": round(gold.count(1) / len(gold), 4)},
        "optimistic_accuracy": round(gold.count(1) / len(gold), 4),
        "error_structure_optimistic": _error_structure(constant, gold),
    })
    return rows


def _score_ordinal(values: list[float], gold: list[int], name: str, *,
                   splits: int, seed: int) -> dict:
    """Cut one ordered score into three bands, fitted on train, scored on test."""
    extremes = [(v, g) for v, g in zip(values, gold) if g != 1]
    auc = metrics.roc_auc([
        {"score": v, "gold_bool": g == 2, "gradable": True} for v, g in extremes
    ]) if extremes else None

    rng = random.Random(seed)
    by_band = {i: [j for j, g in enumerate(gold) if g == i] for i in range(3)}
    holdout, structures = [], []
    for _ in range(splits):
        train, test = [], []
        for members in by_band.values():
            shuffled = list(members)
            rng.shuffle(shuffled)
            cut = max(1, round(len(shuffled) * 0.5))
            train.extend(shuffled[:cut])
            test.extend(shuffled[cut:])
        if not test:
            continue
        thresholds = _fit_cuts([values[i] for i in train],
                               [gold[i] for i in train])
        predicted = [_cut(values[i], thresholds) for i in test]
        actual = [gold[i] for i in test]
        holdout.append(sum(p == g for p, g in zip(predicted, actual)) / len(test))
        structures.append(_error_structure(predicted, actual))

    ordered = sorted(holdout)
    in_sample = [_cut(v, _fit_cuts(values, gold)) for v in values]
    return {
        "predictor": name,
        "auc_low_vs_high": auc,
        "holdout_accuracy": {
            "mean": round(sum(ordered) / len(ordered), 4),
            "p05": round(ordered[int(0.05 * len(ordered))], 4),
            "p95": round(ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))], 4),
        },
        "optimistic_accuracy": round(
            sum(p == g for p, g in zip(in_sample, gold)) / len(gold), 4),
        "error_structure_holdout": {
            key: round(sum(s[key] for s in structures) / len(structures), 4)
            for key in ("exact", "one_band", "two_bands", "within_one")
        },
        "error_structure_optimistic": _error_structure(in_sample, gold),
    }
