"""Accuracy and calibration metrics.

Accuracy alone would not settle the question this study asks. The checkpoint
warns at load that its temperatures are invalid and its confidences
uncalibrated, so the useful question is not "how often is it right" but "when it
says 90%, is it right 90% of the time" — because the whole auto-triage idea
rests on trusting a confidence threshold.
"""

from __future__ import annotations

from collections import Counter


def gradable(outcomes: list[dict]) -> list[dict]:
    """Drop answers with no gold label.

    Once the study runs over the whole corpus, the two judgement questions have
    gold on only a subset of scripts. Counting an ungraded answer as wrong would
    report a failure that was never measured.
    """
    return [o for o in outcomes if o.get("gradable", o.get("gold") is not None)]


def accuracy(outcomes: list[dict]) -> tuple[int, int, float]:
    scored = gradable(outcomes)
    total = len(scored)
    hits = sum(1 for o in scored if o.get("agree"))
    return hits, total, (hits / total if total else 0.0)


def per_question(decisions: list[dict]) -> dict[str, dict]:
    """Accuracy and mean confidence for each question, across all scripts."""
    buckets: dict[str, list[dict]] = {}
    for d in decisions:
        for q in d.get("questions", []):
            buckets.setdefault(q["question"], []).append(q)

    summary = {}
    for key, outcomes in buckets.items():
        scored = gradable(outcomes)
        hits, total, acc = accuracy(scored)
        confidences = [o.get("confidence", 0.0) for o in scored]
        # Accuracy alone is misleading when the classes are unbalanced: a model
        # that always answers the majority class scores the base rate while
        # carrying no information at all. Reporting the two side by side is what
        # separates "usable" from "a constant in disguise".
        gold_counts: dict[str, int] = {}
        for o in scored:
            gold_counts[str(o.get("gold"))] = gold_counts.get(str(o.get("gold")), 0) + 1
        baseline = (max(gold_counts.values()) / total) if total else 0.0

        summary[key] = {
            "n": total,
            "ungraded": len(outcomes) - total,
            "majority_baseline": round(baseline, 4),
            "lift_over_baseline": round(acc - baseline, 4),
            "distinct_predictions": len({str(o.get("predicted")) for o in scored}),
            "correct": hits,
            "accuracy": round(acc, 4),
            "mean_confidence": round(sum(confidences) / total, 4) if total else 0.0,
            "verifiable": bool(outcomes and outcomes[0].get("verifiable")),
            # The gap between confidence and accuracy is the overconfidence.
            "overconfidence": round(
                (sum(confidences) / total - acc) if total else 0.0, 4
            ),
        }
    return summary


def confusion(decisions: list[dict], question: str, labels: tuple[str, ...]) -> dict:
    """Gold-vs-predicted counts for one categorical question."""
    matrix = {gold: {pred: 0 for pred in labels} for gold in labels}
    for d in decisions:
        for q in gradable(d.get("questions", [])):
            if q["question"] != question:
                continue
            gold, pred = str(q.get("gold")), str(q.get("predicted"))
            if gold in matrix and pred in matrix[gold]:
                matrix[gold][pred] += 1
    return matrix


def expected_calibration_error(outcomes: list[dict], bins: int = 5) -> dict:
    """ECE plus the reliability table it is computed from.

    Reported with the per-bin counts because at n=10 a single bin can hold two
    samples, and an ECE quoted without its support invites more confidence than
    the number deserves.
    """
    outcomes = gradable(outcomes)
    buckets: dict[int, list[dict]] = {}
    for o in outcomes:
        confidence = min(0.999999, max(0.0, float(o.get("confidence", 0.0))))
        buckets.setdefault(min(bins - 1, int(confidence * bins)), []).append(o)

    total = len(outcomes)
    table, ece = [], 0.0
    for b in range(bins):
        group = buckets.get(b, [])
        if not group:
            table.append({
                "bin": f"{b / bins:.1f}-{(b + 1) / bins:.1f}",
                "n": 0, "mean_confidence": None, "accuracy": None, "gap": None,
            })
            continue
        mean_confidence = sum(o.get("confidence", 0.0) for o in group) / len(group)
        _, _, acc = accuracy(group)
        gap = abs(mean_confidence - acc)
        ece += (len(group) / total) * gap
        table.append({
            "bin": f"{b / bins:.1f}-{(b + 1) / bins:.1f}",
            "n": len(group),
            "mean_confidence": round(mean_confidence, 4),
            "accuracy": round(acc, 4),
            "gap": round(gap, 4),
        })
    return {"ece": round(ece, 4), "n": total, "bins": table}


