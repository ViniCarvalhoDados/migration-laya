"""Objective complexity scoring.

The score is a sum of points over deterministic features, and it is the gold
label for ``migration_complexity``. No model is involved, so a disagreement with
Laya is always attributable to one side or the other.

Thresholds are not hand-picked: ``mlaya census --emit-rubric`` derives them from
percentiles of the corpus itself and writes them to ``config/rubric.yml``,
recording which percentile produced each number. That turns "why 40 lines?" into
"why the 66th percentile?", which is a question the team can actually answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Features scored by threshold, with the percentile used for each tier. Order is
# the order they appear in the report.
SCORED_FEATURES: tuple[tuple[str, str, str | None], ...] = (
    # (feature path, lower percentile, upper percentile or None for one tier)
    ("loc_code", "p66", "p90"),
    ("source_tables", "p66", "p90"),
    ("subquery_count", "p50", "p90"),
    ("cte_count", "p50", "p90"),
    ("window_function_count", "p66", None),
    ("set_operation_count", "p66", "p90"),
    ("max_nesting_depth", "p66", None),
    ("case_expression_count", "p66", "p90"),
    ("join_graph.edges", "p66", "p90"),
    ("join_graph.max_degree", "p90", None),
    ("join_graph.max_scope_sources", "p66", "p90"),
)

# Conditions worth a flat point regardless of distribution, because each one is
# a qualitative migration hazard rather than a matter of degree.
FLAT_RULES: tuple[tuple[str, str], ...] = (
    ("multi_statement", "more than one statement in the file"),
    ("cross_join_risk", "a source in some scope joins to nothing"),
    ("nonportable_syntax", "engine-specific syntax detected"),
    ("correlated_subquery", "correlated subquery present"),
)


def get_path(data: dict, path: str) -> Any:
    """Read ``a.b`` out of a nested dict, returning 0 when absent."""
    node: Any = data
    for part in path.split("."):
        if not isinstance(node, dict):
            return 0
        node = node.get(part, 0)
    return node if node is not None else 0


@dataclass
class Score:
    points: int = 0
    band: str = ""
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"points": self.points, "band": self.band, "reasons": list(self.reasons)}


def load_rubric(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def score_features(features: dict, rubric: dict) -> Score:
    """Score one feature dict against a rubric config."""
    score = Score()

    for entry in rubric.get("thresholds", []):
        name = entry["feature"]
        value = get_path(features, name)
        if not isinstance(value, (int, float)):
            continue
        upper, lower = entry.get("upper"), entry.get("lower")
        if upper is not None and value >= upper:
            score.points += 2
            score.reasons.append(f"{name}={value} >= {upper} (+2)")
        elif lower is not None and value >= lower:
            score.points += 1
            score.reasons.append(f"{name}={value} >= {lower} (+1)")

    flat = rubric.get("flat_rules", {})
    for name, points in flat.items():
        if _flat_rule_fires(name, features):
            score.points += int(points)
            score.reasons.append(f"{name} (+{points})")

    score.band = band_for(score.points, rubric)
    return score


def _flat_rule_fires(name: str, f: dict) -> bool:
    if name == "multi_statement":
        return get_path(f, "statements") > 1
    if name == "cross_join_risk":
        return get_path(f, "join_graph.cross_join_risk") > 0
    if name == "nonportable_syntax":
        return bool(f.get("nonportable_markers"))
    if name == "correlated_subquery":
        return get_path(f, "correlated_subquery_count") > 0
    return False


def band_for(points: int, rubric: dict) -> str:
    for name, (low, high) in rubric.get("bands", {}).items():
        if points >= low and (high is None or points <= high):
            return name
    return "high"


BAND_ORDER = ("low", "medium", "high")


def band_distance(a: str, b: str) -> int:
    """How many tiers apart two bands are; 99 if either is unrecognised."""
    try:
        return abs(BAND_ORDER.index(a) - BAND_ORDER.index(b))
    except ValueError:
        return 99
