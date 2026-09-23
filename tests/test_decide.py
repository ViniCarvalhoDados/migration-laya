"""Decision-tree and metrics tests.

The tree's job is to separate a recoverable mistake from an unrecoverable one.
These cases pin that boundary down, since it is what the study's headline
number rests on.
"""

import pytest

from migration_laya.decide import (
    AUTO, HUMAN_REVIEW, ESCALATE, decide, evaluate_question, confidence_band,
)
from migration_laya import metrics

THRESHOLDS = {"high": 0.85, "medium": 0.60}

GOLD = {
    "migration_complexity": "low",
    "has_subquery": False,
    "has_window_function": False,
    "multi_source": True,
}


def noul(value, probability=None):
    p = probability if probability is not None else value
    return {"type": "noul", "value": value, "max_probability": max(p, 1 - p),
            "probabilities": {"true": p, "false": 1 - p}}


def score(low, medium, high):
    return {"type": "score", "value": medium + 2 * high,
            "max_probability": max(low, medium, high),
            "probabilities": {"low": low, "medium": medium, "high": high}}


def answers(subquery=0.02, window=0.02, multi=0.98, complexity=(0.95, 0.04, 0.01)):
    return {
        "migration_complexity": score(*complexity),
        "has_subquery": noul(subquery),
        "has_window_function": noul(window),
        "multi_source": noul(multi),
    }


# --- AUTO --------------------------------------------------------------------

def test_all_facts_right_and_confident_gives_auto():
    d = decide("s", GOLD, answers(), THRESHOLDS)
    assert d.outcome == AUTO


def test_one_correct_but_unsure_fact_drops_out_of_auto():
    """Right for the wrong reasons is still not good enough to skip a human."""
    d = decide("s", GOLD, answers(multi=0.70), THRESHOLDS)
    assert d.outcome == HUMAN_REVIEW
    assert any("only 70% confident" in r for r in d.reasons)


# --- ESCALATE ----------------------------------------------------------------

def test_confidently_wrong_verifiable_fact_escalates():
    """The AST knows there is no subquery; asserting one at 95% is the failure
    mode that destroys trust in production."""
    d = decide("s", GOLD, answers(subquery=0.95), THRESHOLDS)
    assert d.outcome == ESCALATE
    assert any("the AST says" in r for r in d.reasons)


def test_wrong_but_unsure_does_not_escalate():
    d = decide("s", GOLD, answers(subquery=0.62), THRESHOLDS)
    assert d.outcome == HUMAN_REVIEW


def test_complexity_two_bands_out_escalates():
    d = decide("s", GOLD, answers(complexity=(0.05, 0.10, 0.85)), THRESHOLDS)
    assert d.outcome == ESCALATE
    assert any("two bands apart" in r for r in d.reasons)


def test_complexity_one_band_out_is_only_a_review():
    d = decide("s", GOLD, answers(complexity=(0.30, 0.60, 0.10)), THRESHOLDS)
    assert d.outcome == HUMAN_REVIEW
    assert any("one band apart" in r for r in d.reasons)


def test_every_decision_carries_a_reason():
    for kwargs in ({}, {"subquery": 0.95}, {"multi": 0.70},
                   {"complexity": (0.1, 0.2, 0.7)}):
        assert decide("s", GOLD, answers(**kwargs), THRESHOLDS).reasons


# --- question evaluation -----------------------------------------------------

def test_noul_is_thresholded_at_half():
    assert evaluate_question("has_subquery", False, noul(0.49), THRESHOLDS).predicted is False
    assert evaluate_question("has_subquery", False, noul(0.51), THRESHOLDS).predicted is True


def test_confidence_uses_top_probability_not_the_reported_field():
    """The shipped `confidence` is not comparable across question types — a
    score answer reported 0.105 against a 0.53 peak."""
    answer = score(0.15, 0.32, 0.53)
    answer["confidence"] = 0.105
    out = evaluate_question("migration_complexity", "high", answer, THRESHOLDS)
    assert out.confidence == pytest.approx(0.53)


