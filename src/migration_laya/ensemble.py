"""Does averaging over paraphrases recover the signal that wording destroys?

The variants probe left the study in an awkward place: rewording a question
moved its AUC by 0.28 on average, so every single-wording result here — the
good ones included — sat inside the noise of how the sentence happened to be
written. That is not a fixable-by-arguing problem; either aggregating over
several wordings is stable, or no number from this setup can be trusted.

What is compared, per question:

* **single paraphrases** — the AUC of each wording on its own, reported as a
  spread. This is the size of the problem.
* **mean / median / trimmed** — aggregations over the six wordings. None of
  these look at the gold label, so they are honest and deployable.
* **oracle** — the single best wording, *chosen on the gold*. It is a ceiling,
  not a strategy, and is labelled as such everywhere it appears.

The test that matters is whether an honest aggregation lands near the top of
the single-wording spread. If it does, you no longer have to guess the lucky
phrasing. If it lands near the middle, aggregation buys nothing and the
sensitivity is fatal.
"""

from __future__ import annotations

from . import metrics

# Fraction trimmed from each end before averaging, for the trimmed variant.
TRIM = 1


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _trimmed(values: list[float], trim: int = TRIM) -> float:
    ordered = sorted(values)
    if len(ordered) > 2 * trim:
        ordered = ordered[trim:len(ordered) - trim]
    return _mean(ordered)


AGGREGATORS = {
    "mean": _mean,
    "median": _median,
    "trimmed": _trimmed,
}


def _auc(scores: list[float], gold: list[bool]) -> float | None:
    return metrics.roc_auc([
        {"score": s, "gold_bool": g, "gradable": True}
        for s, g in zip(scores, gold)
    ])


def analyse(raw: dict, docs: dict, question: str,
            paraphrases: list[str]) -> dict:
    """Compare every single wording against aggregations over all of them."""
    names = sorted(n for n in raw if n in docs)
    gold = [bool((docs[n].get("gold") or {})[question]) for n in names]

    per_wording: dict[str, list[float]] = {}
    for key in paraphrases:
        answers = [(raw[n].get("answers") or {}).get(key) for n in names]
        if any(a is None for a in answers):
            return {}
        per_wording[key] = [float(a.get("value") or 0.0) for a in answers]

    singles = {}
    for key, scores in per_wording.items():
        singles[key] = {
            "auc": _auc(scores, gold),
            "mean_p_true": round(_mean(scores), 4),
        }
    single_aucs = [v["auc"] for v in singles.values() if v["auc"] is not None]

    aggregated = {}
    for name, fn in AGGREGATORS.items():
        combined = [
            fn([per_wording[key][i] for key in paraphrases])
            for i in range(len(names))
        ]
        auc = _auc(combined, gold)
        holdout = metrics.threshold_holdout([
            {"score": s, "gold_bool": g} for s, g in zip(combined, gold)
        ])
        aggregated[name] = {
            "auc": auc,
            "accuracy_at_half": round(
                sum((s >= 0.5) == g for s, g in zip(combined, gold)) / len(gold), 4),
            "holdout_accuracy": holdout.get("test_accuracy_mean"),
        }

    return {
        "question": question,
        "n": len(names),
        "n_paraphrases": len(paraphrases),
        "gold_positive_rate": round(sum(gold) / len(gold), 4),
        "single": singles,
        "single_auc_min": round(min(single_aucs), 4) if single_aucs else None,
        "single_auc_max": round(max(single_aucs), 4) if single_aucs else None,
        "single_auc_mean": round(_mean(single_aucs), 4) if single_aucs else None,
        "single_auc_spread": round(max(single_aucs) - min(single_aucs), 4)
        if single_aucs else None,
        "aggregated": aggregated,
        # Chosen with the gold label in hand: a ceiling, never a strategy.
        "oracle_auc": round(max(single_aucs), 4) if single_aucs else None,
    }


def verdict(row: dict, tolerance: float = 0.03) -> str:
    """Did honest aggregation buy back what wording sensitivity cost?"""
    best = (row.get("aggregated") or {}).get("mean", {}).get("auc")
    if best is None or row.get("single_auc_max") is None:
        return "indeterminado"
    if best >= row["single_auc_max"] - tolerance:
        return "agregar resolve"
    if best >= row["single_auc_mean"] + tolerance:
        return "agregar ajuda"
    return "agregar nao ajuda"
