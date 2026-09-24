"""Paired comparison: Laya against the logistic regression, treated equally.

This module exists because the first version of the comparison was not fair in
the direction it appeared to be.

E6 was unfair *to Laya*: its probabilities were cut at a fixed 0.5 while the
regression's came out calibrated by the fit. E8 fixed that by fitting both on a
training half and scoring both on the held-out half.

An external audit then found the opposite unfairness. E8 and E10 compared Laya
against the **clean** regression — the one with the label-defining features
removed. But the evidence card Laya reads *contains those very facts*
(``subqueries=0``, ``window_fns=2``). So the card was being compared against a
model deliberately blinded to what the card says. The gap that produced is a
measure of the handicap, not of the model.

So both variants are reported side by side, always:

* **clean** — the honest floor. "Can a few lines of arithmetic do this *without*
  being handed the answer?"
* **leaky** — the like-for-like arm. Same information as the card, so this is
  the number that says whether Laya earns its 421M parameters.

Protocol, identical for every arm: stratified split, fit on the training half
only, score on the held-out half only, repeat. Laya's "fit" is its decision
threshold; the regression's is its coefficients; the majority baseline's is
which class is larger. Nothing sees the test half.

No p-value is reported, on purpose: the test halves overlap across splits, so a
paired test over them would be anticonservative. The spread across splits and
the win rate are the honest summaries.
"""

from __future__ import annotations

import random

import numpy as np

from . import baseline as lr

DEFAULT_SPLITS = 200
DEFAULT_SEED = 42
TRAIN_FRACTION = 0.5


def _design(docs: dict, question: str, *, drop_leaky: bool):
    """Feature matrix, labels and ids for one question, in a stable id order."""
    leaky = set(lr.LEAKY.get(question, ()))
    names = tuple(f for f in lr.FEATURES if not (drop_leaky and f in leaky))

    rows, labels, ids = [], [], []
    for script_id, doc in sorted(docs.items()):
        gold = (doc.get("gold") or {}).get(question)
        if not isinstance(gold, bool):
            continue
        rows.append(lr.feature_vector(doc.get("features") or {}, names))
        labels.append(bool(gold))
        ids.append(script_id)
    return np.asarray(rows, dtype=float), labels, ids, names


def _best_threshold(scores: list[float], gold: list[bool]) -> tuple[float, bool]:
    """Threshold and polarity that maximise accuracy on these rows only."""
    candidates = sorted({round(s, 4) for s in scores} | {0.5})
    best, best_hits = (0.5, False), -1
    for threshold in candidates:
        for inverted in (False, True):
            hits = sum(((s >= threshold) != inverted) == g
                       for s, g in zip(scores, gold))
            if hits > best_hits:
                best_hits, best = hits, (threshold, inverted)
    return best


def _stratified_split(positives: list[int], negatives: list[int],
                      rng: random.Random, train_fraction: float):
    train, test = [], []
    for group in (positives, negatives):
        shuffled = list(group)
        rng.shuffle(shuffled)
        cut = max(2, round(len(shuffled) * train_fraction))
        train.extend(shuffled[:cut])
        test.extend(shuffled[cut:])
    return train, test


def _summary(values: list[float]) -> dict:
    # numpy scalars leak in from the regression arm and cannot be serialised.
    ordered = sorted(float(v) for v in values)
    n = len(ordered)
    return {
        "mean": round(sum(ordered) / n, 4),
        "p05": round(ordered[int(0.05 * n)], 4),
        "p95": round(ordered[min(n - 1, int(0.95 * n))], 4),
    }


