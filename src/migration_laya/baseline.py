"""Logistic regression over the same AST features, as the baseline to beat.

Beating the majority class is a low bar. The question a discovery has to answer
is whether a 421M-parameter model earns its place over a few lines of arithmetic
on features we already extract for free — so that is what it is scored against.

Two variants are fitted for every question, and the gap between them is itself a
result:

* **leaky** — every feature, including the ones the gold label is *defined*
  from. `has_subquery` is literally `subquery_count > 0`, so this variant
  reaches ~100% and measures how much of each question the evidence card simply
  hands over.
* **clean** — those defining features removed. This is the honest baseline.

Everything is scored leave-one-out, never fit-and-score on the same rows: the
optimistic-threshold mistake this study already made once is not worth repeating
in its own baseline.

Fitted with L2-regularised Newton-Raphson (IRLS), which converges in a handful
of iterations and — unlike plain gradient descent — does not wander when the
leaky variant makes the classes perfectly separable.
"""

from __future__ import annotations

import numpy as np

# Numeric census columns offered to the model. Deliberately excludes anything
# derived from the rubric score, which would leak every label at once.
FEATURES: tuple[str, ...] = (
    "loc_code", "statements", "cte_count", "cte_max_depth", "subquery_count",
    "scalar_subquery_count", "correlated_subquery_count", "derived_table_count",
    "max_nesting_depth", "scope_count", "window_function_count",
    "distinct_window_specs", "aggregate_count", "source_tables",
    "table_references", "cte_references", "set_operation_count",
    "union_all_count", "intersect_except_count", "case_expression_count",
    "case_max_branches", "graph_nodes", "graph_edges", "graph_density",
    "graph_components", "graph_max_degree", "graph_max_scope_sources",
    "graph_max_scope_edges", "implicit_joins", "explicit_joins",
    "cross_join_risk", "n_nonportable_markers",
)

# Features the gold label is computed from. Leaving them in makes the task
# trivial, which is the point of the "leaky" variant and a trap in the honest
# one.
LEAKY: dict[str, tuple[str, ...]] = {
    "has_subquery": (
        "subquery_count", "scalar_subquery_count", "correlated_subquery_count",
        "derived_table_count", "scope_count", "max_nesting_depth",
    ),
    "has_window_function": ("window_function_count", "distinct_window_specs"),
    "multi_source": (
        "source_tables", "graph_nodes", "table_references", "graph_edges",
        "graph_max_scope_sources", "graph_max_degree", "graph_density",
        "graph_components", "graph_max_scope_edges", "implicit_joins",
        "explicit_joins", "cross_join_risk",
    ),
    # Written by a human/LLM reading the SQL, not computed from features — so
    # nothing leaks and both variants are the same honest baseline.
    "needs_human_review": (),
}


def _standardise(rows: np.ndarray) -> np.ndarray:
    means = rows.mean(axis=0)
    deviations = rows.std(axis=0)
    deviations[deviations == 0] = 1.0
    return (rows - means) / deviations


def fit(rows: np.ndarray, labels: np.ndarray, *, l2: float = 1.0,
        iterations: int = 25, tolerance: float = 1e-8) -> np.ndarray:
    """L2-regularised logistic regression by Newton-Raphson (IRLS).

    The leaky variant is perfectly separable by construction, which sends the
    unpenalised likelihood to infinity; the ridge term is what keeps the fit
    finite and the comparison meaningful.
    """
    design = np.hstack([np.ones((rows.shape[0], 1)), rows])
    beta = np.zeros(design.shape[1])
    penalty = l2 * np.eye(design.shape[1])
    penalty[0, 0] = 0.0                      # never penalise the intercept

    for _ in range(iterations):
        probabilities = 1.0 / (1.0 + np.exp(-np.clip(design @ beta, -35, 35)))
        weights = np.clip(probabilities * (1.0 - probabilities), 1e-9, None)
        gradient = design.T @ (probabilities - labels) + penalty @ beta
        hessian = (design.T * weights) @ design + penalty
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(hessian, gradient, rcond=None)[0]
        beta -= step
        if np.max(np.abs(step)) < tolerance:
            break
    return beta


def predict_proba(model: np.ndarray, rows: np.ndarray) -> np.ndarray:
    design = np.hstack([np.ones((rows.shape[0], 1)), rows])
    return 1.0 / (1.0 + np.exp(-np.clip(design @ model, -35, 35)))


def leave_one_out(rows: np.ndarray, labels: np.ndarray, **kwargs) -> list[float]:
    """Out-of-fold probability for every row.

    Leave-one-out rather than k-fold so there is no seed to tune and the result
    is exactly reproducible; the model is small enough that 99 fits are cheap.
    """
    scaled = _standardise(rows)
    out = []
    for i in range(scaled.shape[0]):
        mask = np.ones(scaled.shape[0], dtype=bool)
        mask[i] = False
        train_labels = labels[mask]
        if len(np.unique(train_labels)) < 2:
            out.append(float(train_labels[0]))
            continue
        model = fit(scaled[mask], train_labels, **kwargs)
        out.append(float(predict_proba(model, scaled[i:i + 1])[0]))
    return out


def feature_vector(features: dict, names: tuple[str, ...]) -> list[float]:
    values = []
    for name in names:
        if name == "n_nonportable_markers":
            markers = features.get("nonportable_markers") or []
            if isinstance(markers, str):
                markers = [m for m in markers.split("|") if m]
            values.append(float(len(markers)))
            continue
        raw = features.get(name, 0)
        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            values.append(0.0)
    return values


def build_baseline(docs: dict, question: str, *, drop_leaky: bool) -> dict:
    """Fit and leave-one-out score the baseline for one binary question."""
    leaky = set(LEAKY.get(question, ()))
    names = tuple(f for f in FEATURES if not (drop_leaky and f in leaky))

    rows, labels, ids = [], [], []
    for script_id, doc in sorted(docs.items()):
        gold = (doc.get("gold") or {}).get(question)
        if not isinstance(gold, bool):
            continue
        rows.append(feature_vector(doc.get("features") or {}, names))
        labels.append(gold)
        ids.append(script_id)

    if len(rows) < 10 or len(set(labels)) < 2:
        return {}

    probabilities = leave_one_out(
        np.asarray(rows, dtype=float), np.asarray(labels, dtype=float))
    hits = sum((p >= 0.5) == g for p, g in zip(probabilities, labels))
    return {
        "question": question,
        "variant": "clean" if drop_leaky else "leaky",
        "n": len(rows),
        "n_features": len(names),
        "dropped": sorted(leaky) if drop_leaky else [],
        "accuracy": round(hits / len(rows), 4),
        "probabilities": dict(zip(ids, probabilities)),
        "labels": dict(zip(ids, labels)),
    }
