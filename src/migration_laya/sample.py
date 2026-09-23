"""Stratified sampling of the study set out of the full corpus census.

Picking ten scripts by eye biases the study toward cases the author already
understands. Instead the sample is drawn from the scored census: proportional
across complexity bands, with the structural outliers and the band-boundary
cases forced in. The boundary cases matter most — that is where a classifier
that has merely learnt "long query = hard" will come apart, and measuring that
is the point of the exercise.

Every pick records why it was chosen and where it sits in the corpus
distribution, so the report can state how much of the space the study covered.
"""

from __future__ import annotations

import random
from pathlib import Path

from .census import percentile

# Structural extremes worth forcing into any sample: each one is a distinct
# migration hazard that a ten-script study would otherwise likely miss.
FORCED_MAXIMA: tuple[tuple[str, str], ...] = (
    ("subquery_count", "most nested subqueries in the corpus"),
    ("graph_nodes", "widest data footprint"),
    ("set_operation_count", "most set operations"),
    ("case_expression_count", "most CASE expressions"),
    ("window_function_count", "most window functions"),
    ("statements", "multiple statements in one file"),
    ("graph_max_scope_sources", "widest single join"),
)


def _int(row: dict, key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def percentile_rank(values: list[float], value: float) -> int:
    """Percentage of the corpus at or below this value."""
    if not values:
        return 0
    return round(100.0 * sum(1 for v in values if v <= value) / len(values))


def select(rows: list[dict], n: int, rubric: dict, seed: int = 42) -> list[dict]:
    """Choose ``n`` scripts, returning one record per pick with its rationale."""
    rng = random.Random(seed)
    by_name = {r["name"]: r for r in rows}
    reasons: dict[str, list[str]] = {}

    def claim(name: str, why: str) -> None:
        if name:
            reasons.setdefault(name, []).append(why)

    # 1. Band boundaries first: one script on each side of each cut. These are
    #    the scripts whose gold label a single rubric point decides, and they
    #    are where a classifier that merely learnt "long query = hard" breaks.
    bands = rubric.get("bands", {})
    for cut_name, cut in (("low/medium", bands.get("low", [0, 0])[1]),
                          ("medium/high", bands.get("medium", [0, 0])[1])):
        if cut is None:
            continue
        below = [r for r in rows if _int(r, "rubric_points") == cut]
        above = [r for r in rows if _int(r, "rubric_points") == cut + 1]
        for side, pool in (("just below", below), ("just above", above)):
            if pool:
                chosen = rng.choice(sorted(pool, key=lambda r: r["name"]))
                claim(chosen["name"],
                      f"{side} the {cut_name} boundary "
                      f"(points={_int(chosen, 'rubric_points')})")

    # 2. Structural outliers, but only up to a budget. Left unbounded they eat
    #    every slot and the study never sees a simple script — which would make
    #    the headline "how much can be auto-triaged" meaningless, since the easy
    #    cases are exactly the ones expected to auto-triage.
    reserve = max(3, n // 3)
    outlier_budget = max(0, n - len(reasons) - reserve)
    for key, why in FORCED_MAXIMA:
        if outlier_budget <= 0:
            break
        best = max(rows, key=lambda r: (_int(r, key), r["name"]))
        if _int(best, key) > 0 and best["name"] not in reasons:
            claim(best["name"], f"{why} ({key}={_int(best, key)})")
            outlier_budget -= 1

    # 3. Fill the rest proportionally across bands, sampling within each band.
    remaining = n - len(reasons)
    if remaining > 0:
        pools: dict[str, list[dict]] = {}
        for r in rows:
            if r["name"] not in reasons:
                pools.setdefault(r.get("rubric_band", "?"), []).append(r)

        quota = _proportional_quota(pools, remaining)
        for band, count in quota.items():
            for pick in _spread_within_band(pools.get(band, []), count, rng):
                claim(pick["name"],
                      f"stratified fill ({band}, {_int(pick, 'rubric_points')}pts)")

    # 4. Annotate every pick with its position in the corpus distribution.
    metrics = ["rubric_points", "loc_code", "source_tables", "subquery_count",
               "cte_count", "graph_edges", "graph_max_scope_sources"]
    columns = {m: [float(_int(r, m)) for r in rows] for m in metrics}

    picked = []
    for i, name in enumerate(sorted(reasons, key=lambda k: _int(by_name[k], "rubric_points")), 1):
        row = by_name[name]
        picked.append({
            "id": f"script_{i:02d}",
            "origin": name,
            "rubric_points": _int(row, "rubric_points"),
            "rubric_band": row.get("rubric_band", ""),
            "selected_because": reasons[name],
            "corpus_percentile": {
                m: percentile_rank(columns[m], float(_int(row, m))) for m in metrics
            },
        })
    return picked


def _spread_within_band(pool: list[dict], count: int, rng: random.Random) -> list[dict]:
    """Take ``count`` scripts from one band, spread across its score values.

    Sampling a band uniformly can land every pick on the same score — with the
    "low" band spanning 0 to 4, two uniform draws both hitting 4 would leave the
    study with no genuinely simple script, understating the auto-triage rate
    that the whole exercise is meant to measure. Walking the distinct scores
    from the band's extremes inward guarantees the span is covered first.
    """
    if count <= 0 or not pool:
        return []

    by_score: dict[int, list[dict]] = {}
    for row in sorted(pool, key=lambda r: r["name"]):
        by_score.setdefault(_int(row, "rubric_points"), []).append(row)

    scores = sorted(by_score)
    # Alternate lowest, highest, second-lowest, ... so the band's range is
    # represented before its mode is sampled twice.
    order: list[int] = []
    left, right = 0, len(scores) - 1
    while left <= right:
        order.append(scores[left])
        if left != right:
            order.append(scores[right])
        left, right = left + 1, right - 1

    # Shuffle each bucket once, then walk it by index. Drawing randomly on the
    # first round and by index afterwards can return the same script twice,
    # which silently shrinks the sample when duplicates are collapsed.
    for bucket in by_score.values():
        rng.shuffle(bucket)

    picked: list[dict] = []
    round_no = 0
    while len(picked) < count:
        progressed = False
        for score in order:
            bucket = by_score[score]
            if round_no < len(bucket):
                picked.append(bucket[round_no])
                progressed = True
                if len(picked) == count:
                    return picked
        if not progressed:
            break
        round_no += 1
    return picked


def _proportional_quota(pools: dict[str, list[dict]], total: int) -> dict[str, int]:
    """Split ``total`` picks across bands in proportion to band size."""
    sizes = {band: len(pool) for band, pool in pools.items() if pool}
    if not sizes or total <= 0:
        return {}
    population = sum(sizes.values())
    quota = {band: int(total * size / population) for band, size in sizes.items()}
    # Hand out the rounding remainder to the largest bands first.
    for band in sorted(sizes, key=lambda b: -sizes[b]):
        if sum(quota.values()) >= total:
            break
        quota[band] += 1
    return quota


def summarise_coverage(picked: list[dict], rows: list[dict]) -> dict:
    """How much of the corpus the sample spans, for the final report."""
    points = [float(_int(r, "rubric_points")) for r in rows]
    picked_points = [p["rubric_points"] for p in picked]
    bands: dict[str, int] = {}
    for p in picked:
        bands[p["rubric_band"]] = bands.get(p["rubric_band"], 0) + 1
    return {
        "n_sampled": len(picked),
        "n_corpus": len(rows),
        "bands": bands,
        "rubric_points_range": [min(picked_points, default=0), max(picked_points, default=0)],
        "corpus_points_range": [int(min(points, default=0)), int(max(points, default=0))],
        "corpus_p90_points": int(percentile(points, 90)),
    }
