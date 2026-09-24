"""Label derivation and training-export tests.

These two pieces exist to avoid the mistake the discovery study made: gold that
is a function of the same features the model reads. Derivation recovers the
label from what a migration actually did; the exporter refuses to let a
near-duplicate sit on both sides of a split.
"""

import json

import pytest

from migration_laya import labels as lab
from migration_laya import training as tr

STAR = """
SELECT i_brand, Sum(ss_ext_sales_price)
FROM store_sales, item, date_dim
WHERE ss_item_sk = i_item_sk AND ss_sold_date_sk = d_date_sk
GROUP BY i_brand
"""


def write(tmp_path, name, sql):
    path = tmp_path / name
    path.write_text(sql, encoding="utf-8")
    return path


# --- deriving a label from a finished migration ------------------------------

def test_cosmetic_change_is_lift_and_shift(tmp_path):
    """Different literals and casing, same shape and same tables."""
    before = write(tmp_path, "a.sql", STAR)
    after = write(tmp_path, "b.sql", STAR.replace("i_brand", "I_BRAND"))
    assert lab.derive(before, after).strategy == "lift_and_shift"


def test_wrapping_in_a_derived_table_is_a_refactor(tmp_path):
    before = write(tmp_path, "a.sql", STAR)
    after = write(tmp_path, "b.sql",
                  f"SELECT * FROM ({STAR}) t ORDER BY 1 LIMIT 100")
    row = lab.derive(before, after)
    assert row.strategy == "refactor"
    assert "derived_table_count" in row.shape_changes


def test_reading_a_different_table_is_a_redesign(tmp_path):
    before = write(tmp_path, "a.sql", STAR)
    after = write(tmp_path, "b.sql", STAR.replace("store_sales", "web_sales"))
    row = lab.derive(before, after)
    assert row.strategy == "redesign"
    assert row.sources_added == ["web_sales"]
    assert row.sources_removed == ["store_sales"]


def test_an_unparseable_side_is_handed_to_a_human(tmp_path):
    before = write(tmp_path, "a.sql", STAR)
    after = write(tmp_path, "b.sql", "this is not sql at all ((((")
    row = lab.derive(before, after)
    assert row.strategy == "manual_rewrite"
    assert row.confidence == "low"
    assert row.parse_ok is False


def test_every_derivation_explains_itself(tmp_path):
    """A migration lead has to be able to disagree with a specific case."""
    before = write(tmp_path, "a.sql", STAR)
    for after_sql in (STAR, f"SELECT * FROM ({STAR}) t",
                      STAR.replace("item", "promotion")):
        after = write(tmp_path, "b.sql", after_sql)
        assert lab.derive(before, after).reasons


def test_summary_flags_classes_too_thin_to_learn(tmp_path):
    before = write(tmp_path, "a.sql", STAR)
    after = write(tmp_path, "b.sql", STAR)
    rows = [lab.derive(before, after) for _ in range(5)]
    summary = lab.summarise(rows)
    assert summary["n"] == 5
    assert "redesign" in summary["thin_classes"]
    assert summary["by_strategy"]["lift_and_shift"] == 5


# --- exporting a dataset -----------------------------------------------------

QUESTIONS = {
    "has_subquery": {"type": "noul", "instructions": "..."},
    "rewrite_strategy": {"type": "choice", "instructions": "...",
                         "criteria": {"lift_and_shift": "a", "refactor": "b"}},
    "migration_complexity": {"type": "score", "instructions": "...",
                             "criteria": ["low", "medium", "high"]},
}


def doc(i, sources=("a", "b"), subqueries=0):
    return {
        "id": f"script_{i:02d}", "name": f"query{i}",
        "evidence_card": {"purpose": "p", "structure": "s", "facts": "f"},
        "features": {"source_tables": len(sources), "subquery_count": subqueries,
                     "cte_count": 0, "window_function_count": 0,
                     "set_operation_count": 0, "max_nesting_depth": 0,
                     "graph_edges": 1, "statements": 1,
                     "distinct_sources": list(sources)},
        "gold": {"has_subquery": subqueries > 0,
                 "rewrite_strategy": "refactor",
                 "migration_complexity": "medium"},
    }


def test_gold_is_encoded_as_one_hot_per_question_type():
    case = tr.build_case(doc(1, subqueries=2), QUESTIONS, doc(1, subqueries=2)["gold"])
    gold = json.loads(case["gold"])
    assert gold["has_subquery"]["label"] == "true"
    assert gold["has_subquery"]["probabilities"] == {"true": 1.0, "false": 0.0}
    assert gold["rewrite_strategy"]["label"] == "refactor"
    assert gold["migration_complexity"]["label"] == 1      # medium -> index 1


def test_a_case_without_an_evidence_card_is_dropped():
    empty = doc(1)
    empty["evidence_card"] = {"purpose": None, "structure": None, "facts": None}
    assert tr.build_case(empty, QUESTIONS, empty["gold"]) is None


def test_a_label_outside_the_option_set_is_dropped_not_guessed():
    d = doc(1)
    d["gold"]["rewrite_strategy"] = "something_else"
    gold = json.loads(tr.build_case(d, QUESTIONS, d["gold"])["gold"])
    assert "rewrite_strategy" not in gold
    assert "has_subquery" in gold


def test_near_duplicates_share_a_family():
    """q33 / q56 / q60 in this corpus differ only in a grouping column."""
    a, b = doc(1), doc(2)
    assert tr.family_key(a["features"]) == tr.family_key(b["features"])
    different = doc(3, sources=("a", "b", "c"))
    assert tr.family_key(different["features"]) != tr.family_key(a["features"])


def test_a_family_never_straddles_two_splits():
    """The leak that makes a reported accuracy partly memorisation."""
    cases = []
    for i in range(60):
        d = doc(i, sources=tuple(f"t{j}" for j in range(i % 12 + 1)))
        cases.append(tr.build_case(d, QUESTIONS, d["gold"]))
    splits = tr.split_by_family(cases)
    seen = {}
    for name, rows in splits.items():
        for case in rows:
            assert seen.setdefault(case["family"], name) == name


def test_split_report_would_catch_a_leak():
    cases = [tr.build_case(doc(i), QUESTIONS, doc(i)["gold"]) for i in range(4)]
    leaked = {"train": cases[:2], "test": cases[2:]}     # all one family
    assert tr.report(leaked, QUESTIONS)["family_overlap"]

    clean = tr.split_by_family(cases)
    assert tr.report(clean, QUESTIONS)["family_overlap"] == {}


def test_report_counts_decisions_against_the_reference_scale():
    cases = [tr.build_case(doc(i, sources=tuple(f"t{j}" for j in range(i % 9 + 1))),
                           QUESTIONS, doc(i)["gold"]) for i in range(30)]
    summary = tr.report(tr.split_by_family(cases), QUESTIONS)
    assert summary["decisions_total"] == 30 * 3
    assert summary["reference_scale"]["decisions"] == 6000
    assert set(summary["cases"]) == {"train", "calibration", "test"}


def test_a_calibration_slice_is_always_reserved():
    """Skipping it reproduces the shipped checkpoint's uncalibrated confidences."""
    assert "calibration" in tr.DEFAULT_SPLIT
    assert tr.DEFAULT_SPLIT["calibration"] > 0
    assert sum(tr.DEFAULT_SPLIT.values()) == pytest.approx(1.0)