def test_missing_gold_never_counts_as_agreement():
    out = evaluate_question("needs_human_review", None, noul(0.9), THRESHOLDS)
    assert out.agree is False


@pytest.mark.parametrize("value,band", [
    (0.99, "high"), (0.85, "high"), (0.84, "medium"),
    (0.60, "medium"), (0.59, "low"), (0.0, "low"),
])
def test_confidence_bands(value, band):
    assert confidence_band(value, THRESHOLDS) == band


# --- metrics -----------------------------------------------------------------

def _outcomes(*pairs):
    return [{"confidence": c, "agree": a, "gold": True} for c, a in pairs]


def test_perfect_calibration_scores_zero_ece():
    # Ten answers at 100% confidence, all correct.
    ece = metrics.expected_calibration_error(_outcomes(*[(1.0, True)] * 10))
    assert ece["ece"] == pytest.approx(0.0, abs=1e-6)


def test_total_overconfidence_scores_ece_one():
    ece = metrics.expected_calibration_error(_outcomes(*[(1.0, False)] * 10))
    assert ece["ece"] == pytest.approx(1.0, abs=1e-6)


def test_ece_matches_a_hand_computed_case():
    # 4 answers at 0.9 with 50% accuracy (gap 0.4), 4 at 0.5 with 50% (gap 0.0).
    outcomes = _outcomes((0.9, True), (0.9, True), (0.9, False), (0.9, False),
                         (0.5, True), (0.5, True), (0.5, False), (0.5, False))
    ece = metrics.expected_calibration_error(outcomes)
    assert ece["ece"] == pytest.approx(0.5 * 0.4 + 0.5 * 0.0, abs=1e-4)


def test_ece_bins_report_their_support():
    """An ECE quoted without its per-bin counts invites more confidence than a
    ten-script study can support."""
    ece = metrics.expected_calibration_error(_outcomes((0.9, True), (0.5, False)))
    assert sum(b["n"] for b in ece["bins"]) == 2


def test_brier_is_zero_when_certain_and_right():
    assert metrics.brier_score(_outcomes(*[(1.0, True)] * 4)) == pytest.approx(0.0)


def test_brier_is_a_quarter_at_a_coin_flip():
    assert metrics.brier_score(_outcomes((0.5, True), (0.5, False))) == pytest.approx(0.25)


def test_coverage_curve_shrinks_as_the_threshold_rises():
    decisions = [{"questions": _outcomes((0.95, True), (0.75, True), (0.55, False))}]
    curve = metrics.coverage_curve(decisions, thresholds=(0.5, 0.7, 0.9))
    coverages = [p["coverage"] for p in curve]
    assert coverages == sorted(coverages, reverse=True)
    assert curve[-1]["n_kept"] == 1


def test_overconfidence_is_confidence_minus_accuracy():
    decisions = [{"questions": [
        {"question": "q", "confidence": 0.9, "agree": True, "verifiable": True,
         "gradable": True},
        {"question": "q", "confidence": 0.9, "agree": False, "verifiable": True,
         "gradable": True},
    ]}]
    summary = metrics.per_question(decisions)["q"]
    assert summary["accuracy"] == pytest.approx(0.5)
    assert summary["overconfidence"] == pytest.approx(0.4)


# --- ungraded answers --------------------------------------------------------
# Scaling the study to the whole corpus leaves the two judgement questions
# without gold on most scripts. Those answers must be excluded, never counted
# as wrong.

def test_missing_gold_marks_the_outcome_ungradable():
    out = evaluate_question("needs_human_review", None, noul(0.9), THRESHOLDS)
    assert out.gradable is False
    assert out.agree is False


def test_ungraded_answers_do_not_count_as_errors():
    decisions = [{"questions": [
        {"question": "q", "confidence": 0.9, "agree": True, "gradable": True},
        {"question": "q", "confidence": 0.1, "agree": False, "gradable": False},
    ]}]
    summary = metrics.per_question(decisions)["q"]
    assert summary["n"] == 1
    assert summary["ungraded"] == 1
    assert summary["accuracy"] == pytest.approx(1.0)


