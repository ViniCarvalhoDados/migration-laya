"""Rubric tests: band boundaries, threshold tiers, and percentile derivation."""

import pytest

from migration_laya.census import (
    percentile, emit_rubric, build_profile, choose_bands, _nest,
)
from migration_laya.rubric import score_features, band_for, band_distance, get_path


RUBRIC = {
    "thresholds": [
        {"feature": "loc_code", "lower": 50, "upper": 100},
        {"feature": "subquery_count", "lower": 1, "upper": 4},
        {"feature": "join_graph.edges", "lower": 5, "upper": 7},
    ],
    "flat_rules": {
        "multi_statement": 1,
        "cross_join_risk": 1,
        "nonportable_syntax": 1,
        "correlated_subquery": 1,
    },
    "bands": {"low": [0, 3], "medium": [4, 7], "high": [8, None]},
}


def base(**over):
    f = {
        "loc_code": 10, "statements": 1, "subquery_count": 0,
        "correlated_subquery_count": 0, "nonportable_markers": [],
        "join_graph": {"edges": 0, "cross_join_risk": 0},
    }
    f.update(over)
    return f


def test_trivial_script_scores_zero():
    assert score_features(base(), RUBRIC).points == 0


def test_lower_tier_gives_one_point_upper_gives_two():
    assert score_features(base(loc_code=50), RUBRIC).points == 1
    assert score_features(base(loc_code=99), RUBRIC).points == 1
    assert score_features(base(loc_code=100), RUBRIC).points == 2


def test_tiers_do_not_stack_on_the_same_feature():
    """A script far above the upper threshold scores 2, never 1+2."""
    assert score_features(base(loc_code=100_000), RUBRIC).points == 2


def test_flat_rules_each_add_one():
    f = base(statements=2, correlated_subquery_count=3,
             nonportable_markers=["rollup"],
             join_graph={"edges": 0, "cross_join_risk": 2})
    assert score_features(f, RUBRIC).points == 4


def test_reasons_explain_every_point():
    s = score_features(base(loc_code=100, subquery_count=1), RUBRIC)
    assert s.points == 3
    assert len(s.reasons) == 2
    assert any("loc_code=100 >= 100 (+2)" == r for r in s.reasons)


def test_nested_feature_paths_are_scored():
    assert score_features(base(join_graph={"edges": 7, "cross_join_risk": 0}),
                          RUBRIC).points == 2


def test_get_path_returns_zero_for_missing_keys():
    assert get_path({"a": {"b": 3}}, "a.b") == 3
    assert get_path({"a": {}}, "a.b") == 0
    assert get_path({}, "nope.nope") == 0


# --- band boundaries ---------------------------------------------------------

@pytest.mark.parametrize("points,band", [
    (0, "low"), (3, "low"), (4, "medium"), (7, "medium"), (8, "high"), (99, "high"),
])
def test_band_boundaries(points, band):
    assert band_for(points, RUBRIC) == band


def test_band_distance_measures_tiers_apart():
    assert band_distance("low", "low") == 0
    assert band_distance("low", "medium") == 1
    assert band_distance("low", "high") == 2
    assert band_distance("low", "nonsense") == 99


# --- percentiles -------------------------------------------------------------

def test_percentile_returns_an_observed_value():
    values = [1.0, 2.0, 3.0, 4.0, 100.0]
    for p in (0, 25, 50, 75, 100):
        assert percentile(values, p) in values


def test_percentile_is_monotonic():
    values = [float(i) for i in range(100)]
    got = [percentile(values, p) for p in (10, 25, 50, 75, 90)]
    assert got == sorted(got)


def test_percentile_of_empty_is_zero():
    assert percentile([], 50) == 0.0


# --- rubric derivation -------------------------------------------------------

def _rows(n=30):
    return [
        {"loc_code": i, "source_tables": i % 7, "subquery_count": i % 5,
         "cte_count": 0, "window_function_count": 0, "set_operation_count": 0,
         "max_nesting_depth": i % 3, "case_expression_count": 0,
         "statements": 1, "correlated_subquery_count": 0,
         "nonportable_markers": [], "graph_edges": i % 9,
         "graph_max_degree": i % 4, "graph_max_scope_sources": i % 6,
         "cross_join_risk": 0}
        for i in range(1, n + 1)
    ]


def test_emitted_thresholds_are_never_zero():
    """A percentile of 0 must become a threshold of 1: when most scripts lack a
    feature, merely having it is the signal."""
    rows = _rows()
    rubric = emit_rubric(build_profile(rows), rows, "test", len(rows))
    for t in rubric["thresholds"]:
        assert t["lower"] >= 1, t


def test_emitted_tiers_stay_distinct():
    rows = _rows()
    rubric = emit_rubric(build_profile(rows), rows, "test", len(rows))
    for t in rubric["thresholds"]:
        if "upper" in t:
            assert t["upper"] > t["lower"], t


def test_emitted_bands_are_contiguous_and_usable():
    rows = _rows()
    rubric = emit_rubric(build_profile(rows), rows, "test", len(rows))
    low, medium, high = (rubric["bands"][k] for k in ("low", "medium", "high"))
    assert low[0] == 0
    assert medium[0] == low[1] + 1
    assert high[0] == medium[1] + 1
    assert high[1] is None
    # Every script must land in exactly one band.
    for row in rows:
        assert band_for(score_features(_nest(row), rubric).points, rubric) in (
            "low", "medium", "high")


def test_rubric_records_where_thresholds_came_from():
    rows = _rows()
    rubric = emit_rubric(build_profile(rows), rows, "test", len(rows))
    assert rubric["meta"]["n"] == len(rows)
    # The note must state the resulting split so the cut is auditable.
    assert "/" in rubric["meta"]["band_note"]
    assert str(len(rows)) in rubric["meta"]["band_note"]
    for t in rubric["thresholds"]:
        assert "lower_from" in t


# --- band selection ----------------------------------------------------------

def test_band_selection_splits_evenly():
    scores = [i % 9 for i in range(90)]           # uniform 0..8
    t1, t2, sizes = choose_bands(scores)
    assert t1 < t2
    assert sum(sizes) == len(scores)
    assert max(sizes) - min(sizes) <= len(scores) // 4


def test_band_selection_never_collapses_the_middle_band():
    """A spiky distribution is exactly where raw terciles fail: a third of the
    corpus piling onto two adjacent scores would leave medium one value wide."""
    scores = [5] * 40 + [6] * 30 + [0, 1, 2, 3] * 5 + [9, 12, 15] * 3
    t1, t2, sizes = choose_bands(scores)
    assert t2 - t1 >= 2
    assert all(size > 0 for size in sizes)


def test_band_selection_handles_an_empty_corpus():
    t1, t2, sizes = choose_bands([])
    assert t1 < t2 and sizes == (0, 0, 0)
