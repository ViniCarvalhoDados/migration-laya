"""Thin wrapper around the Laya runtime.

Three jobs beyond calling ``predict``:

* **Timing.** Every call is measured so each script carries a real latency, and
  a calibration pass fits a cost model so a run can be estimated before it is
  paid for.
* **Shape normalisation.** The shipped result does not match the published
  docs — a ``score`` answer returns ``probabilities`` keyed ``"0"``/``"1"``/...
  with a ``legend``, not a ``distribution`` list. Normalising once here keeps
  that surprise out of the scoring code.
* **Calibration warnings.** The checkpoint emits a RuntimeWarning saying its
  temperatures are invalid and its confidences are uncalibrated. That is
  material to every conclusion in this study, so it is captured and carried
  into the run record rather than being lost to stderr.
"""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml

DEFAULT_MODEL = "convaiinnovations/laya"


@dataclass
class Answer:
    question: str
    type: str
    value: Any = None            # the chosen label, score, or P(true)
    label: str = ""              # human-readable form of `value`
    reported_confidence: float = 0.0
    max_probability: float = 0.0  # our own read: the top probability mass
    probabilities: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Prediction:
    script_id: str
    # The origin query name travels with the answers. `script_id` is assigned by
    # the sampler and is reused for a different query whenever the sample size
    # changes, so a run recorded under ids alone silently re-pairs itself with
    # the wrong gold labels on any later re-scoring.
    origin: str = ""
    answers: dict[str, dict] = field(default_factory=dict)
    input_tokens: int = 0
    elapsed_ms: float = 0.0
    ms_per_question: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


class LayaClient:
    def __init__(self, model: str = DEFAULT_MODEL, device: str = "cpu",
                 subfolder: str | None = None):
        self.model = model
        self.device = device
        self.subfolder = subfolder
        self.load_seconds = 0.0
        self.warnings: list[str] = []
        self._agent = None

    def load(self):
        if self._agent is not None:
            return self._agent
        import laya

        start = time.perf_counter()
        # The checkpoint warns about invalid temperatures at load time. It goes
        # to stderr and would otherwise vanish from the record.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            kwargs = {"device": self.device}
            if self.subfolder:
                kwargs["subfolder"] = self.subfolder
            self._agent = laya.load(self.model, **kwargs)
        self.load_seconds = round(time.perf_counter() - start, 3)
        self.warnings = [str(w.message) for w in caught]
        return self._agent

    def predict(self, script_id: str, state: dict, questions: dict,
                origin: str = "") -> Prediction:
        agent = self.load()
        start = time.perf_counter()
        raw = agent.predict(state, questions)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        answers = {
            key: normalise_answer(key, body).as_dict()
            for key, body in (raw.get("answers") or {}).items()
        }
        n = max(1, len(answers))
        return Prediction(
            script_id=script_id,
            origin=origin,
            answers=answers,
            input_tokens=int((raw.get("usage") or {}).get("input_tokens", 0)),
            elapsed_ms=round(elapsed_ms, 1),
            ms_per_question=round(elapsed_ms / n, 1),
        )


def normalise_answer(key: str, body: dict) -> Answer:
    """Flatten one Laya answer into a stable record.

    `max_probability` is computed here rather than trusting `confidence`: for
    `score` answers the shipped confidence is not the top probability (0.105
    reported against a 0.53 peak), so the two are kept side by side and the
    decision tree can be explicit about which one it uses.
    """
    kind = body.get("type", "")
    probabilities = body.get("probabilities") or {}
    a = Answer(
        question=key,
        type=kind,
        reported_confidence=_f(body.get("confidence")),
        probabilities={k: _f(v) for k, v in probabilities.items()},
    )

    if kind == "choice":
        a.value = body.get("choice")
        a.label = str(a.value)
    elif kind == "score":
        a.value = _f(body.get("score"))
        legend = body.get("legend") or {}
        if probabilities:
            top = max(probabilities, key=lambda k: _f(probabilities[k]))
            a.label = str(legend.get(top, top))
        # Re-key the distribution by its legend text so downstream code never
        # has to carry the "0"/"1"/"2" indirection.
        if legend:
            a.probabilities = {
                str(legend.get(k, k)): _f(v) for k, v in probabilities.items()
            }
    elif kind == "noul":
        a.value = _f(body.get("noul"))
        a.label = "true" if a.value >= 0.5 else "false"
        a.probabilities = {"true": a.value, "false": round(1.0 - a.value, 6)}

    a.max_probability = max(a.probabilities.values(), default=0.0)
    return a