def compare(docs: dict, question: str, laya_scores: dict[str, float], *,
            splits: int = DEFAULT_SPLITS, seed: int = DEFAULT_SEED,
            train_fraction: float = TRAIN_FRACTION) -> dict:
    """Run the paired protocol for one binary question.

    `laya_scores` maps script id to P(true). Scripts without a Laya score or
    without a boolean gold label are dropped from every arm alike, so the arms
    stay comparable.
    """
    matrices, labels, ids = {}, None, None
    for variant, drop in (("clean", True), ("leaky", False)):
        rows, these_labels, these_ids, _ = _design(docs, question,
                                                   drop_leaky=drop)
        if len(these_ids) < 12:
            return {}
        matrices[variant] = rows
        labels, ids = these_labels, these_ids

    keep = [i for i, script_id in enumerate(ids) if script_id in laya_scores]
    if len(keep) < 12:
        return {}
    labels = [labels[i] for i in keep]
    scores = [float(laya_scores[ids[i]]) for i in keep]
    matrices = {v: m[keep] for v, m in matrices.items()}
    if len(set(labels)) < 2:
        return {}

    scaled = {v: lr._standardise(m) for v, m in matrices.items()}
    label_array = np.asarray(labels, dtype=float)

    positives = [i for i, g in enumerate(labels) if g]
    negatives = [i for i, g in enumerate(labels) if not g]
    if len(positives) < 4 or len(negatives) < 4:
        return {}

    rng = random.Random(seed)
    arms = {"laya": [], "lr_clean": [], "lr_leaky": [], "majority": []}

    for _ in range(splits):
        train, test = _stratified_split(positives, negatives, rng,
                                        train_fraction)
        if not test:
            continue
        test_gold = [labels[i] for i in test]

        # Laya: the threshold is the only thing fitted, and only on train.
        threshold, inverted = _best_threshold([scores[i] for i in train],
                                              [labels[i] for i in train])
        arms["laya"].append(
            sum(((scores[i] >= threshold) != inverted) == labels[i]
                for i in test) / len(test))

        # Regression: coefficients fitted on train, scored on test.
        for variant in ("clean", "leaky"):
            matrix = scaled[variant]
            model = lr.fit(matrix[train], label_array[train])
            predicted = lr.predict_proba(model, matrix[test])
            arms[f"lr_{variant}"].append(
                float(sum(bool(p >= 0.5) == g
                          for p, g in zip(predicted, test_gold)) / len(test)))

        # Majority class, also chosen only on train.
        train_gold = [labels[i] for i in train]
        call = sum(train_gold) * 2 >= len(train_gold)
        arms["majority"].append(
            sum(g == call for g in test_gold) / len(test_gold))

    if not arms["laya"]:
        return {}

    result = {
        "question": question,
        "n": len(labels),
        "splits": len(arms["laya"]),
        "gold_positive_rate": round(sum(labels) / len(labels), 4),
        "accuracy": {arm: _summary(values) for arm, values in arms.items()},
        "differences": {},
    }
    for arm in ("lr_clean", "lr_leaky", "majority"):
        deltas = [a - b for a, b in zip(arms["laya"], arms[arm])]
        summary = _summary(deltas)
        summary["win_rate"] = round(
            sum(d > 0 for d in deltas) / len(deltas), 4)
        summary["verdict"] = _verdict(summary)
        result["differences"][f"laya_minus_{arm}"] = summary
    return result


def _verdict(summary: dict) -> str:
    """Only a spread that clears zero is called a win or a loss."""
    if summary["p05"] > 0:
        return "vence"
    if summary["p95"] < 0:
        return "perde"
    return "empate"


def aggregate_scores(raw: dict, docs: dict, question: str,
                     paraphrases: list[str] | None = None) -> dict[str, float]:
    """P(true) per script id: one wording, or the mean over several.

    Answers are matched to the gold by **origin query**, not by the sequential
    script id — the id is reassigned when the sample size changes, and matching
    on it silently scores an old run against the wrong labels.

    Averaging the paraphrases is the E10 ensemble, and it never looks at the
    gold label: the aggregation is fixed before any scoring.
    """
    keys = paraphrases or [question]
    by_origin = {d.get("name"): d for d in docs.values() if d.get("name")}

    out: dict[str, float] = {}
    for script_id, prediction in raw.items():
        origin = prediction.get("origin")
        doc = by_origin.get(origin) if origin else docs.get(script_id)
        if not doc:
            continue
        answers = prediction.get("answers") or {}
        values = [answers[k].get("value") for k in keys if k in answers]
        values = [float(v) for v in values if v is not None]
        if len(values) != len(keys):
            continue
        out[doc["id"]] = sum(values) / len(values)
    return out
