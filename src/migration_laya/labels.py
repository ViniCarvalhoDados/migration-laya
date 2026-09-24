"""Derive `rewrite_strategy` labels from a migration that already happened.

This is the piece that makes a client fine-tune worth doing at all.

Every label in the discovery study was my opinion, which is why a logistic
regression could reproduce it from the same AST features it was implicitly
derived from. A fine-tune trained on that gold would learn my opinion — an
expensive way to reimplement the extractor.

A finished migration does not have that problem. The client already decided,
script by script, how much each one had to change, and the decision is recorded
in the diff between the legacy file and the migrated one. Comparing the two
ASTs recovers the label from *what was actually done*, not from what anyone
thinks should be done.

The rules below are deliberately coarse and auditable — a migration lead should
be able to read them, disagree with a specific case, and correct it. They are a
starting point for labelling, not a replacement for review.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

from .features import extract_features, Features

# Structural counts that decide whether the shape of the query changed. Purely
# cosmetic differences (aliases, whitespace, literal values, dialect syntax) do
# not move any of these.
SHAPE = (
    "subquery_count", "correlated_subquery_count", "derived_table_count",
    "cte_count", "window_function_count", "set_operation_count",
    "max_nesting_depth", "statements",
)

STRATEGIES = ("lift_and_shift", "refactor", "redesign", "manual_rewrite")


@dataclass
class Derivation:
    name: str
    strategy: str
    confidence: str          # high | medium | low — how safe the rule was here
    reasons: list[str]
    shape_changes: dict[str, tuple[int, int]]
    sources_added: list[str]
    sources_removed: list[str]
    parse_ok: bool

    def as_dict(self) -> dict:
        return asdict(self)


def _shape_diff(before: Features, after: Features) -> dict[str, tuple[int, int]]:
    out = {}
    for key in SHAPE:
        b, a = getattr(before, key, 0), getattr(after, key, 0)
        if b != a:
            out[key] = (b, a)
    return out


def derive(legacy_path: str | Path, migrated_path: str | Path) -> Derivation:
    """Label one migrated script by comparing it to its legacy original."""
    before = extract_features(legacy_path)
    after = extract_features(migrated_path)
    name = Path(legacy_path).stem

    if not (before.parse_ok and after.parse_ok):
        return Derivation(
            name=name, strategy="manual_rewrite", confidence="low",
            reasons=["one side did not parse; a human has to classify this one"],
            shape_changes={}, sources_added=[], sources_removed=[],
            parse_ok=False,
        )

    before_sources, after_sources = set(before.distinct_sources), set(after.distinct_sources)
    added = sorted(after_sources - before_sources)
    removed = sorted(before_sources - after_sources)
    shape = _shape_diff(before, after)
    reasons: list[str] = []

    # The data the query reads changed: this is not a translation any more.
    if added or removed:
        if added:
            reasons.append(f"passou a ler {', '.join(added)}")
        if removed:
            reasons.append(f"deixou de ler {', '.join(removed)}")
        # Replacing most of the sources means the query was rebuilt, not ported.
        churn = len(added) + len(removed)
        strategy = "redesign" if churn <= len(before_sources) else "manual_rewrite"
        return Derivation(
            name=name, strategy=strategy,
            confidence="high" if churn > 1 else "medium",
            reasons=reasons, shape_changes=shape,
            sources_added=added, sources_removed=removed, parse_ok=True,
        )

    if shape:
        for key, (b, a) in sorted(shape.items()):
            reasons.append(f"{key}: {b} -> {a}")
        # Many simultaneous shape changes read as a rewrite rather than a tidy-up.
        strategy = "redesign" if len(shape) >= 4 else "refactor"
        return Derivation(
            name=name, strategy=strategy,
            confidence="high" if len(shape) >= 2 else "medium",
            reasons=reasons, shape_changes=shape,
            sources_added=[], sources_removed=[], parse_ok=True,
        )

    # Same sources, same shape. Whatever changed was dialect or cosmetics.
    dialect_moved = before.parse_dialect != after.parse_dialect
    markers = sorted(set(before.nonportable_markers) ^ set(after.nonportable_markers))
    if dialect_moved:
        reasons.append(f"dialeto {before.parse_dialect} -> {after.parse_dialect}")
    if markers:
        reasons.append("sintaxe específica alterada: " + ", ".join(markers[:4]))
    if not reasons:
        reasons.append("nenhuma diferença estrutural detectável")

    return Derivation(
        name=name, strategy="lift_and_shift",
        confidence="high" if (dialect_moved or markers) else "medium",
        reasons=reasons, shape_changes={}, sources_added=[], sources_removed=[],
        parse_ok=True,
    )


def derive_many(pairs: list[tuple[str, str]]) -> list[Derivation]:
    return [derive(legacy, migrated) for legacy, migrated in pairs]


def summarise(rows: list[Derivation]) -> dict:
    """Counts a migration lead needs before trusting a derived label set."""
    by_strategy: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for row in rows:
        by_strategy[row.strategy] = by_strategy.get(row.strategy, 0) + 1
        by_confidence[row.confidence] = by_confidence.get(row.confidence, 0) + 1
    needs_review = [r.name for r in rows if r.confidence == "low"]
    return {
        "n": len(rows),
        "by_strategy": by_strategy,
        "by_confidence": by_confidence,
        "needs_human_review": needs_review,
        # A class with almost no examples cannot be learnt, and a fine-tune that
        # never sees it will never predict it.
        "thin_classes": [s for s in STRATEGIES if by_strategy.get(s, 0) < 20],
    }
