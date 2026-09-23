"""The decision tree: what happens to each script after Laya answers.

Three outcomes, and the distinction that matters is not right-vs-wrong but
*confidently* wrong on something the AST already knew:

* ``AUTO``          — every verifiable fact correct at high confidence and the
                      complexity band matches. No human needed.
* ``HUMAN_REVIEW``  — a near miss, or a correct answer the model was unsure of.
                      A person confirms; cost is a glance, not an investigation.
* ``ESCALATE``      — a confident error. This is the outcome that destroys trust
                      in production, and the whole reason the study grades
                      against a deterministic ground truth: a classifier that is
                      merely wrong is manageable, one that is wrong and sure of
                      itself is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from .rubric import band_distance

# Questions the AST answers outright. A disagreement here is unambiguous.
VERIFIABLE = ("has_subquery", "has_window_function", "multi_source")

AUTO = "AUTO"
HUMAN_REVIEW = "HUMAN_REVIEW"
ESCALATE = "ESCALATE"


@dataclass
class QuestionOutcome:
    question: str
    gold: object = None
    predicted: object = None
    agree: bool = False
    # False when no gold label exists for this script/question pair. Ungraded
    # answers must be excluded from accuracy and calibration rather than
    # counted as wrong — scaling the corpus leaves the judgement questions
    # without gold on most scripts, and treating those as errors would report
    # a failure that was never measured.
    gradable: bool = True
    confidence: float = 0.0
    confidence_band: str = ""
    verifiable: bool = False
    band_gap: int = 0          # complexity only: how many tiers apart

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Decision:
    script_id: str
    outcome: str = HUMAN_REVIEW
    reasons: list[str] = field(default_factory=list)
    questions: list[dict] = field(default_factory=list)
    elapsed_ms: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


def confidence_band(value: float, thresholds: dict) -> str:
    if value >= thresholds.get("high", 0.85):
        return "high"
    if value >= thresholds.get("medium", 0.60):
        return "medium"
    return "low"


def _confidence_of(answer: dict) -> float:
    """Which number to treat as the model's confidence.

    The shipped `confidence` is not comparable across question types — a `score`
    answer reported 0.105 against a 0.53 peak probability. The top probability
    mass is the consistent reading, so it is what the tree uses; the reported
    value is still carried through to the report for comparison.
    """
    return float(answer.get("max_probability") or 0.0)


def evaluate_question(key: str, gold, answer: dict, thresholds: dict) -> QuestionOutcome:
    confidence = _confidence_of(answer)
    out = QuestionOutcome(
        question=key,
        gold=gold,
        gradable=gold is not None,
        confidence=round(confidence, 4),
        confidence_band=confidence_band(confidence, thresholds),
        verifiable=key in VERIFIABLE,
    )

    kind = answer.get("type")
    if kind == "noul":
        out.predicted = bool(float(answer.get("value") or 0.0) >= 0.5)
        out.agree = (gold is not None) and (bool(gold) == out.predicted)
    elif kind == "choice":
        out.predicted = answer.get("value")
        out.agree = (gold is not None) and (str(gold) == str(out.predicted))
    elif kind == "score":
        out.predicted = _band_from_score(answer)
        out.agree = (gold is not None) and (str(gold) == str(out.predicted))
        out.band_gap = band_distance(str(gold), str(out.predicted)) if gold else 99
    return out


# The score question's three levels correspond to the three complexity bands.
_SCORE_BANDS = ("low", "medium", "high")


def _band_from_score(answer: dict) -> str:
    """Map a `score` answer onto a complexity band via its top probability."""
    probabilities = answer.get("probabilities") or {}
    if not probabilities:
        value = float(answer.get("value") or 0.0)
        return _SCORE_BANDS[min(len(_SCORE_BANDS) - 1, max(0, int(round(value))))]
    top = max(probabilities, key=lambda k: probabilities[k])
    # Probabilities are keyed by the criteria text; position carries the band.
    keys = list(probabilities)
    return _SCORE_BANDS[min(keys.index(top), len(_SCORE_BANDS) - 1)]


def decide(script_id: str, gold: dict, answers: dict, thresholds: dict,
           elapsed_ms: float = 0.0) -> Decision:
    decision = Decision(script_id=script_id, elapsed_ms=elapsed_ms)
    outcomes = [
        evaluate_question(key, gold.get(key), answer, thresholds)
        for key, answer in answers.items()
    ]
    decision.questions = [o.as_dict() for o in outcomes]

    by_key = {o.question: o for o in outcomes}
    verifiable = [o for o in outcomes if o.verifiable and o.gradable]
    complexity = by_key.get("migration_complexity")
    if complexity is not None and not complexity.gradable:
        complexity = None
    high_cut = thresholds.get("high", 0.85)

    # ESCALATE: confidently wrong about something the AST already knew.
    confident_errors = [
        o for o in verifiable if not o.agree and o.confidence >= high_cut
    ]
    for o in confident_errors:
        decision.reasons.append(
            f"{o.question}: answered {o.predicted} at {o.confidence:.0%} "
            f"but the AST says {o.gold}"
        )
    if complexity and complexity.band_gap >= 2:
        decision.reasons.append(
            f"migration_complexity: {complexity.predicted} vs gold "
            f"{complexity.gold} — two bands apart"
        )
    if decision.reasons:
        decision.outcome = ESCALATE
        return decision

    # AUTO: everything verifiable right and confident, complexity on the nose.
    all_facts_right = all(o.agree for o in verifiable)
    all_facts_confident = all(o.confidence >= high_cut for o in verifiable)
    complexity_exact = bool(complexity and complexity.agree)

    if all_facts_right and all_facts_confident and complexity_exact:
        decision.outcome = AUTO
        decision.reasons.append(
            f"all {len(verifiable)} verifiable facts correct at >={high_cut:.0%} "
            "and complexity band matches"
        )
        return decision

    # Everything else is a near miss worth one person's glance.
    decision.outcome = HUMAN_REVIEW
    for o in verifiable:
        if not o.agree:
            decision.reasons.append(
                f"{o.question}: wrong but only {o.confidence:.0%} confident"
            )
        elif o.confidence < high_cut:
            decision.reasons.append(
                f"{o.question}: correct but only {o.confidence:.0%} confident"
            )
    if complexity and not complexity.agree:
        decision.reasons.append(
            f"migration_complexity: {complexity.predicted} vs gold "
            f"{complexity.gold} — one band apart"
        )
    if not decision.reasons:
        decision.reasons.append("held for review by default")
    return decision
