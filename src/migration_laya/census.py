"""Corpus census: run the deterministic extractor over every script.

This is step zero of the study and it stands on its own. It produces the
reference distribution the rubric's thresholds are derived from, the ground
truth the Laya answers are graded against, and a profile of the corpus that is
useful even if Laya turns out to be unsuitable.
"""

from __future__ import annotations

import csv
import json
import statistics
from datetime import date
from pathlib import Path

import yaml

from .features import extract_features, Features
from .rubric import SCORED_FEATURES, FLAT_RULES, get_path, score_features

PERCENTILES = (25, 33, 50, 66, 75, 90, 95)

# Columns written to the census CSV, in order. List-valued features are joined
# with "|" so the file stays a flat table.
CSV_COLUMNS = (
    "name", "parse_ok", "parse_dialect", "loc", "loc_code", "chars", "statements",
    "cte_count", "cte_max_depth", "subquery_count", "scalar_subquery_count",
    "correlated_subquery_count", "derived_table_count", "max_nesting_depth",
    "scope_count", "window_function_count", "distinct_window_specs",
    "aggregate_count", "has_having", "has_distinct", "has_order_by",
    "source_tables", "table_references", "cte_references", "set_operation_count", "union_all_count",
    "intersect_except_count", "case_expression_count", "case_max_branches",
    "graph_nodes", "graph_edges", "graph_density", "graph_components",
    "graph_max_degree", "graph_max_scope_sources", "graph_max_scope_edges",
    "graph_max_scope_degree", "graph_shape", "implicit_joins", "explicit_joins",
    "cross_join_risk", "unresolved_predicates",
    "distinct_sources", "distinct_aggregates", "nonportable_markers",
    "rubric_points", "rubric_band",
)


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile. Chosen over interpolation so a threshold is
    always a value the corpus actually exhibits."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, min(len(ordered), int(round(p / 100.0 * len(ordered) + 0.5))))
    return ordered[rank - 1]


def flatten(f: Features) -> dict:
    d = f.as_dict()
    g = d.pop("join_graph", {}) or {}
    flat = {
        **{k: v for k, v in d.items() if k not in ("path",)},
        "graph_nodes": g.get("nodes", 0),
        "graph_edges": g.get("edges", 0),
        "graph_density": g.get("density", 0.0),
        "graph_components": g.get("connected_components", 0),
        "graph_max_degree": g.get("max_degree", 0),
        "graph_max_scope_sources": g.get("max_scope_sources", 0),
        "graph_max_scope_edges": g.get("max_scope_edges", 0),
        "graph_max_scope_degree": g.get("max_scope_degree", 0),
        "graph_shape": g.get("widest_scope_shape", ""),
        "implicit_joins": g.get("implicit_joins", 0),
        "explicit_joins": g.get("explicit_joins", 0),
        "cross_join_risk": g.get("cross_join_risk", 0),
        "unresolved_predicates": g.get("unresolved_predicates", 0),
    }
    return flat


def run_census(corpus_dir: str | Path) -> list[tuple[Features, dict]]:
    """Extract features for every .sql in the corpus, in natural file order."""
    out: list[tuple[Features, dict]] = []
    for path in sorted(Path(corpus_dir).glob("*.sql"), key=_natural_key):
        features = extract_features(path)
        out.append((features, flatten(features)))
    return out


def _natural_key(path: Path):
    """query2 before query10."""
    digits = "".join(c for c in path.stem if c.isdigit())
    return (int(digits) if digits else 0, path.stem)


def build_profile(rows: list[dict]) -> dict:
    """Per-feature distribution summary over the corpus."""
    profile: dict[str, dict] = {}
    numeric = [
        c for c in CSV_COLUMNS
        if c not in ("name", "parse_dialect", "graph_shape", "distinct_sources",
                     "distinct_aggregates", "nonportable_markers", "rubric_band",
                     "parse_ok", "has_having", "has_distinct", "has_order_by")
    ]
    for col in numeric:
        values = [float(r.get(col, 0) or 0) for r in rows]
        if not values:
            continue
        entry = {
            "min": _num(min(values)),
            "max": _num(max(values)),
            "mean": round(statistics.fmean(values), 3),
            "stdev": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
            "zeros": sum(1 for v in values if v == 0),
        }
        for p in PERCENTILES:
            entry[f"p{p}"] = _num(percentile(values, p))
        profile[col] = entry
    return profile


def _num(x: float):
    return int(x) if float(x).is_integer() else round(float(x), 4)