def brier_score(outcomes: list[dict]) -> float | None:
    """Mean squared error of the probability against the binary truth."""
    scored = gradable(outcomes)
    if not scored:
        return None
    total = 0.0
    for o in scored:
        probability = float(o.get("confidence", 0.0))
        # `confidence` is the top probability mass, so it is the probability
        # assigned to whatever was predicted.
        truth = 1.0 if o.get("agree") else 0.0
        total += (probability - truth) ** 2
    return round(total / len(scored), 4)


def coverage_curve(decisions: list[dict], thresholds=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)) -> list[dict]:
    """Accuracy of the answers that survive each confidence cut-off.

    The curve that actually answers "where do I set the threshold": every point
    trades how much of the backlog is handled automatically against how often
    that automatic answer is wrong.
    """
    all_outcomes = gradable([q for d in decisions for q in d.get("questions", [])])
    total = len(all_outcomes)
    curve = []
    for t in thresholds:
        kept = [o for o in all_outcomes if o.get("confidence", 0.0) >= t]
        hits, n, acc = accuracy(kept)
        curve.append({
            "threshold": t,
            "coverage": round(n / total, 4) if total else 0.0,
            "n_kept": n,
            "accuracy": round(acc, 4) if n else None,
            "errors": n - hits,
        })
    return curve


def latency_summary(decisions: list[dict]) -> dict:
    times = sorted(d.get("elapsed_ms", 0.0) for d in decisions if d.get("elapsed_ms"))
    if not times:
        return {}
    def pick(p: float) -> float:
        idx = min(len(times) - 1, int(round(p / 100.0 * len(times) + 0.5)) - 1)
        return round(times[max(0, idx)], 1)
    return {
        "n": len(times),
        "min_ms": round(times[0], 1),
        "p50_ms": pick(50),
        "p95_ms": pick(95),
        "max_ms": round(times[-1], 1),
        "total_s": round(sum(times) / 1000.0, 1),
        "mean_ms": round(sum(times) / len(times), 1),
    }


def outcome_counts(decisions: list[dict]) -> dict[str, int]:
    return dict(Counter(d.get("outcome", "?") for d in decisions))


