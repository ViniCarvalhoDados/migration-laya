"""Tests for the two commercial questions.

The bug these pin was a reported result, not a crash: `migration_complexity`
was scored against a 31% baseline because three bands invites "one third". The
bands are 31 / 37 / 31, so the number to beat is 37% — and under the wrong one,
a wording scoring 38% read as *above* baseline when it is level with it.
"""

import pytest

from migration_laya import business as biz


def _answer(probabilities: dict) -> dict:
    label = max(probabilities, key=probabilities.get)
    return {"type": "score", "label": label, "probabilities": probabilities}


def _corpus(bands: list[str], probabilities) -> tuple[dict, dict]:
    """Docs keyed by id and raw answers keyed by script, matched by origin."""
    docs, raw = {}, {}
    for i, band in enumerate(bands):
        script_id = f"script_{i:02d}"
        origin = f"query{i:02d}"
        docs[script_id] = {"id": script_id, "name": origin,
                           "gold": {"migration_complexity": band,
                                    "rewrite_strategy": "refactor"}}
        raw[script_id] = {
            "script_id": script_id, "origin": origin,
            "answers": {"migration_complexity_p1": _answer(probabilities(i, band))},
        }
    return docs, raw


# The real corpus: 31 low, 37 medium, 31 high.
CORPUS_BANDS = ["low"] * 31 + ["medium"] * 37 + ["high"] * 31


def _aligned(i: int, band: str) -> dict:
    """Probabilities that point at the right band, so only the cut is at issue."""
    weights = {"low": (0.7, 0.2, 0.1), "medium": (0.2, 0.6, 0.2),
               "high": (0.1, 0.2, 0.7)}[band]
    return dict(zip(("low", "medium", "high"), weights))


def test_baseline_is_the_majority_class_not_one_over_three():
    docs, raw = _corpus(CORPUS_BANDS, _aligned)
    result = biz.complexity(raw, docs, "migration_complexity_p1", splits=20)

    assert result["band_counts"] == {"low": 31, "medium": 37, "high": 31}
    assert result["majority_baseline"] == pytest.approx(37 / 99, abs=1e-3)
    # The reflex answer, and the one this test exists to keep out.
    assert result["majority_baseline"] != pytest.approx(31 / 99, abs=1e-3)


def test_a_constant_middle_answer_scores_exactly_the_baseline():
    """The failure mode the argmax actually shows on the real run."""
    docs, raw = _corpus(CORPUS_BANDS,
                        lambda i, band: {"low": 0.25, "medium": 0.5, "high": 0.25})
    result = biz.complexity(raw, docs, "migration_complexity_p1", splits=20)

    assert result["distinct_argmax_labels"] == 1
    assert result["argmax_accuracy"] == pytest.approx(result["majority_baseline"])


def test_the_rubric_that_defines_the_gold_is_reported_as_free_and_perfect():
    """Without this column, reproducing the rubric badly looks like a result."""
    docs, raw = _corpus(CORPUS_BANDS, _aligned)
    result = biz.complexity(raw, docs, "migration_complexity_p1", splits=20)
    assert result["rubric_accuracy"] == 1.0


def test_holdout_never_beats_the_in_sample_ceiling():
    docs, raw = _corpus(CORPUS_BANDS, _aligned)
    result = biz.complexity(raw, docs, "migration_complexity_p1", splits=40)
    assert result["holdout_accuracy"]["mean"] <= result["optimistic_accuracy"]


def test_a_cut_point_lands_on_the_side_the_grid_says():
    """Float dust once put 1.5999999999999999 below a cut of 1.6.

    The fixture separates the three bands perfectly, so anything below 100%
    here is the comparison disagreeing with itself, not a modelling limit.
    """
    docs, raw = _corpus(CORPUS_BANDS, _aligned)
    result = biz.complexity(raw, docs, "migration_complexity_p1", splits=20)
    assert result["optimistic_accuracy"] == 1.0
    assert result["error_structure_optimistic"]["two_bands"] == 0.0


