"""Export a client's labelled corpus in the shape Laya's fine-tune notebook eats.

The notebook reads three JSON columns per case — `state`, `questions`, `gold` —
where gold is ``{qid: {"label": ..., "probabilities": {...}}}``. This builds
that from the evidence cards and labels already in `state/`.

Two things here are not bookkeeping, and both come from mistakes this study
made:

**Splitting by family, not at random.** This corpus contains near-identical
queries (TPC-DS q33 / q56 / q60 differ only in a grouping column). A random
split puts one in train and its twin in test, and the reported accuracy is
partly memorisation. Client backlogs are worse — the same report copied per
region, per year, per business unit. Scripts are grouped by a structural
fingerprint and whole groups go to one side of the split.

**Reserving a calibration slice.** The notebook fits output temperatures on a
held-out set at the end, which is what makes the confidences mean anything.
Skipping it reproduces the shipped checkpoint's own warning — that its
confidences are uncalibrated — in your own model.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

# Structural signature used to group near-duplicates. Deliberately coarse: two
# scripts with the same shape and the same sources are treated as one family
# even if their filters differ.
FAMILY_KEYS = (
    "source_tables", "subquery_count", "cte_count", "window_function_count",
    "set_operation_count", "max_nesting_depth", "graph_edges", "statements",
)

DEFAULT_SPLIT = {"train": 0.70, "calibration": 0.10, "test": 0.20}


def family_key(features: dict) -> str:
    """A fingerprint that near-identical scripts share."""
    parts = [f"{k}={features.get(k, 0)}" for k in FAMILY_KEYS]
    parts.append("sources=" + ",".join(sorted(features.get("distinct_sources") or [])))
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:12]


def build_case(doc: dict, questions: dict, labels: dict) -> dict | None:
    """One training row: state, the questions asked, and the gold answers."""
    card = doc.get("evidence_card") or {}
    state = {
        "purpose": card.get("purpose") or "",
        "structure": card.get("structure") or "",
        "metrics": card.get("facts") or "",
    }
    if not any(state.values()):
        return None

    gold = {}
    for qid, question in questions.items():
        value = labels.get(qid)
        if value is None:
            continue
        kind = question.get("type")
        if kind == "noul":
            truth = bool(value)
            gold[qid] = {"label": "true" if truth else "false",
                         "probabilities": {"true": 1.0 if truth else 0.0,
                                           "false": 0.0 if truth else 1.0}}
        elif kind == "choice":
            options = list(question.get("criteria") or {})
            if value not in options:
                continue
            gold[qid] = {"label": value,
                         "probabilities": {o: (1.0 if o == value else 0.0)
                                           for o in options}}
        elif kind == "score":
            levels = list(question.get("criteria") or [])
            index = _score_index(value, levels)
            if index is None:
                continue
            gold[qid] = {"label": index,
                         "probabilities": {str(i): (1.0 if i == index else 0.0)
                                           for i in range(len(levels))}}
    if not gold:
        return None

    return {
        "id": doc.get("id"),
        "origin": doc.get("name"),
        "family": family_key(doc.get("features") or {}),
        "state": json.dumps(state, ensure_ascii=False),
        "questions": json.dumps(questions, ensure_ascii=False),
        "gold": json.dumps(gold, ensure_ascii=False),
    }


_BAND_ORDER = ("low", "medium", "high")


def _score_index(value, levels: list[str]) -> int | None:
    if isinstance(value, int) and 0 <= value < len(levels):
        return value
    if isinstance(value, str):
        if value in _BAND_ORDER and len(levels) == len(_BAND_ORDER):
            return _BAND_ORDER.index(value)
        for i, level in enumerate(levels):
            if level.lower().startswith(value.lower()):
                return i
    return None


def split_by_family(cases: list[dict], fractions: dict[str, float] | None = None,
                    seed: int = 42) -> dict[str, list[dict]]:
    """Assign whole families to one split, never splitting a family.

    Random row-level splitting leaks: a near-duplicate in train makes its twin
    in test easy for the wrong reason, and the reported accuracy is partly
    memorisation of the family rather than a learnt rule.
    """
    fractions = fractions or DEFAULT_SPLIT
    families: dict[str, list[dict]] = {}
    for case in cases:
        families.setdefault(case["family"], []).append(case)

    # Biggest families placed first, each into whichever split is furthest below
    # its quota — otherwise one large family can swamp a small split entirely.
    ordered = sorted(families.values(), key=lambda g: (-len(g), g[0]["family"]))
    rng = random.Random(seed)
    rng.shuffle(ordered)
    ordered.sort(key=len, reverse=True)

    total = len(cases)
    out: dict[str, list[dict]] = {name: [] for name in fractions}
    for group in ordered:
        target = min(
            out, key=lambda name: len(out[name]) - fractions[name] * total
        )
        out[target].extend(group)
    return out


def write_jsonl(rows: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def report(splits: dict[str, list[dict]], questions: dict) -> dict:
    """What to check before spending GPU time on this dataset."""
    families = {name: {c["family"] for c in rows} for name, rows in splits.items()}
    overlap = {}
    names = list(splits)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = families[a] & families[b]
            if shared:
                overlap[f"{a}~{b}"] = len(shared)

    per_question: dict[str, dict[str, int]] = {}
    for rows in splits.values():
        for case in rows:
            for qid, answer in json.loads(case["gold"]).items():
                bucket = per_question.setdefault(qid, {})
                key = str(answer["label"])
                bucket[key] = bucket.get(key, 0) + 1

    decisions = sum(len(json.loads(c["gold"])) for rows in splits.values() for c in rows)
    return {
        "cases": {name: len(rows) for name, rows in splits.items()},
        "decisions_total": decisions,
        "families": {name: len(f) for name, f in families.items()},
        # Must be empty: a shared family across splits is leakage.
        "family_overlap": overlap,
        "label_counts": per_question,
        # Reference scale from Laya's own notebook: 1,200 cases / 6,000 decisions.
        "reference_scale": {"cases": 1200, "decisions": 6000},
    }
