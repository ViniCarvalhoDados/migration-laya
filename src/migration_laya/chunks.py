"""Feed Laya the SQL itself instead of a summary card.

The card experiment has a circularity problem it cannot escape: the card *lists*
the facts being asked about, so the questions degrade into a reading test that a
logistic regression wins. The only way out is to hand the model the source and
see whether it can find those facts for itself.

The obstacle is the 512-token context. Literally one line at a time would be
5,621 calls and, worse, meaningless — `AND ss_item_sk = i_item_sk` in isolation
says nothing about whether the script has a subquery. So the SQL is split into
the largest windows of whole lines that still fit, and each window is asked
every question independently.

Most scripts never get split: the median script is 44 lines, about 136 tokens.
Only the long tail is chunked at all, which means this is mostly "Laya reads the
whole SQL" with a fallback for the outliers.

**Aggregation is pre-registered here, before any result was seen**, because
picking the rule afterwards is how a null result gets turned into a positive
one:

* `has_subquery`, `has_window_function` — MAX. These are existential: the script
  contains the construct if any window does.
* `needs_human_review` — MAX. If any part needs a human, the script does.
* `migration_complexity` — MAX of the expected score. Difficulty is set by the
  hardest part, not the average one.
* `rewrite_strategy` — the answer from the most confident window.
* `multi_source` — MAX, but this question is **structurally unanswerable by
  window**: "four or more distinct source tables" is a global count, and no
  single window can see the whole FROM list of a long script. It is kept in so
  the cost of chunking shows up in the numbers rather than being argued about.
"""

from __future__ import annotations

import re

# Leaves room for the question text and option descriptions inside the 512-token
# context of the English checkpoint.
WINDOW_TOKEN_BUDGET = 380

_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)

# question -> how its per-window answers combine into one script-level answer
AGGREGATION: dict[str, str] = {
    "has_subquery": "max",
    "has_window_function": "max",
    "multi_source": "max",
    "needs_human_review": "max",
    "migration_complexity": "max",
    "rewrite_strategy": "most_confident",
}

# Questions a window simply cannot answer, kept for the record rather than
# quietly dropped.
STRUCTURALLY_GLOBAL = ("multi_source",)


def approx_tokens(line: str) -> int:
    """Same rough estimator the cards use, so budgets are comparable."""
    words = line.split()
    extra = sum(1 for w in words if any(c.isdigit() for c in w) or "=" in w)
    return max(1, int(len(words) * 1.3 + extra))


def split_sql(sql: str, budget: int = WINDOW_TOKEN_BUDGET) -> list[str]:
    """Largest windows of whole lines that fit the budget.

    Lines are never split: half a predicate is worse than no predicate. A single
    line longer than the budget becomes its own oversized window rather than
    being dropped.
    """
    lines = [
        line.rstrip()
        for line in _COMMENT.sub("", sql).splitlines()
        if line.strip()
    ]
    if not lines:
        return []

    costs = [approx_tokens(line) for line in lines]
    windows: list[str] = []
    start = 0
    while start < len(lines):
        total, end = 0, start
        while end < len(lines) and total + costs[end] <= budget:
            total += costs[end]
            end += 1
        end = max(end, start + 1)          # always make progress
        windows.append("\n".join(lines[start:end]))
        start = end
    return windows


def render_window(window: str, index: int, total: int) -> dict:
    """The state handed to `predict` for one window."""
    state = {"sql": window}
    if total > 1:
        # Say so explicitly: a window is a fragment, and the model should not be
        # led to believe it is seeing the whole script.
        state["note"] = f"Fragment {index + 1} of {total} of one SQL script."
    return state


def aggregate(question: str, answers: list[dict]) -> dict:
    """Combine one question's per-window answers using the pre-registered rule."""
    answers = [a for a in answers if a]
    if not answers:
        return {}
    if len(answers) == 1:
        return dict(answers[0])

    rule = AGGREGATION.get(question, "max")
    if rule == "most_confident":
        best = max(answers, key=lambda a: float(a.get("max_probability") or 0.0))
        return {**best, "n_windows": len(answers), "aggregation": rule}

    kind = answers[0].get("type")
    if kind == "noul":
        winner = max(answers, key=lambda a: float(a.get("value") or 0.0))
    elif kind == "score":
        winner = max(answers, key=lambda a: float(a.get("value") or 0.0))
    else:
        winner = max(answers, key=lambda a: float(a.get("max_probability") or 0.0))
    return {**winner, "n_windows": len(answers), "aggregation": rule}
