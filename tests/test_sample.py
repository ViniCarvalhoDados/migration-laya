"""Sampler tests: reproducibility, coverage, and the boundary/outlier contract."""

from migration_laya.sample import select, summarise_coverage

RUBRIC = {"bands": {"low": [0, 4], "medium": [5, 6], "high": [7, None]}}


def _corpus(n=60):
    """A synthetic census spanning 0..16 points with structural outliers."""
    rows = []
    for i in range(n):
        points = i % 17
        band = "low" if points <= 4 else ("medium" if points <= 6 else "high")
        rows.append({
            "name": f"query{i}",
            "rubric_points": str(points),
            "rubric_band": band,
            "loc_code": str(10 + i),
            "source_tables": str(1 + i % 9),
            "subquery_count": str(i % 5),
            "cte_count": str(i % 3),
            "graph_edges": str(i % 7),
            "graph_nodes": str(1 + i % 8),
            "graph_max_scope_sources": str(1 + i % 6),
            "set_operation_count": str(i % 4),
            "case_expression_count": str(i % 6),
            "window_function_count": str(i % 2),
            "statements": "2" if i == 7 else "1",
        })
    return rows


def test_sample_is_reproducible_for_a_seed():
    rows = _corpus()
    a = [p["origin"] for p in select(rows, 10, RUBRIC, seed=42)]
    b = [p["origin"] for p in select(rows, 10, RUBRIC, seed=42)]
    assert a == b


def test_a_different_seed_gives_a_different_sample():
    rows = _corpus()
    a = {p["origin"] for p in select(rows, 10, RUBRIC, seed=1)}
    b = {p["origin"] for p in select(rows, 10, RUBRIC, seed=999)}
    assert a != b


def test_sample_has_the_requested_size_and_no_duplicates():
    picked = select(_corpus(), 10, RUBRIC, seed=42)
    assert len(picked) == 10
    assert len({p["origin"] for p in picked}) == 10


def test_ids_are_sequential_and_ordered_by_complexity():
    picked = select(_corpus(), 10, RUBRIC, seed=42)
    assert [p["id"] for p in picked] == [f"script_{i:02d}" for i in range(1, 11)]
    points = [p["rubric_points"] for p in picked]
    assert points == sorted(points)


def test_both_band_boundaries_are_represented():
    """The cut points are where a one-point difference flips the gold label."""
    picked = select(_corpus(), 10, RUBRIC, seed=42)
    reasons = " ".join(r for p in picked for r in p["selected_because"])
    assert "low/medium boundary" in reasons
    assert "medium/high boundary" in reasons


def test_sample_spans_the_easy_end_of_the_corpus():
    """Without this the auto-triage headline is biased downward: the simple
    scripts are exactly the ones expected to classify without a human."""
    picked = select(_corpus(), 10, RUBRIC, seed=42)
    assert min(p["rubric_points"] for p in picked) <= 2


def test_outliers_do_not_crowd_out_stratified_fill():
    picked = select(_corpus(), 10, RUBRIC, seed=42)
    fills = [p for p in picked if any("stratified fill" in r for r in p["selected_because"])]
    assert len(fills) >= 3


def test_every_pick_records_why_and_where_it_sits():
    for p in select(_corpus(), 10, RUBRIC, seed=42):
        assert p["selected_because"]
        assert 0 <= p["corpus_percentile"]["rubric_points"] <= 100
        assert "loc_code" in p["corpus_percentile"]


def test_coverage_summary_reports_the_span():
    rows = _corpus()
    picked = select(rows, 10, RUBRIC, seed=42)
    cov = summarise_coverage(picked, rows)
    assert cov["n_sampled"] == 10
    assert cov["n_corpus"] == len(rows)
    assert sum(cov["bands"].values()) == 10
    lo, hi = cov["rubric_points_range"]
    assert lo <= hi


def test_sampling_more_than_the_corpus_holds_is_capped():
    rows = _corpus(8)
    picked = select(rows, 20, RUBRIC, seed=42)
    assert len(picked) <= len(rows)
    assert len({p["origin"] for p in picked}) == len(picked)


# --- evidence cards ----------------------------------------------------------

from migration_laya.cards import build_structure, build_facts, check_budget


FEATURES = {
    "loc_code": 243, "statements": 2, "source_tables": 5, "subquery_count": 19,
    "correlated_subquery_count": 12, "cte_count": 4, "window_function_count": 0,
    "set_operation_count": 10, "case_expression_count": 0, "max_nesting_depth": 4,
    "join_graph": {"edges": 6, "max_scope_sources": 3, "widest_scope_shape": "star"},
}


def test_structure_pluralises_correctly():
    text = build_structure(FEATURES)
    assert "19 subqueries" in text
    assert "subquerys" not in text
    assert "4 CTEs" in text
    assert "2 statements" in text


def test_a_single_item_reads_as_singular():
    text = build_structure({**FEATURES, "statements": 1, "subquery_count": 1})
    assert "1 statement in the file" in text
    assert "1 subquery" in text


def test_absent_features_are_listed_with_or_not_and():
    text = build_structure(FEATURES)
    assert "No window function or CASE expression." in text


def test_a_lone_marker_is_not_spelled_out_letter_by_letter():
    """A single marker arrives as a bare string from the CSV round-trip; joining
    it directly produced 'Engine-specific syntax: r, o, l, l, u'."""
    text = build_structure({**FEATURES, "nonportable_markers": "rollup"})
    assert "Engine-specific syntax: rollup." in text
    assert "r, o, l" not in text


def test_marker_lists_still_work():
    text = build_structure({**FEATURES, "nonportable_markers": ["rollup", "select_top"]})
    assert "rollup, select_top" in text


def test_facts_line_is_machine_readable_and_complete():
    facts = build_facts(FEATURES)
    for key in ("lines=243", "statements=2", "sources=5", "subqueries=19",
                "ctes=4", "window_fns=0", "set_ops=10", "nesting=4"):
        assert key in facts


def test_budget_check_flags_an_oversized_card():
    ok, tokens = check_budget({"purpose": "word " * 2000, "structure": "", "facts": ""})
    assert not ok and tokens > 380


def test_full_corpus_sample_returns_every_script():
    """Asking for the whole corpus must return the whole corpus: an earlier
    fill drew randomly on the first round and by index afterwards, so the same
    script could be picked twice and the sample silently came up short."""
    rows = _corpus(60)
    picked = select(rows, len(rows), RUBRIC, seed=42)
    assert len(picked) == len(rows)
    assert {p["origin"] for p in picked} == {r["name"] for r in rows}


def test_no_duplicates_at_any_sample_size():
    rows = _corpus(60)
    for n in (5, 17, 33, 50, 60):
        picked = select(rows, n, RUBRIC, seed=7)
        assert len({p["origin"] for p in picked}) == len(picked)
