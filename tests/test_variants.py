"""Prompt-sensitivity probe tests.

The negation prediction is registered before the run, so the code that checks
it must not be able to drift afterwards.
"""

import pytest

from migration_laya import variants as probe


def _run(scores_by_key, golds):
    names = [f"q{i}" for i in range(len(golds))]
    raw = {
        n: {"answers": {k: {"type": "noul", "value": v[i]}
                        for k, v in scores_by_key.items()}}
        for i, n in enumerate(names)
    }
    docs = {n: {"gold": {"x": golds[i]}} for i, n in enumerate(names)}
    return raw, docs


def test_a_reader_that_inverts_is_detected_as_inverting():
    """v3 asks the opposite; a model that reads should roughly mirror its AUC."""
    golds = [i >= 10 for i in range(20)]
    same = [i / 20 for i in range(20)]
    raw, docs = _run({"x_v1": same, "x_v2": same,
                      "x_v3": [1 - s for s in same]}, golds)
    row = probe.analyse(raw, docs, ["x"])[0]
    assert row["v1"]["auc"] == pytest.approx(1.0)
    assert row["negation"]["inverted"] is True
    assert row["paraphrase_shift"] == pytest.approx(0.0)


def test_a_keyword_matcher_that_ignores_negation_is_caught():
    """Answering v3 the same way as v1 is the signature of pattern matching."""
    golds = [i >= 10 for i in range(20)]
    same = [i / 20 for i in range(20)]
    raw, docs = _run({"x_v1": same, "x_v2": same, "x_v3": same}, golds)
    row = probe.analyse(raw, docs, ["x"])[0]
    assert row["negation"]["predicted_auc"] == pytest.approx(0.0)
    assert row["negation"]["observed_auc"] == pytest.approx(1.0)
    assert row["negation"]["inverted"] is False


def test_paraphrase_shift_measures_the_wording_effect():
    golds = [i >= 10 for i in range(20)]
    strong = [i / 20 for i in range(20)]
    flat = [0.5] * 20
    raw, docs = _run({"x_v1": strong, "x_v2": flat, "x_v3": flat}, golds)
    row = probe.analyse(raw, docs, ["x"])[0]
    assert row["paraphrase_shift"] == pytest.approx(0.5, abs=0.02)


def test_questions_missing_a_variant_are_skipped_not_guessed():
    golds = [i >= 5 for i in range(10)]
    raw, docs = _run({"x_v1": [i / 10 for i in range(10)]}, golds)
    assert probe.analyse(raw, docs, ["x"]) == []


def test_summary_counts_inversions_and_reports_the_worst_shift():
    golds = [i >= 10 for i in range(20)]
    strong = [i / 20 for i in range(20)]
    rows = [
        {"question": "a", "paraphrase_shift": 0.10,
         "negation": {"inverted": True, "predicted_auc": 0.0, "observed_auc": 0.05}},
        {"question": "b", "paraphrase_shift": 0.57,
         "negation": {"inverted": False, "predicted_auc": 0.0, "observed_auc": 0.47}},
    ]
    s = probe.summarise(rows)
    assert s["max_paraphrase_shift"] == pytest.approx(0.57)
    assert s["mean_paraphrase_shift"] == pytest.approx(0.335)
    assert (s["inverted_under_negation"], s["failed_to_invert"]) == (1, 1)


def test_inversion_tolerance_is_explicit_and_tight():
    """A loose tolerance would let a non-inverting model pass as a reader."""
    assert 0.05 <= probe.INVERSION_TOLERANCE <= 0.20