def test_ungraded_answers_are_excluded_from_calibration():
    outcomes = [
        {"confidence": 1.0, "agree": True, "gradable": True},
        {"confidence": 1.0, "agree": False, "gradable": False},
    ]
    ece = metrics.expected_calibration_error(outcomes)
    assert ece["n"] == 1
    assert ece["ece"] == pytest.approx(0.0, abs=1e-6)
    assert metrics.brier_score(outcomes) == pytest.approx(0.0)


def test_ungraded_answers_are_excluded_from_the_coverage_curve():
    decisions = [{"questions": [
        {"confidence": 0.9, "agree": True, "gradable": True},
        {"confidence": 0.9, "agree": False, "gradable": False},
    ]}]
    curve = metrics.coverage_curve(decisions, thresholds=(0.5,))
    assert curve[0]["n_kept"] == 1
    assert curve[0]["errors"] == 0


def test_a_script_without_judgement_gold_can_still_reach_auto():
    """Most of the corpus has no `rewrite_strategy` gold; that must not block a
    script whose verifiable facts are all correct and confident."""
    gold = {k: v for k, v in GOLD.items()}
    gold["rewrite_strategy"] = None
    answers_with_choice = answers()
    answers_with_choice["rewrite_strategy"] = {
        "type": "choice", "value": "refactor", "max_probability": 0.4,
        "probabilities": {"refactor": 0.4, "redesign": 0.3, "lift_and_shift": 0.3},
    }
    assert decide("s", gold, answers_with_choice, THRESHOLDS).outcome == AUTO


def test_spearman_detects_a_perfect_ranking():
    assert metrics.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert metrics.spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


def test_spearman_averages_tied_ranks():
    """Repeated rubric scores are common, so ties must not skew rho."""
    assert metrics.spearman([1, 1, 2, 2], [1, 1, 2, 2]) == pytest.approx(1.0)


def test_spearman_needs_at_least_three_points():
    assert metrics.spearman([1, 2], [1, 2]) is None


def test_ranking_signal_survives_a_stuck_argmax():
    """The point of the metric: a constant prediction can still hide a usable
    ordering underneath."""
    raw = {
        f"script_{i:02d}": {"answers": {"migration_complexity": {
            "value": 0.8 + 0.05 * i,
            "probabilities": {"low": 0.3, "medium": 0.6, "high": 0.1},
        }}}
        for i in range(5)
    }
    docs = {f"script_{i:02d}": {"gold": {"rubric_points": i * 3}} for i in range(5)}
    signal = metrics.ranking_signal(raw, docs)
    assert signal["n"] == 5
    assert signal["rho_expected_score"] == pytest.approx(1.0)


# --- script-level conjunction ------------------------------------------------

def _script(*confidences, agree=True):
    return {"questions": [
        {"question": q, "confidence": c, "agree": agree, "gradable": True}
        for q, c in zip(("has_subquery", "has_window_function", "multi_source"),
                        confidences)
    ]}


def test_script_coverage_needs_every_question_above_the_cut():
    """Two answers at 0.9 and one at 0.7 does not make a 0.8 script."""
    decisions = [_script(0.9, 0.9, 0.7)]
    curve = {p["threshold"]: p for p in
             metrics.script_level_coverage(decisions, ("has_subquery",
                                                       "has_window_function",
                                                       "multi_source"))}
    assert curve[0.7]["scripts_all_confident"] == 1
    assert curve[0.8]["scripts_all_confident"] == 0


def test_script_coverage_is_never_above_answer_coverage():
    """The conjunction is what the decision tree applies, and it is always at
    least as strict as grading answers independently."""
    questions = ("has_subquery", "has_window_function", "multi_source")
    decisions = [_script(0.9, 0.9, 0.7), _script(0.95, 0.88, 0.86),
                 _script(0.5, 0.5, 0.5)]
    by_script = {p["threshold"]: p["coverage"]
                 for p in metrics.script_level_coverage(decisions, questions)}
    by_answer = {p["threshold"]: p["coverage"]
                 for p in metrics.coverage_curve(decisions)}
    for t in (0.5, 0.6, 0.7, 0.8, 0.85):
        assert by_script[t] <= by_answer[t] + 1e-9, t


