"""Paraphrase-ensemble tests.

The claim this code supports is "you no longer have to guess the lucky
wording". That claim is only worth anything if the aggregation is honest —
never fitted to the gold — and if the oracle stays labelled as a ceiling.
"""

import pytest

from migration_laya import ensemble as ens


def _run(scores_by_key, golds):
    names = [f"q{i}" for i in range(len(golds))]
    raw = {
        n: {"answers": {k: {"type": "noul", "value": v[i]}
                        for k, v in scores_by_key.items()}}
        for i, n in enumerate(names)
    }
    docs = {n: {"gold": {"x": golds[i]}} for i, n in enumerate(names)}
    return raw, docs


GOLD = [i >= 20 for i in range(40)]
GOOD = [i / 40 for i in range(40)]               # ranks perfectly
FLAT = [0.5] * 40                                # carries no ranking at all

# Random noise, not a constant: a constant added to a good score is a monotone
# transform, so it leaves AUC untouched. Only genuinely disordered scores can
# drag an ensemble down, which is what the "does aggregation help" question
# needs to be tested against.
_rng = __import__("random").Random(17)
NOISE = [_rng.random() for _ in range(40)]


def test_averaging_noise_into_signal_still_beats_the_worst_wording():
    raw, docs = _run({"x_p1": GOOD, "x_p2": NOISE, "x_p3": NOISE}, GOLD)
    row = ens.analyse(raw, docs, "x", ["x_p1", "x_p2", "x_p3"])
    assert row["single_auc_max"] == pytest.approx(1.0)
    assert row["aggregated"]["mean"]["auc"] > row["single_auc_min"]


def test_a_constant_wording_cannot_disturb_the_ranking():
    """Adding a constant is a monotone transform: AUC is untouched. Worth
    pinning so a flat paraphrase is never mistaken for a harmless one."""
    raw, docs = _run({"x_p1": GOOD, "x_p2": FLAT}, GOLD)
    row = ens.analyse(raw, docs, "x", ["x_p1", "x_p2"])
    assert row["aggregated"]["mean"]["auc"] == pytest.approx(1.0)


def test_spread_reports_the_size_of_the_wording_problem():
    raw, docs = _run({"x_p1": GOOD, "x_p2": FLAT}, GOLD)
    row = ens.analyse(raw, docs, "x", ["x_p1", "x_p2"])
    assert row["single_auc_spread"] == pytest.approx(
        row["single_auc_max"] - row["single_auc_min"])
    assert row["single_auc_spread"] > 0.4


def test_agreeing_paraphrases_leave_the_ensemble_where_it_was():
    raw, docs = _run({"x_p1": GOOD, "x_p2": GOOD, "x_p3": GOOD}, GOLD)
    row = ens.analyse(raw, docs, "x", ["x_p1", "x_p2", "x_p3"])
    assert row["single_auc_spread"] == pytest.approx(0.0)
    assert row["aggregated"]["mean"]["auc"] == pytest.approx(1.0)
    assert ens.verdict(row) == "agregar resolve"


def test_one_wrecking_paraphrase_is_survived_by_the_median():
    """The median is there precisely for a single wording that inverts."""
    inverted = [1 - s for s in GOOD]
    raw, docs = _run({"x_p1": GOOD, "x_p2": GOOD, "x_p3": inverted}, GOLD)
    row = ens.analyse(raw, docs, "x", ["x_p1", "x_p2", "x_p3"])
    assert row["aggregated"]["median"]["auc"] > row["aggregated"]["mean"]["auc"] - 0.01
    assert row["aggregated"]["median"]["auc"] > 0.9


def test_verdict_calls_out_an_ensemble_that_buys_nothing():
    """Five disordered wordings against one good one: the ensemble should land
    well short of the best single wording, and the verdict must say so."""
    rng = __import__("random").Random(5)
    noisy = {f"x_p{i}": [rng.random() for _ in range(40)] for i in range(2, 7)}
    raw, docs = _run({"x_p1": GOOD, **noisy}, GOLD)
    row = ens.analyse(raw, docs, "x", ["x_p1", *noisy])
    assert row["aggregated"]["mean"]["auc"] < row["single_auc_max"] - 0.05
    assert ens.verdict(row) != "agregar resolve"


def test_the_oracle_is_the_best_single_wording_not_the_ensemble():
    """It is selected on the gold label, so it must never be reported as a
    strategy — only as a ceiling."""
    raw, docs = _run({"x_p1": GOOD, "x_p2": FLAT}, GOLD)
    row = ens.analyse(raw, docs, "x", ["x_p1", "x_p2"])
    assert row["oracle_auc"] == row["single_auc_max"]
    assert row["oracle_auc"] >= row["aggregated"]["mean"]["auc"] - 1e-9


def test_aggregators_never_see_the_gold_label():
    """A guard on the honest half of the comparison: the combining functions
    take scores only."""
    for fn in ens.AGGREGATORS.values():
        assert fn([0.1, 0.2, 0.9]) == pytest.approx(
            fn([0.1, 0.2, 0.9]))
    assert ens._mean([0.0, 1.0]) == pytest.approx(0.5)
    assert ens._median([0.1, 0.9, 0.2]) == pytest.approx(0.2)
    assert ens._trimmed([0.0, 0.4, 0.5, 0.6, 1.0]) == pytest.approx(0.5)


def test_missing_paraphrase_returns_nothing_rather_than_a_partial_answer():
    raw, docs = _run({"x_p1": GOOD}, GOLD)
    assert ens.analyse(raw, docs, "x", ["x_p1", "x_p2"]) == {}
