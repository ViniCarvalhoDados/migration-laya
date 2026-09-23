"""Logistic-regression baseline tests.

This baseline exists because beating the majority class proves nothing. If it is
itself wrong, the comparison it supports is worthless — so its two properties
that matter are pinned here: it must actually learn, and it must be scored out
of fold.
"""

import numpy as np
import pytest

from migration_laya import baseline as lr


def _separable(n=60):
    rows = [[float(i), float(i % 3)] for i in range(n)]
    labels = [i >= n / 2 for i in range(n)]
    return np.array(rows), np.array(labels, dtype=float)


def test_fit_learns_a_separable_problem():
    rows, labels = _separable()
    scaled = lr._standardise(rows)
    model = lr.fit(scaled, labels)
    predictions = lr.predict_proba(model, scaled) >= 0.5
    assert (predictions == labels.astype(bool)).mean() == 1.0


def test_fit_stays_finite_on_perfectly_separable_data():
    """The leaky variant is separable by construction, which sends an
    unpenalised likelihood to infinity. The ridge term is what keeps it finite."""
    rows, labels = _separable()
    model = lr.fit(lr._standardise(rows), labels, l2=1.0)
    assert np.all(np.isfinite(model))
    assert np.max(np.abs(model)) < 1e6


def test_fit_is_deterministic():
    rows, labels = _separable()
    scaled = lr._standardise(rows)
    assert np.allclose(lr.fit(scaled, labels), lr.fit(scaled, labels))


def test_standardise_centres_and_scales():
    rows = np.array([[1.0, 10.0], [3.0, 30.0], [5.0, 50.0]])
    scaled = lr._standardise(rows)
    assert np.allclose(scaled.mean(axis=0), 0.0, atol=1e-9)
    assert np.allclose(scaled.std(axis=0), 1.0, atol=1e-9)


def test_standardise_survives_a_constant_column():
    """Several census features are zero for the whole corpus."""
    rows = np.array([[1.0, 7.0], [2.0, 7.0], [3.0, 7.0]])
    scaled = lr._standardise(rows)
    assert np.all(np.isfinite(scaled))
    assert np.allclose(scaled[:, 1], 0.0)


def test_leave_one_out_never_trains_on_the_row_it_scores():
    """Pure noise must score near chance. If the fold leaked, it would not."""
    rng = np.random.default_rng(0)
    rows = rng.normal(size=(60, 4))
    labels = np.array([i % 2 for i in range(60)], dtype=float)
    probabilities = lr.leave_one_out(rows, labels)
    accuracy = sum((p >= 0.5) == bool(g) for p, g in zip(probabilities, labels)) / 60
    assert accuracy < 0.75          # an in-sample fit would sail past this


def test_leave_one_out_returns_one_probability_per_row():
    rows, labels = _separable(30)
    assert len(lr.leave_one_out(rows, labels)) == 30
    assert all(0.0 <= p <= 1.0 for p in lr.leave_one_out(rows, labels))


def test_leave_one_out_handles_a_degenerate_fold():
    rows = np.array([[float(i)] for i in range(12)])
    labels = np.array([1.0] + [0.0] * 11)
    probabilities = lr.leave_one_out(rows, labels)
    assert len(probabilities) == 12
    assert all(np.isfinite(probabilities))


# --- leakage bookkeeping -----------------------------------------------------

@pytest.mark.parametrize("question,feature", [
    ("has_subquery", "subquery_count"),
    ("has_window_function", "window_function_count"),
    ("multi_source", "source_tables"),
])
def test_the_defining_feature_is_declared_leaky(question, feature):
    """Each verifiable gold label IS a threshold on one census feature. Leaving
    it in the honest baseline would make the comparison meaningless."""
    assert feature in lr.LEAKY[question]


def test_judgement_questions_have_nothing_to_leak():
    """`needs_human_review` is written by reading the SQL, not computed from
    features, so both variants are the same honest baseline."""
    assert lr.LEAKY["needs_human_review"] == ()


def test_clean_variant_actually_drops_the_leaky_features():
    docs = {
        f"script_{i:02d}": {
            "gold": {"has_subquery": i % 2 == 0},
            "features": {name: float(i) for name in lr.FEATURES},
        }
        for i in range(20)
    }
    leaky = lr.build_baseline(docs, "has_subquery", drop_leaky=False)
    clean = lr.build_baseline(docs, "has_subquery", drop_leaky=True)
    assert leaky["n_features"] == len(lr.FEATURES)
    assert clean["n_features"] < leaky["n_features"]
    assert set(clean["dropped"]) == set(lr.LEAKY["has_subquery"])


def test_build_baseline_skips_scripts_without_a_boolean_gold():
    docs = {
        "script_01": {"gold": {"has_subquery": True},
                      "features": {n: 1.0 for n in lr.FEATURES}},
        "script_02": {"gold": {"has_subquery": None},
                      "features": {n: 2.0 for n in lr.FEATURES}},
    }
    assert lr.build_baseline(docs, "has_subquery", drop_leaky=True) == {}


def test_feature_vector_counts_marker_lists_and_survives_strings():
    names = ("loc_code", "n_nonportable_markers")
    assert lr.feature_vector(
        {"loc_code": 12, "nonportable_markers": ["rollup", "cube"]}, names
    ) == [12.0, 2.0]
    # The CSV round-trip can hand back a "|"-joined string instead of a list.
    assert lr.feature_vector(
        {"loc_code": "12", "nonportable_markers": "rollup|cube"}, names
    ) == [12.0, 2.0]
    assert lr.feature_vector({}, names) == [0.0, 0.0]