def _f(x) -> float:
    try:
        return round(float(x), 6)
    except (TypeError, ValueError):
        return 0.0


# --- latency ----------------------------------------------------------------

# The real evidence cards land around 70-100 tokens; the wider points bracket
# the 380-token budget so the fit covers the whole allowed range.
CALIBRATION_SIZES: tuple[int, ...] = (50, 100, 200, 380)

# Context limit of the English checkpoint, per forward pass.
CONTEXT_LIMIT = 512


def calibrate_latency(client: LayaClient, questions: dict,
                      sizes: tuple[int, ...] = CALIBRATION_SIZES,
                      repeats: int = 3) -> dict:
    """Measure how latency moves with card size, and fit a cost model.

    Gives an up-front estimate for a run instead of discovering the cost after
    paying it. The fit is against *card* tokens, not the reported
    ``input_tokens``: the card size is what we know before calling, and
    ``input_tokens`` turns out to be the sum over all questions (one forward
    pass each) rather than a single context.
    """
    n_questions = max(1, len(questions))
    samples: list[dict] = []

    for card_tokens in sizes:
        state = {"card": _filler(card_tokens)}
        timings, total_tokens = [], 0
        for i in range(repeats + 1):
            prediction = client.predict("calibration", state, questions)
            total_tokens = prediction.input_tokens
            if i:  # discard the first pass: it warms caches
                timings.append(prediction.elapsed_ms)
        per_question_tokens = round(total_tokens / n_questions)
        samples.append({
            "card_tokens": card_tokens,
            "input_tokens_total": total_tokens,
            "tokens_per_question": per_question_tokens,
            "fits_context": per_question_tokens <= CONTEXT_LIMIT,
            "ms_median": round(sorted(timings)[len(timings) // 2], 1),
            "ms_min": round(min(timings), 1),
            "ms_max": round(max(timings), 1),
            "ms_per_question": round(sorted(timings)[len(timings) // 2] / n_questions, 1),
        })

    slope, intercept = _fit_line(
        [s["card_tokens"] for s in samples], [s["ms_median"] for s in samples]
    )
    overflow = [s["card_tokens"] for s in samples if not s["fits_context"]]
    return {
        "device": client.device,
        "model": client.model,
        "n_questions": n_questions,
        "load_seconds": client.load_seconds,
        "context_limit_per_question": CONTEXT_LIMIT,
        "card_sizes_overflowing_context": overflow,
        "samples": samples,
        "model_fit": {
            "ms_per_card_token": round(slope, 4),
            "intercept_ms": round(intercept, 1),
            "n_questions": n_questions,
            "formula": (
                "estimated_ms = intercept_ms + ms_per_card_token * card_tokens "
                f"(for {n_questions} questions, {client.device})"
            ),
        },
        "warnings": client.warnings,
    }


def estimate_ms(card_tokens: int, fit: dict) -> float:
    """Predicted wall-clock for one script's full question set."""
    return round(
        fit.get("intercept_ms", 0.0) + fit.get("ms_per_card_token", 0.0) * card_tokens, 1
    )


def _fit_line(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Ordinary least squares on a handful of points."""
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return 0.0, mean_y
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator
    return slope, mean_y - slope * mean_x


_FILLER_WORDS = (
    "select sum of extended sales price joined against the date dimension and "
    "the item dimension grouped by category class and brand with a filter on "
    "the reporting month and a threshold on quantity sold "
)


def _filler(target_tokens: int) -> str:
    """Realistic-looking English of roughly the requested token count."""
    words = _FILLER_WORDS.split()
    needed = max(1, int(target_tokens * 0.85))
    return " ".join(words[i % len(words)] for i in range(needed))


def load_yaml(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
