"""Deterministic feature extraction from a SQL file.

Everything here is derived from the sqlglot AST, never from an LLM. These
numbers are the study's ground truth: the rubric scores complexity from them and
the Laya answers are graded against them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from .graph import build_join_graph

# Tried in order; the first dialect that parses the whole file wins. A legacy
# corpus is rarely written in one dialect, and which one it needed is itself a
# migration signal (TPC-DS q67 uses T-SQL `SELECT TOP`).
DIALECT_CASCADE: tuple[str, ...] = ("spark", "tsql", "presto", "duckdb")

# Raw-text markers of engine-specific syntax. Matched on the source rather than
# the AST because sqlglot normalises several of these away on parse.
_SYNTAX_MARKERS: tuple[tuple[str, str], ...] = (
    ("rollup", r"\brollup\s*\("),
    ("cube", r"\bcube\s*\("),
    ("grouping_sets", r"\bgrouping\s+sets\b"),
    ("grouping_fn", r"\bgrouping\s*\("),
    ("select_top", r"\bselect\s+top\b"),
    ("backtick_identifier", r"`[^`]+`"),
    ("interval_arithmetic", r"\binterval\s+["+"'\"]"),
    ("qualify", r"\bqualify\b"),
    ("connect_by", r"\bconnect\s+by\b"),
    ("decode_fn", r"\bdecode\s*\("),
    ("nvl_fn", r"\bnvl\s*\("),
    ("rownum", r"\brownum\b"),
    ("oracle_outer_join", r"\(\+\)"),
    ("stddev_samp", r"\bstddev_samp\s*\("),
    ("listagg", r"\blistagg\s*\(|\bstring_agg\s*\(|\bgroup_concat\s*\("),
)

_COMMENT_RE = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)

# Nodes sqlglot models as Func but which are not function calls in any sense a
# migration engineer cares about.
_NOT_REALLY_FUNCTIONS = (exp.Connector, exp.Case, exp.If, exp.Cast)


@dataclass
class Features:
    # identity
    name: str = ""
    path: str = ""
    # parse
    parse_ok: bool = False
    parse_dialect: str = ""
    parse_error: str = ""
    # size
    loc: int = 0
    loc_code: int = 0
    chars: int = 0
    statements: int = 0
    # structure
    cte_count: int = 0
    cte_max_depth: int = 0
    subquery_count: int = 0
    scalar_subquery_count: int = 0
    correlated_subquery_count: int = 0
    derived_table_count: int = 0
    max_nesting_depth: int = 0
    scope_count: int = 0
    # analytic
    window_function_count: int = 0
    distinct_window_specs: int = 0
    aggregate_count: int = 0
    distinct_aggregates: list[str] = field(default_factory=list)
    has_having: bool = False
    has_distinct: bool = False
    has_order_by: bool = False
    # sources
    source_tables: int = 0
    distinct_sources: list[str] = field(default_factory=list)
    table_references: int = 0
    cte_references: int = 0
    # set operations
    set_operation_count: int = 0
    union_all_count: int = 0
    intersect_except_count: int = 0
    # expressions
    case_expression_count: int = 0
    case_max_branches: int = 0
    distinct_functions: list[str] = field(default_factory=list)
    nonportable_markers: list[str] = field(default_factory=list)
    # graph
    join_graph: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def parse_sql(sql: str) -> tuple[list[exp.Expression], str, str]:
    """Parse with the dialect cascade. Returns (statements, dialect, error)."""
    last_error = ""
    for dialect in DIALECT_CASCADE:
        try:
            trees = [t for t in sqlglot.parse(sql, read=dialect) if t is not None]
            if trees:
                return trees, dialect, ""
        except Exception as exc:  # sqlglot raises several error types
            last_error = f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}"
    return [], "", last_error or "no statements parsed"


def extract_features(path: str | Path) -> Features:
    path = Path(path)
    sql = path.read_text(encoding="utf-8")
    f = Features(name=path.stem, path=path.as_posix())

    f.chars = len(sql)
    f.loc = sum(1 for line in sql.splitlines() if line.strip())
    stripped = _COMMENT_RE.sub("", sql)
    f.loc_code = sum(1 for line in stripped.splitlines() if line.strip())

    low = stripped.lower()
    f.nonportable_markers = [
        name for name, pattern in _SYNTAX_MARKERS if re.search(pattern, low)
    ]

    trees, dialect, error = parse_sql(sql)
    f.parse_dialect, f.parse_error = dialect, error
    f.parse_ok = bool(trees)
    if not trees:
        return f

    f.statements = len(trees)
    if dialect != DIALECT_CASCADE[0]:
        # Needing a fallback dialect means the file carries engine-specific
        # syntax the primary dialect rejects outright.
        f.nonportable_markers.append("requires_dialect:" + dialect)

    sources: set[str] = set()
    aggregates: set[str] = set()
    functions: set[str] = set()
    window_specs: set[str] = set()

    for tree in trees:
        _collect_structure(tree, f)

        # `FROM v1` parses as a Table even when v1 is a CTE defined above it.
        # Counting those as source tables inflates the data footprint and would
        # corrupt both the rubric and the `multi_source` gold label.
        cte_names = {
            cte.alias_or_name.lower()
            for cte in tree.find_all(exp.CTE)
            if cte.alias_or_name
        }
        for table in tree.find_all(exp.Table):
            name = table.name.lower()
            if name in cte_names:
                f.cte_references += 1
                continue
            sources.add(name)
            f.table_references += 1

        for node in tree.find_all(exp.Window):
            f.window_function_count += 1
            window_specs.add(node.sql(dialect=dialect))

        for node in tree.find_all(exp.AggFunc):
            f.aggregate_count += 1
            aggregates.add(node.sql_name().lower())

        for node in tree.find_all(exp.Func):
            if not isinstance(node, _NOT_REALLY_FUNCTIONS):
                functions.add(node.sql_name().lower())

        for node in tree.find_all(exp.Case):
            f.case_expression_count += 1
            f.case_max_branches = max(
                f.case_max_branches, len(node.args.get("ifs") or [])
            )

        f.has_having |= tree.find(exp.Having) is not None
        f.has_order_by |= tree.find(exp.Order) is not None
        f.has_distinct |= (
            any(s.args.get("distinct") for s in tree.find_all(exp.Select))
            or tree.find(exp.Distinct) is not None
        )

        for node in tree.find_all(exp.Union, exp.Intersect, exp.Except):
            f.set_operation_count += 1
            if isinstance(node, exp.Union):
                # sqlglot marks UNION ALL as distinct=False.
                if node.args.get("distinct") is False:
                    f.union_all_count += 1
            else:
                f.intersect_except_count += 1

    f.distinct_sources = sorted(sources)
    f.source_tables = len(sources)
    f.distinct_aggregates = sorted(aggregates)
    f.distinct_functions = sorted(functions)
    f.distinct_window_specs = len(window_specs)

    # Built over all statements at once so a file holding two near-identical
    # statements reports one join footprint, not a doubled one.
    f.join_graph = build_join_graph(trees).as_dict()
    return f


def _collect_structure(tree: exp.Expression, f: Features) -> None:
    """Scope-level counts: CTEs, subqueries, nesting depth."""
    for scope in traverse_scope(tree):
        f.scope_count += 1

        depth, parent = 0, scope.parent
        while parent is not None:
            depth += 1
            parent = parent.parent
        f.max_nesting_depth = max(f.max_nesting_depth, depth)

        if scope.is_cte:
            f.cte_count += 1
            f.cte_max_depth = max(f.cte_max_depth, depth)
        elif scope.is_derived_table:
            f.derived_table_count += 1
            f.subquery_count += 1
        elif scope.is_subquery:
            f.subquery_count += 1
            f.scalar_subquery_count += 1
            if scope.is_correlated_subquery:
                f.correlated_subquery_count += 1