def test_script_coverage_skips_scripts_missing_a_question():
    decisions = [{"questions": [
        {"question": "has_subquery", "confidence": 0.99, "agree": True,
         "gradable": True},
    ]}]
    curve = metrics.script_level_coverage(
        decisions, ("has_subquery", "has_window_function", "multi_source"))
    assert all(p["scripts_all_confident"] == 0 for p in curve)


# --- majority-class baseline -------------------------------------------------

def test_a_constant_predictor_scores_exactly_the_baseline():
    """The sharpest failure mode this study found: a model that always answers
    the majority class posts a respectable-looking accuracy while carrying zero
    information. Accuracy must always be reported next to the baseline."""
    decisions = [{"questions": [
        {"question": "q", "gold": g, "predicted": "refactor",
         "agree": g == "refactor", "confidence": 0.6, "gradable": True}
        for g in (["refactor"] * 55 + ["lift_and_shift"] * 35 + ["redesign"] * 10)
    ]}]
    s = metrics.per_question(decisions)["q"]
    assert s["accuracy"] == pytest.approx(0.55)
    assert s["majority_baseline"] == pytest.approx(0.55)
    assert s["lift_over_baseline"] == pytest.approx(0.0)
    assert s["distinct_predictions"] == 1


def test_lift_goes_negative_when_a_model_loses_to_the_baseline():
    """Answering the minority class sometimes can score *below* always
    answering the majority one."""
    golds = [True] * 70 + [False] * 30
    preds = [True] * 54 + [False] * 16 + [True] * 30
    decisions = [{"questions": [
        {"question": "q", "gold": g, "predicted": p, "agree": g == p,
         "confidence": 0.6, "gradable": True}
        for g, p in zip(golds, preds)
    ]}]
    s = metrics.per_question(decisions)["q"]
    assert s["majority_baseline"] == pytest.approx(0.70)
    assert s["accuracy"] < s["majority_baseline"]
    assert s["lift_over_baseline"] < 0


def test_baseline_ignores_ungraded_answers():
    decisions = [{"questions": [
        {"question": "q", "gold": "a", "predicted": "a", "agree": True,
         "confidence": 0.9, "gradable": True},
        {"question": "q", "gold": None, "predicted": "b", "agree": False,
         "confidence": 0.9, "gradable": False},
    ]}]
    s = metrics.per_question(decisions)["q"]
    assert s["n"] == 1
    assert s["majority_baseline"] == pytest.approx(1.0)


# --- ranking quality ---------------------------------------------------------
# Added after an external audit showed that reporting accuracy alone led to the
# wrong verdict: a question can sit inside noise of its baseline and still
# separate the classes almost perfectly.

def _binary(scores_and_golds):
    return [{"score": s, "gold_bool": g, "gradable": True}
            for s, g in scores_and_golds]


def test_auc_is_one_for_a_perfect_ranking():
    assert metrics.roc_auc(_binary([(0.9, True), (0.8, True), (0.2, False)])) == 1.0


def test_auc_is_half_for_no_signal():
    assert metrics.roc_auc(_binary([(0.5, True), (0.5, False)])) == 0.5


def test_auc_below_half_means_inverted_signal_not_absent_signal():
    """AUC 0.22 on `needs_human_review` is the model ranking backwards, which an
    inverted threshold recovers — not the model knowing nothing."""
    outcomes = _binary([(0.1, True), (0.2, True), (0.9, False), (0.8, False)])
    assert metrics.roc_auc(outcomes) == 0.0
    best = metrics.best_threshold(outcomes)
    assert best["inverted"] is True
    assert best["accuracy"] == pytest.approx(1.0)


def test_auc_ignores_the_threshold_entirely():
    """Every score under 0.5 but perfectly ordered: 0% accuracy at the default
    cut-off, AUC still 1.0."""
    outcomes = _binary([(0.4, True), (0.3, True), (0.2, False), (0.1, False)])
    assert metrics.roc_auc(outcomes) == 1.0
    assert sum((o["score"] >= 0.5) == o["gold_bool"] for o in outcomes) == 2
    assert metrics.best_threshold(outcomes)["accuracy"] == pytest.approx(1.0)


