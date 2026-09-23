"""Windowing and aggregation tests for the read-the-SQL mode.

The aggregation rules are pre-registered in `chunks.AGGREGATION`. These tests
pin them down so that a later "the numbers would look better with mean instead
of max" cannot quietly happen after the results are in.
"""

from pathlib import Path

import pytest

from migration_laya import chunks

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "tpcds"


def test_short_script_is_a_single_window():
    """The median script is ~44 lines; most never get split, so this mode is
    mostly 'Laya reads the whole SQL'."""
    sql = (CORPUS / "query96.sql").read_text(encoding="utf-8")
    assert len(chunks.split_sql(sql)) == 1


def test_long_script_is_split():
    sql = (CORPUS / "query66.sql").read_text(encoding="utf-8")
    assert len(chunks.split_sql(sql)) > 1


def test_every_window_fits_the_budget():
    for name in ("query66.sql", "query14.sql", "query8.sql", "query23.sql"):
        sql = (CORPUS / name).read_text(encoding="utf-8")
        for window in chunks.split_sql(sql):
            cost = sum(chunks.approx_tokens(l) for l in window.splitlines())
            assert cost <= chunks.WINDOW_TOKEN_BUDGET, name


def test_windows_preserve_every_code_line_exactly_once():
    """No line dropped and none duplicated: the model must see the whole script."""
    sql = (CORPUS / "query14.sql").read_text(encoding="utf-8")
    rejoined = "\n".join(chunks.split_sql(sql)).splitlines()
    original = [
        l.rstrip() for l in chunks._COMMENT.sub("", sql).splitlines() if l.strip()
    ]
    assert rejoined == original


def test_lines_are_never_split_in_half():
    sql = (CORPUS / "query66.sql").read_text(encoding="utf-8")
    original = {
        l.rstrip() for l in chunks._COMMENT.sub("", sql).splitlines() if l.strip()
    }
    for window in chunks.split_sql(sql):
        for line in window.splitlines():
            assert line in original


def test_an_oversized_single_line_still_becomes_a_window():
    """Better an over-budget window than a dropped line."""
    monster = " ".join(f"col_{i} = {i}" for i in range(500))
    windows = chunks.split_sql(monster)
    assert len(windows) == 1
    assert windows[0] == monster


def test_empty_or_comment_only_sql_yields_no_windows():
    assert chunks.split_sql("") == []
    assert chunks.split_sql("-- just a comment\n/* and a block */") == []


def test_fragments_are_labelled_as_fragments():
    """A window is not the whole script and the state says so."""
    assert "note" not in chunks.render_window("select 1", 0, 1)
    state = chunks.render_window("select 1", 0, 3)
    assert "Fragment 1 of 3" in state["note"]


# --- aggregation -------------------------------------------------------------

def noul(value):
    return {"type": "noul", "value": value, "max_probability": max(value, 1 - value)}


def test_single_window_passes_straight_through():
    answer = chunks.aggregate("has_subquery", [noul(0.3)])
    assert answer["value"] == 0.3
    assert "aggregation" not in answer


def test_existential_questions_take_the_maximum():
    """One window containing a subquery makes the script contain a subquery."""
    answer = chunks.aggregate("has_subquery", [noul(0.1), noul(0.9), noul(0.2)])
    assert answer["value"] == 0.9
    assert answer["n_windows"] == 3
    assert answer["aggregation"] == "max"


def test_complexity_takes_the_hardest_window():
    answers = [
        {"type": "score", "value": 0.4, "max_probability": 0.6},
        {"type": "score", "value": 1.7, "max_probability": 0.5},
    ]
    assert chunks.aggregate("migration_complexity", answers)["value"] == 1.7


def test_choice_takes_the_most_confident_window():
    answers = [
        {"type": "choice", "value": "refactor", "max_probability": 0.4},
        {"type": "choice", "value": "redesign", "max_probability": 0.8},
    ]
    assert chunks.aggregate("rewrite_strategy", answers)["value"] == "redesign"


def test_aggregation_rules_are_declared_for_every_question():
    from migration_laya.decide import VERIFIABLE
    for question in VERIFIABLE + ("needs_human_review", "migration_complexity",
                                  "rewrite_strategy"):
        assert question in chunks.AGGREGATION


def test_the_counting_question_is_flagged_as_unanswerable_by_window():
    """`multi_source` asks for a global count of distinct tables; no single
    window can see the whole FROM list. Kept in the run so the cost shows up."""
    assert "multi_source" in chunks.STRUCTURALLY_GLOBAL


def test_aggregate_of_nothing_is_empty():
    assert chunks.aggregate("has_subquery", []) == {}
    assert chunks.aggregate("has_subquery", [None]) == {}