def test_error_structure_separates_adjacent_from_two_band_mistakes():
    """Calling a `high` script `low` is the error that ruins planning."""
    assert biz._error_structure([0, 1, 2], [0, 1, 2]) == {
        "exact": 1.0, "one_band": 0.0, "two_bands": 0.0, "within_one": 1.0}
    assert biz._error_structure([0, 0, 0], [0, 1, 2]) == pytest.approx(
        {"exact": 1 / 3, "one_band": 1 / 3, "two_bands": 1 / 3,
         "within_one": 2 / 3}, abs=1e-4)


def test_ordinal_expected_value_orders_the_bands():
    order = ["low", "medium", "high"]
    low = biz._expected_level({"low": 0.8, "medium": 0.15, "high": 0.05}, order)
    high = biz._expected_level({"low": 0.05, "medium": 0.15, "high": 0.8}, order)
    assert low < 1.0 < high


def test_several_wordings_are_averaged_and_labelled_ensemble():
    docs, raw = _corpus(CORPUS_BANDS, _aligned)
    for prediction in raw.values():
        prediction["answers"]["migration_complexity_p2"] = _answer(
            {"low": 0.34, "medium": 0.33, "high": 0.33})

    result = biz.complexity(
        raw, docs, ["migration_complexity_p1", "migration_complexity_p2"],
        splits=20)
    assert result["wording"] == "ensemble"
    assert result["n_wordings"] == 2


def test_strategy_reports_which_classes_were_ever_predicted():
    """A model that only ever says `refactor` must be visible as such."""
    docs, raw = _corpus(CORPUS_BANDS, _aligned)
    for prediction in raw.values():
        prediction["answers"]["rewrite_strategy_p1"] = {
            "type": "choice", "label": "refactor",
            "probabilities": {"lift_and_shift": 0.2, "refactor": 0.5,
                              "redesign": 0.2, "manual_rewrite": 0.1}}

    result = biz.strategy(raw, docs, "rewrite_strategy_p1")
    assert result["distinct_predictions"] == ["refactor"]
    assert result["accuracy"] == pytest.approx(result["majority_baseline"])


def test_a_single_feature_is_scored_as_a_baseline():
    """R02: counting lines beats the model, so the model is scored beside it."""
    docs = {}
    for i, band in enumerate(CORPUS_BANDS):
        # `loc_code` that orders the bands perfectly, `noise` that does not.
        docs[f"script_{i:02d}"] = {
            "id": f"script_{i:02d}", "name": f"query{i:02d}",
            "features": {"loc_code": {"low": 10, "medium": 50,
                                      "high": 200}[band] + i % 3,
                         "max_nesting_depth": i % 4,
                         "subquery_count": i % 5,
                         "source_tables": i % 6,
                         "graph_edges": i % 7},
            "gold": {"migration_complexity": band},
        }

    rows = {r["predictor"]: r for r in biz.trivial_baselines(docs, splits=20)}
    assert rows["loc_code"]["auc_low_vs_high"] == 1.0
    assert rows["loc_code"]["holdout_accuracy"]["mean"] > 0.9


def test_the_constant_predictor_makes_zero_two_band_errors():
    """Why quoting a two-band rate without a baseline says nothing."""
    docs = {
        f"script_{i:02d}": {
            "id": f"script_{i:02d}", "name": f"query{i:02d}",
            "features": {"loc_code": 10 + i},
            "gold": {"migration_complexity": band},
        }
        for i, band in enumerate(CORPUS_BANDS)
    }
    rows = {r["predictor"]: r for r in biz.trivial_baselines(docs, splits=10)}
    constant = rows["constante `medium`"]
    assert constant["error_structure_optimistic"]["two_bands"] == 0.0
    assert constant["optimistic_accuracy"] == pytest.approx(37 / 99, abs=1e-3)
