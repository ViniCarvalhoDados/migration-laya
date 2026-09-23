"""Prompt-sensitivity probe: how much of a result is the wording?

Reformulating one question during this study moved its AUC from 0.84 to 0.95,
which made every other conclusion suspect: only one phrasing per question had
ever been tried. This asks each question three ways in a single call — so
run-to-run variance cannot be mistaken for a wording effect — and reports two
things:

* **paraphrase sensitivity** — |AUC(v1) - AUC(v2)| for two wordings of the same
  question. A model that reads should barely move; a model matching keywords
  moves a lot.
* **the negation test** — v3 asks the opposite. A model that reads the sentence
  should roughly invert: AUC(v3) ~= 1 - AUC(v1). One that answers from keywords
  alone answers v3 the way it answered v1, and its AUC stays on the same side
  of 0.5. This prediction is registered in `config/questions_variants.yml`
  before the run.
"""

from __future__ import annotations

from . import metrics

# How close the negated AUC has to land to its prediction to count as inverted.
INVERSION_TOLERANCE = 0.15


def analyse(raw: dict, docs: dict, questions: list[str],
            variants: tuple[str, ...] = ("v1", "v2", "v3")) -> list[dict]:
    names = sorted(n for n in raw if n in docs)
    out = []

    for question in questions:
        gold = [bool((docs[n].get("gold") or {})[question]) for n in names]
        measured = {}
        for variant in variants:
            key = f"{question}_{variant}"
            answers = [(raw[n].get("answers") or {}).get(key) for n in names]
            if any(a is None for a in answers):
                measured = {}
                break
            scores = [float(a.get("value") or 0.0) for a in answers]
            measured[variant] = {
                "auc": metrics.roc_auc([
                    {"score": s, "gold_bool": g, "gradable": True}
                    for s, g in zip(scores, gold)
                ]),
                "mean_p_true": round(sum(scores) / len(scores), 4),
                "accuracy_at_half": round(
                    sum((s >= 0.5) == g for s, g in zip(scores, gold)) / len(gold), 4),
            }
        if not measured:
            continue

        first, second, negated = (measured.get(v) for v in variants)
        record = {
            "question": question,
            "n": len(names),
            "gold_positive_rate": round(sum(gold) / len(gold), 4),
            **{v: measured[v] for v in measured},
        }
        if first and second and first["auc"] is not None and second["auc"] is not None:
            record["paraphrase_shift"] = round(abs(first["auc"] - second["auc"]), 4)
        if first and negated and first["auc"] is not None and negated["auc"] is not None:
            predicted = round(1.0 - first["auc"], 4)
            record["negation"] = {
                "predicted_auc": predicted,
                "observed_auc": negated["auc"],
                "inverted": abs(negated["auc"] - predicted) <= INVERSION_TOLERANCE,
            }
        out.append(record)
    return out


def summarise(rows: list[dict]) -> dict:
    shifts = [r["paraphrase_shift"] for r in rows if "paraphrase_shift" in r]
    negations = [r["negation"] for r in rows if "negation" in r]
    return {
        "questions": len(rows),
        "mean_paraphrase_shift": round(sum(shifts) / len(shifts), 4) if shifts else None,
        "max_paraphrase_shift": round(max(shifts), 4) if shifts else None,
        "inverted_under_negation": sum(1 for n in negations if n["inverted"]),
        "failed_to_invert": sum(1 for n in negations if not n["inverted"]),
    }