def _ranks(values: list[float]) -> list[float]:
    """Ranks with ties averaged, so repeated rubric scores do not skew rho."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def spearman(a: list[float], b: list[float]) -> float | None:
    """Rank correlation between two series."""
    if len(a) != len(b) or len(a) < 3:
        return None
    ra, rb = _ranks(a), _ranks(b)
    n = len(a)
    mean_a, mean_b = sum(ra) / n, sum(rb) / n
    numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(ra, rb))
    denominator = (
        sum((x - mean_a) ** 2 for x in ra) * sum((y - mean_b) ** 2 for y in rb)
    ) ** 0.5
    return round(numerator / denominator, 4) if denominator else None


def ranking_signal(raw: dict, docs: dict, question: str = "migration_complexity") -> dict:
    """Does the model rank scripts by complexity even when its argmax is stuck?

    Argmax accuracy can read as "no signal at all" while the underlying
    distribution still orders the corpus correctly. That distinction decides
    what to do next: a model with no signal needs different features, whereas
    one that ranks but cannot place a boundary needs calibration — a far
    cheaper fix.
    """
    gold_points, expected, p_high, p_low = [], [], [], []
    for script_id, prediction in sorted(raw.items()):
        points = ((docs.get(script_id) or {}).get("gold") or {}).get("rubric_points")
        answer = (prediction.get("answers") or {}).get(question)
        if points is None or not answer:
            continue
        gold_points.append(float(points))
        expected.append(float(answer.get("value") or 0.0))
        probabilities = list((answer.get("probabilities") or {}).values())
        p_low.append(float(probabilities[0]) if probabilities else 0.0)
        p_high.append(float(probabilities[-1]) if probabilities else 0.0)

    if len(gold_points) < 3:
        return {}
    return {
        "n": len(gold_points),
        "rho_expected_score": spearman(gold_points, expected),
        "rho_p_high": spearman(gold_points, p_high),
        "rho_p_low": spearman(gold_points, p_low),
        "expected_score_range": [round(min(expected), 3), round(max(expected), 3)],
        "pairs": sorted(zip(gold_points, [round(e, 3) for e in expected])),
    }


def script_level_coverage(decisions: list[dict], questions: tuple[str, ...],
                          thresholds=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9)) -> list[dict]:
    """Per-script auto-triage rate, as opposed to per-answer accuracy.

    A script is only auto-triaged when *every* question about it clears the
    threshold, so the per-answer coverage curve badly overstates what can be
    automated: independent answers each clearing 85% still rarely clear it
    together. This is the conjunction the decision tree actually applies, and
    the gap between the two curves is the single most decision-relevant number
    in the study.
    """
    total = len(decisions)
    curve = []
    for t in thresholds:
        confident = correct_and_confident = 0
        for d in decisions:
            relevant = [
                q for q in gradable(d.get("questions", []))
                if q["question"] in questions
            ]
            if len(relevant) != len(questions):
                continue
            if all(q.get("confidence", 0.0) >= t for q in relevant):
                confident += 1
                if all(q.get("agree") for q in relevant):
                    correct_and_confident += 1
        curve.append({
            "threshold": t,
            "scripts_all_confident": confident,
            "coverage": round(confident / total, 4) if total else 0.0,
            "accuracy": round(correct_and_confident / confident, 4) if confident else None,
            "errors": confident - correct_and_confident,
        })
    return curve


def roc_auc(outcomes: list[dict]) -> float | None:
    """Probability that a true case outscores a false one.

    Accuracy answers "is the threshold right"; AUC answers "is the ranking
    right". They come apart badly here: a question can sit within noise of its
    majority-class baseline and still separate the classes almost perfectly,
    which means the model is informative and the 0.5 cut-off is not. Reporting
    only accuracy hid that, and reading it as "no information" was wrong.

    Below 0.5 is not absence of signal either — it is signal pointing the wrong
    way, which an inverted threshold would recover.
    """
    scored = [o for o in gradable(outcomes) if o.get("score") is not None]
    positive = [o["score"] for o in scored if o.get("gold_bool")]
    negative = [o["score"] for o in scored if not o.get("gold_bool")]
    if not positive or not negative:
        return None
    wins = sum(
        (p > n) + 0.5 * (p == n) for p in positive for n in negative
    )
    return round(wins / (len(positive) * len(negative)), 4)


def mcnemar(model_correct: list[bool], baseline_correct: list[bool]) -> dict:
    """Exact two-sided McNemar test of a model against a fixed baseline.

    Answers the question the accuracy table cannot: is this gap bigger than
    chance? Without it a two-point difference reads as a finding when it is a
    coin flip — which is exactly how the `multi_source` "-2%" was first
    reported.
    """
    from math import comb

    b = sum(1 for m, base in zip(model_correct, baseline_correct) if m and not base)
    c = sum(1 for m, base in zip(model_correct, baseline_correct) if base and not m)
    n = b + c
    if n == 0:
        return {"p_value": 1.0, "model_only": 0, "baseline_only": 0, "discordant": 0}
    k = min(b, c)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / (2 ** n))
    return {"p_value": round(p, 5), "model_only": b, "baseline_only": c,
            "discordant": n}


def wilson_interval(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — usable at the small n this study reports.

    A headline of "8 scripts, zero errors" needs its interval attached: with
    n=8 the true error rate can still be well over a third.
    """
    if n == 0:
        return (0.0, 1.0)
    p = hits / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    spread = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denominator
    return (round(max(0.0, centre - spread), 4), round(min(1.0, centre + spread), 4))


def binary_diagnostics(decisions: list[dict], question: str) -> dict:
    """AUC and a significance test for one binary question."""
    outcomes = [
        q for d in decisions for q in gradable(d.get("questions", []))
        if q["question"] == question and isinstance(q.get("gold"), bool)
    ]
    if not outcomes:
        return {}

    enriched = []
    for o in outcomes:
        # P(true) is recoverable from the top probability and the label taken.
        confidence = float(o.get("confidence", 0.0))
        p_true = confidence if o.get("predicted") else 1.0 - confidence
        enriched.append({**o, "score": p_true, "gold_bool": bool(o["gold"]),
                         "gradable": True})

    golds = [e["gold_bool"] for e in enriched]
    majority = sum(golds) / len(golds) >= 0.5
    model_correct = [bool(e.get("agree")) for e in enriched]
    baseline_correct = [g == majority for g in golds]

    hits = sum(model_correct)
    return {
        "n": len(enriched),
        "auc": roc_auc(enriched),
        "accuracy": round(hits / len(enriched), 4),
        "accuracy_ci95": wilson_interval(hits, len(enriched)),
        "baseline": round(sum(baseline_correct) / len(enriched), 4),
        "mcnemar": mcnemar(model_correct, baseline_correct),
        "best_threshold": best_threshold(enriched),
        "holdout": threshold_holdout(enriched),
    }