# Feature paths in the Features dataclass do not always match CSV column names.
_PROFILE_KEY = {
    "join_graph.edges": "graph_edges",
    "join_graph.max_degree": "graph_max_degree",
    "join_graph.max_scope_sources": "graph_max_scope_sources",
}


def emit_rubric(profile: dict, rows: list[dict], corpus: str, n: int) -> dict:
    """Derive rubric thresholds from the observed distribution."""
    thresholds = []
    for feature, lower_p, upper_p in SCORED_FEATURES:
        key = _PROFILE_KEY.get(feature, feature)
        stats = profile.get(key)
        if not stats:
            continue
        # A percentile of 0 means "most scripts do not have this at all", in
        # which case merely having it is already above that percentile.
        lower = max(int(stats[lower_p]), 1)
        entry = {
            "feature": feature,
            "lower": lower,
            "lower_from": f"{lower_p}={stats[lower_p]}",
        }
        if upper_p:
            # Keep the tiers distinct so one script cannot score both.
            entry["upper"] = max(int(stats[upper_p]), lower + 1)
            entry["upper_from"] = f"{upper_p}={stats[upper_p]}"
        thresholds.append(entry)

    rubric = {
        "meta": {
            "generated_by": "mlaya census --emit-rubric",
            "generated_on": date.today().isoformat(),
            "corpus": corpus,
            "n": n,
            "note": "Thresholds are corpus percentiles, not hand-picked values. "
                    "Regenerate when the corpus changes.",
        },
        "thresholds": thresholds,
        "flat_rules": {name: 1 for name, _ in FLAT_RULES},
        "flat_rule_docs": {name: doc for name, doc in FLAT_RULES},
        # Provisional; replaced by terciles of the observed score distribution.
        "bands": {"low": [0, 3], "medium": [4, 7], "high": [8, None]},
        "confidence_bands": {"high": 0.85, "medium": 0.60},
    }

    scores = sorted(score_features(_nest(r), rubric).points for r in rows)
    t1, t2, sizes = choose_bands(scores)
    rubric["bands"] = {"low": [0, t1], "medium": [t1 + 1, t2], "high": [t2 + 1, None]}
    rubric["meta"]["band_note"] = (
        f"Cuts at <={t1} / <={t2} / rest, giving {sizes[0]}/{sizes[1]}/{sizes[2]} "
        f"scripts over n={n}. Chosen as the split closest to equal thirds, with "
        f"the middle band spanning at least two score values."
    )
    return rubric


def choose_bands(scores: list[int]) -> tuple[int, int, tuple[int, int, int]]:
    """Pick the two cut points that split the score distribution most evenly.

    Raw terciles look principled but break on a spiky discrete distribution: if
    a third of the corpus piles onto two adjacent scores, the middle band
    collapses to a single value and a one-point difference decides a script's
    gold label. Searching for the most balanced split keeps the bands stable
    and is just as auditable — the chosen sizes are reported alongside.
    """
    n = len(scores)
    if n == 0:
        return 3, 7, (0, 0, 0)

    lo, hi = min(scores), max(scores)
    target = n / 3.0
    best, best_cuts, best_sizes = None, (lo, lo + 1), (n, 0, 0)

    for t1 in range(lo, hi):
        for t2 in range(t1 + 1, hi + 1):
            low = sum(1 for s in scores if s <= t1)
            medium = sum(1 for s in scores if t1 < s <= t2)
            high = n - low - medium
            if medium == 0 or high == 0:
                continue
            # A middle band covering one score value makes the gold label turn
            # on a single point, which no reviewer can defend.
            if t2 - t1 < 2:
                continue
            cost = abs(low - target) + abs(medium - target) + abs(high - target)
            if best is None or cost < best:
                best, best_cuts, best_sizes = cost, (t1, t2), (low, medium, high)

    return best_cuts[0], best_cuts[1], best_sizes


def _nest(row: dict) -> dict:
    """Re-nest a flat CSV row into the shape the rubric expects."""
    return {
        **row,
        "join_graph": {
            "edges": row.get("graph_edges", 0),
            "max_degree": row.get("graph_max_degree", 0),
            "max_scope_sources": row.get("graph_max_scope_sources", 0),
            "cross_join_risk": row.get("cross_join_risk", 0),
        },
    }


def write_csv(rows: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            for key, value in out.items():
                if isinstance(value, list):
                    out[key] = "|".join(str(v) for v in value)
            writer.writerow(out)


def write_yaml(data, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
