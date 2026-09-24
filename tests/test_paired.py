"""Tests for the paired comparison, and for the unfairness it was built to fix.

The property that matters here is not that Laya wins or loses — it is that the
comparison is *symmetric*. An external audit found that E8 and E10 compared Laya
against the regression variant that had been deliberately blinded to the very
facts the evidence card prints, which inflated Laya's margin. So the arm every
number is reported against is pinned by a test.
"""

import pytest

from migration_laya import baseline as lr
from migration_laya import paired


def _docs(n: int = 60) -> dict:
    """Scripts whose `has_subquery` gold is exactly `subquery_count > 0`."""
    docs = {}
    for i in range(n):
        subqueries = i % 4
        docs[f"script_{i:02d}"] = {
            "id": f"script_{i:02d}",
            "name": f"query{i:02d}",
            "features": {
                "subquery_count": subqueries,
                "loc_code": 20 + i,
                "source_tables": 2 + (i % 5),
                "window_function_count": i % 3,
            },
            "gold": {"has_subquery": subqueries > 0},
        }
    return docs


def _scores(docs: dict, *, noise: float) -> dict[str, float]:
    """P(true) that tracks the gold, degraded by a deterministic offset."""
    out = {}
    for i, (script_id, doc) in enumerate(sorted(docs.items())):
        gold = doc["gold"]["has_subquery"]
        base = 0.9 if gold else 0.1
        out[script_id] = base + (noise if i % 3 == 0 else -noise)
    return out


def test_leaky_arm_sees_the_defining_feature_and_clean_arm_does_not():
    """The two arms differ by exactly the features the gold is defined from."""
    docs = _docs()
    _, _, _, clean = paired._design(docs, "has_subquery", drop_leaky=True)
    _, _, _, leaky = paired._design(docs, "has_subquery", drop_leaky=False)

    assert "subquery_count" in leaky
    assert "subquery_count" not in clean
    assert set(clean) < set(leaky)


def test_both_regression_arms_are_reported():
    """Neither arm may be silently dropped: the gap between them is the finding."""
    docs = _docs()
    result = paired.compare(docs, "has_subquery", _scores(docs, noise=0.05),
                            splits=20)

    assert set(result["differences"]) == {
        "laya_minus_lr_clean", "laya_minus_lr_leaky", "laya_minus_majority",
    }
    assert set(result["accuracy"]) == {
        "laya", "lr_clean", "lr_leaky", "majority",
    }


def test_the_equally_informed_arm_is_the_harder_one():
    """A regression handed the defining feature beats one denied it.

    This is the whole point of reporting both: a margin measured against the
    clean arm partly measures the handicap, not the model.
    """
    docs = _docs()
    result = paired.compare(docs, "has_subquery", _scores(docs, noise=0.05),
                            splits=20)

    assert (result["accuracy"]["lr_leaky"]["mean"]
            > result["accuracy"]["lr_clean"]["mean"])
    assert (result["differences"]["laya_minus_lr_leaky"]["mean"]
            < result["differences"]["laya_minus_lr_clean"]["mean"])


def test_verdict_only_calls_a_winner_when_the_spread_clears_zero():
    assert paired._verdict({"p05": 0.02, "p95": 0.20}) == "vence"
    assert paired._verdict({"p05": -0.20, "p95": -0.02}) == "perde"
    assert paired._verdict({"p05": -0.05, "p95": 0.12}) == "empate"
    # Touching zero is not clearing it.
    assert paired._verdict({"p05": 0.0, "p95": 0.18}) == "empate"


def test_threshold_is_fitted_on_train_only():
    """A polarity-inverted signal must not be rescued by the test half."""
    docs = _docs()
    scores = {k: 1.0 - v for k, v in _scores(docs, noise=0.05).items()}
    result = paired.compare(docs, "has_subquery", scores, splits=20)

    # The fit is allowed to discover the inversion on train, so accuracy stays
    # high — but it is measured only on rows the threshold never saw.
    assert result["accuracy"]["laya"]["mean"] > 0.8
    assert result["splits"] == 20


def test_scores_are_matched_by_origin_query_not_script_id():
    """Ids are reassigned when the sample changes; origins are not."""
    docs = _docs(30)
    raw = {
        "script_99": {"script_id": "script_99", "origin": "query07",
                      "answers": {"has_subquery": {"value": 0.8}}},
    }
    scores = paired.aggregate_scores(raw, docs, "has_subquery")
    assert scores == {"script_07": 0.8}


def test_paraphrases_are_averaged_without_seeing_gold():
    docs = _docs(30)
    raw = {
        "script_07": {"script_id": "script_07", "origin": "query07",
                      "answers": {"has_subquery_p1": {"value": 0.6},
                                  "has_subquery_p2": {"value": 0.8}}},
    }
    scores = paired.aggregate_scores(raw, docs, "has_subquery",
                                     ["has_subquery_p1", "has_subquery_p2"])
    assert scores["script_07"] == pytest.approx(0.7)


def test_a_script_missing_one_wording_is_dropped_whole():
    docs = _docs(30)
    raw = {
        "script_07": {"script_id": "script_07", "origin": "query07",
                      "answers": {"has_subquery_p1": {"value": 0.6}}},
    }
    scores = paired.aggregate_scores(raw, docs, "has_subquery",
                                     ["has_subquery_p1", "has_subquery_p2"])
    assert scores == {}


def test_every_arm_is_scored_on_the_same_scripts():
    """Dropping a script for one arm and not the others would skew the gap."""
    docs = _docs()
    scores = _scores(docs, noise=0.05)
    scores.pop("script_00")
    scores.pop("script_01")
    result = paired.compare(docs, "has_subquery", scores, splits=10)
    assert result["n"] == len(docs) - 2