def best_threshold(outcomes: list[dict]) -> dict:
    """The threshold that would maximise accuracy, and what it would buy.

    Fitted on the very data it is scored against, so it is an OPTIMISTIC UPPER
    BOUND, not a deployable setting — quoting it without a hold-out would repeat
    the mistake this study is trying to avoid. Its value is diagnostic: a large
    gap between accuracy at 0.5 and accuracy here means the model ranks well and
    is merely mis-centred, which is a calibration problem rather than a
    capability one.
    """
    scored = [o for o in outcomes if o.get("score") is not None]
    if not scored:
        return {}
    points = [(o["score"], bool(o["gold_bool"])) for o in scored]
    candidates = sorted({p for p, _ in points} | {0.0, 1.0})

    best = {"accuracy": 0.0, "threshold": 0.5, "inverted": False}
    for threshold in candidates:
        for inverted in (False, True):
            hits = sum(
                ((score >= threshold) != inverted) == gold for score, gold in points
            )
            accuracy = hits / len(points)
            if accuracy > best["accuracy"]:
                best = {"accuracy": round(accuracy, 4),
                        "threshold": round(threshold, 4),
                        "inverted": inverted}
    return best


def threshold_holdout(outcomes: list[dict], *, repeats: int = 500,
                      seed: int = 42, train_fraction: float = 0.5) -> dict:
    """Fit the decision threshold on one half, score it on the other.

    `best_threshold` reports what the cut-off *could* buy if chosen with
    hindsight; it is fitted and scored on the same rows, so it is an upper
    bound. This is the deployable version: repeated stratified splits, the
    threshold chosen only on the training half, accuracy measured only on the
    held-out half. The gap between the two numbers is how much of the
    "calibration fixes it" story was hindsight.

    Stratified so that a split cannot land with one class missing from a half,
    which at n=99 with a 15% positive rate is otherwise common.
    """
    import random

    scored = [o for o in outcomes if o.get("score") is not None]
    positives = [o for o in scored if o["gold_bool"]]
    negatives = [o for o in scored if not o["gold_bool"]]
    if len(positives) < 4 or len(negatives) < 4:
        return {}

    rng = random.Random(seed)
    test_accuracies, chosen = [], []

    for _ in range(repeats):
        train, test = [], []
        for group in (positives, negatives):
            shuffled = list(group)
            rng.shuffle(shuffled)
            cut = max(2, round(len(shuffled) * train_fraction))
            train.extend(shuffled[:cut])
            test.extend(shuffled[cut:])
        if not test:
            continue

        fitted = best_threshold(train)
        threshold, inverted = fitted["threshold"], fitted["inverted"]
        hits = sum(
            ((o["score"] >= threshold) != inverted) == o["gold_bool"] for o in test
        )
        test_accuracies.append(hits / len(test))
        chosen.append(threshold)

    if not test_accuracies:
        return {}

    ordered = sorted(test_accuracies)
    mean = sum(ordered) / len(ordered)
    default = sum((o["score"] >= 0.5) == o["gold_bool"] for o in scored) / len(scored)
    optimistic = best_threshold(scored)

    return {
        "repeats": len(ordered),
        "test_accuracy_mean": round(mean, 4),
        "test_accuracy_p05": round(ordered[int(0.05 * len(ordered))], 4),
        "test_accuracy_p95": round(ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))], 4),
        "threshold_median": round(sorted(chosen)[len(chosen) // 2], 4),
        "threshold_spread": [round(min(chosen), 4), round(max(chosen), 4)],
        "accuracy_at_half": round(default, 4),
        "optimistic_accuracy": optimistic["accuracy"],
        # How much of the apparent gain was hindsight rather than signal.
        "hindsight_gap": round(optimistic["accuracy"] - mean, 4),
        "gain_over_default": round(mean - default, 4),
    }