def test_auc_needs_both_classes():
    assert metrics.roc_auc(_binary([(0.9, True), (0.8, True)])) is None


def test_mcnemar_calls_a_two_point_gap_noise():
    """The `multi_source` "-2%" that was first reported as a finding."""
    model = [True] * 15 + [False] * 17 + [True] * 67
    base = [False] * 15 + [True] * 17 + [True] * 67
    result = metrics.mcnemar(model, base)
    assert result["discordant"] == 32
    assert result["p_value"] > 0.05


def test_mcnemar_detects_a_real_gap():
    model = [True] * 18 + [False] * 2
    base = [False] * 18 + [True] * 2
    assert metrics.mcnemar(model, base)["p_value"] < 0.01


def test_mcnemar_with_no_disagreement_is_not_significant():
    assert metrics.mcnemar([True] * 10, [True] * 10)["p_value"] == 1.0


def test_wilson_interval_is_wide_at_small_n():
    """"8 scripts, zero errors" must not be quoted as 100%."""
    low, high = metrics.wilson_interval(8, 8)
    assert high == 1.0
    assert low < 0.70          # the true error rate can still exceed 30%


def test_wilson_interval_tightens_as_n_grows():
    narrow = metrics.wilson_interval(800, 800)
    wide = metrics.wilson_interval(8, 8)
    assert narrow[0] > wide[0]


def test_best_threshold_is_flagged_as_fitted_on_its_own_data():
    """Guards the docstring contract: the caller must be able to see that this
    is an optimistic bound, not a deployable setting."""
    doc = " ".join((metrics.best_threshold.__doc__ or "").split())
    assert "OPTIMISTIC UPPER BOUND" in doc
    assert "hold-out" in doc


# --- held-out threshold ------------------------------------------------------

def _points(scores_and_golds):
    return [{"score": s, "gold_bool": g, "gradable": True}
            for s, g in scores_and_golds]


def test_holdout_is_not_more_optimistic_than_the_fitted_bound():
    """The whole point: the in-sample best threshold is a ceiling the held-out
    number must sit under."""
    rng = __import__("random").Random(3)
    points = _points([(rng.random(), rng.random() > 0.5) for _ in range(120)])
    result = metrics.threshold_holdout(points, repeats=60, seed=1)
    assert result["test_accuracy_mean"] <= result["optimistic_accuracy"] + 1e-9
    assert result["hindsight_gap"] >= -1e-9


def test_holdout_on_pure_noise_lands_near_chance():
    """Noise has no threshold to find. If this scored high, the split leaked."""
    rng = __import__("random").Random(11)
    points = _points([(rng.random(), rng.random() > 0.5) for _ in range(200)])
    result = metrics.threshold_holdout(points, repeats=120, seed=5)
    assert result["test_accuracy_mean"] < 0.70


def test_holdout_recovers_a_genuinely_separable_threshold():
    points = _points([(0.1 + i * 0.004, i >= 100) for i in range(200)])
    result = metrics.threshold_holdout(points, repeats=60, seed=5)
    assert result["test_accuracy_mean"] > 0.95
    assert result["hindsight_gap"] < 0.05


def test_holdout_reports_the_spread_across_splits():
    points = _points([(0.2 + i * 0.003, i >= 90) for i in range(180)])
    result = metrics.threshold_holdout(points, repeats=60, seed=2)
    assert result["test_accuracy_p05"] <= result["test_accuracy_mean"]
    assert result["test_accuracy_mean"] <= result["test_accuracy_p95"]
    lo, hi = result["threshold_spread"]
    assert lo <= result["threshold_median"] <= hi


def test_holdout_declines_when_a_class_is_too_small():
    """At n=99 with a 15% positive rate a split can strand a class; below the
    floor the function returns nothing rather than a fragile number."""
    assert metrics.threshold_holdout(_points([(0.5, True)] * 3 + [(0.1, False)] * 40)) == {}
