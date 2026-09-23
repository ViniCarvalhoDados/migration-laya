"""Evidence cards: the compressed state that Laya actually reads.

Laya's English checkpoint has a 512-token context shared between the state, the
instructions and every option description. A 300-line SQL script does not fit,
so the card — not the SQL — is what gets classified. Compressing a script into
~380 tokens without losing what decides its complexity is the real engineering
problem this study is testing.

A card has three parts, deliberately separated:

* ``facts``   — generated from the AST. Never written by hand.
* ``structure`` — a sentence generated from the same facts, because a bag of
  numbers reads poorly to a language model trained on prose.
* ``purpose`` — what the query is *for*, in business terms. This is the only
  part an LLM writes, and the only part the AST cannot produce.
"""

from __future__ import annotations

# Leaves room for the question instructions and option descriptions inside the
# 512-token context. Cards are rejected above this.
TOKEN_BUDGET = 380


def build_facts(features: dict) -> str:
    """The deterministic half of the card: a compact fact line."""
    g = features.get("join_graph") or {}
    parts = [
        f"lines={features.get('loc_code', 0)}",
        f"statements={features.get('statements', 0)}",
        f"sources={features.get('source_tables', 0)}",
        f"joins={g.get('edges', 0)}",
        f"widest_join={g.get('max_scope_sources', 0)}",
        f"subqueries={features.get('subquery_count', 0)}",
        f"correlated={features.get('correlated_subquery_count', 0)}",
        f"ctes={features.get('cte_count', 0)}",
        f"window_fns={features.get('window_function_count', 0)}",
        f"set_ops={features.get('set_operation_count', 0)}",
        f"case_exprs={features.get('case_expression_count', 0)}",
        f"nesting={features.get('max_nesting_depth', 0)}",
    ]
    return " ".join(parts)


def build_structure(features: dict) -> str:
    """The same facts as a sentence, which reads better to a text encoder."""
    g = features.get("join_graph") or {}
    sources = features.get("source_tables", 0)
    shape = g.get("widest_scope_shape", "single")

    bits = [
        f"{_count(features.get('statements', 0), 'statement')} in the file.",
        f"Reads {_count(sources, 'source table')}, joined in a {shape} shape "
        f"with {_count(g.get('edges', 0), 'join predicate')}.",
    ]

    present, absent = [], []
    for label, value in (
        ("CTE", features.get("cte_count", 0)),
        ("subquery", features.get("subquery_count", 0)),
        ("window function", features.get("window_function_count", 0)),
        ("set operation", features.get("set_operation_count", 0)),
        ("CASE expression", features.get("case_expression_count", 0)),
    ):
        (present if value else absent).append(
            _count(value, label) if value else label
        )

    bits.append(f"Uses {_join_list(present)}." if present else "")
    bits.append(f"No {_join_list(absent, 'or')}." if absent else "")

    correlated = features.get("correlated_subquery_count", 0)
    if correlated:
        bits.append(f"{_count(correlated, 'subquery')} correlated with the outer query.")
    depth = features.get("max_nesting_depth", 0)
    if depth:
        bits.append(f"Nests {depth} level{'s' if depth > 1 else ''} deep.")

    markers = features.get("nonportable_markers") or []
    # A single marker arrives as a bare string from some callers; joining that
    # directly would spell it out one letter at a time.
    if isinstance(markers, str):
        markers = [m for m in markers.split("|") if m]
    if markers:
        bits.append("Engine-specific syntax: " + ", ".join(markers[:5]) + ".")

    return " ".join(b for b in bits if b)


def _plural(noun: str) -> str:
    if noun.endswith("y") and not noun.endswith(("ay", "ey", "iy", "oy", "uy")):
        return noun[:-1] + "ies"          # subquery -> subqueries
    return noun + "s"


def _count(n, noun: str) -> str:
    n = int(n or 0)
    return f"{n} {noun if n == 1 else _plural(noun)}"


def _join_list(items: list[str], conjunction: str = "and") -> str:
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + f" {conjunction} " + items[-1]


def render_state(card: dict) -> dict:
    """The dict handed to ``agent.predict`` as the state."""
    return {
        "purpose": card.get("purpose") or "",
        "structure": card.get("structure") or "",
        "metrics": card.get("facts") or "",
    }


def approx_tokens(card: dict) -> int:
    """Rough token count for budget checks.

    A word-and-punctuation estimate rather than the real tokenizer, so the
    budget check runs without loading torch. It overestimates slightly, which
    is the safe direction for a budget.
    """
    text = " ".join(str(v) for v in render_state(card).values())
    words = text.split()
    # Numbers and `key=value` pairs tokenise into several pieces each.
    extra = sum(1 for w in words if any(c.isdigit() for c in w) or "=" in w)
    return int(len(words) * 1.3 + extra)


def check_budget(card: dict, budget: int = TOKEN_BUDGET) -> tuple[bool, int]:
    tokens = approx_tokens(card)
    return tokens <= budget, tokens
