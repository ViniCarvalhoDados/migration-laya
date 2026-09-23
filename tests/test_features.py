"""Extractor tests.

The extractor is the single point of failure for the whole study: every gold
label and therefore every verdict about Laya rests on it. These cases are hand-
verified against the SQL text, not against the extractor's own output.
"""

from pathlib import Path

import pytest

from migration_laya.features import extract_features, parse_sql

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "tpcds"


def feats(name: str):
    return extract_features(CORPUS / f"{name}.sql")


def test_corpus_is_present():
    assert len(list(CORPUS.glob("*.sql"))) == 99


def test_every_script_parses():
    """A parse failure would silently zero out that script's ground truth."""
    failures = [p.name for p in CORPUS.glob("*.sql") if not parse_sql(p.read_text(encoding="utf-8"))[0]]
    assert failures == []


# --- query96: the simplest shape in the corpus -------------------------------
# 15 lines, one SELECT, four tables comma-joined in WHERE, a single COUNT(*).

def test_q96_is_a_flat_four_table_star():
    f = feats("query96")
    assert f.parse_ok and f.parse_dialect == "spark"
    assert f.statements == 1
    assert f.source_tables == 4
    assert f.distinct_sources == [
        "household_demographics", "store", "store_sales", "time_dim",
    ]
    assert f.subquery_count == 0
    assert f.cte_count == 0
    assert f.window_function_count == 0
    assert f.set_operation_count == 0
    assert f.max_nesting_depth == 0


def test_q96_join_graph_is_a_clean_star():
    g = feats("query96").join_graph
    assert (g["nodes"], g["edges"]) == (4, 3)
    assert g["connected_components"] == 1
    assert g["max_degree"] == 3            # store_sales is the hub
    assert g["widest_scope_shape"] == "star"
    assert g["implicit_joins"] == 3        # comma joins, no ON clauses
    assert g["explicit_joins"] == 0
    assert g["cross_join_risk"] == 0
    assert g["unresolved_predicates"] == 0


# --- query23: two statements, CTEs, correlated subqueries --------------------

def test_q23_counts_both_statements():
    f = feats("query23")
    assert f.statements == 2
    # Three CTEs are declared per statement and the file holds two statements.
    assert f.cte_count == 6
    assert f.subquery_count > 0
    assert f.correlated_subquery_count > 0
    assert f.set_operation_count == 2
    assert f.union_all_count == 2


def test_q23_graph_is_not_doubled_by_the_repeated_statement():
    """Both statements hit the same six tables; the footprint is counted once."""
    g = feats("query23").join_graph
    assert g["nodes"] == 6
    assert g["edges"] < 12          # would be doubled if statements were summed
    assert g["connected_components"] == 1


# --- dialect cascade ---------------------------------------------------------

def test_q67_falls_back_to_tsql_and_says_so():
    """`SELECT TOP` is T-SQL; needing the fallback is itself a migration flag."""
    f = feats("query67")
    assert f.parse_dialect == "tsql"
    assert "requires_dialect:tsql" in f.nonportable_markers
    assert "select_top" in f.nonportable_markers


# --- window functions and non-portable syntax -------------------------------

def test_q12_has_exactly_one_window_function():
    f = feats("query12")
    assert f.window_function_count == 1
    assert f.subquery_count == 0
    assert "interval_arithmetic" in f.nonportable_markers


def test_q14_is_the_set_operation_outlier():
    f = feats("query14")
    assert f.set_operation_count == 10
    assert f.statements == 2
    assert f.subquery_count >= 10


def test_q66_is_the_case_expression_outlier():
    f = feats("query66")
    assert f.case_expression_count == 48
    assert f.loc_code > 300


# --- resolver regressions ----------------------------------------------------

def test_q39_resolves_truncated_table_prefixes():
    """`inv_item_sk` -> inventory (truncation), `i_item_sk` -> item (not
    inventory, though both abbreviate to `i`)."""
    g = feats("query39").join_graph
    assert g["edges"] > 0
    assert g["unresolved_predicates"] == 0


@pytest.mark.parametrize("name", ["query96", "query3", "query42", "query12", "query66"])
def test_simple_scripts_resolve_every_join_predicate(name):
    assert feats(name).join_graph["unresolved_predicates"] == 0
