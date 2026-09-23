"""Join-graph extraction from parsed SQL statements.

Two different things are worth measuring and they must not be conflated:

* **Data footprint** — which base tables the script touches and how they relate.
  Built by unioning every scope's base-table edges into one graph.
* **Structural join complexity** — how tangled the worst single join is. Taken
  as the maximum over scopes, counting *every* source (base tables, CTEs and
  derived tables), because a five-way join against three CTEs is structurally a
  five-way join.

Merging every scope into one graph and then reading `connected_components` as
"cartesian product risk" is wrong: separate scopes are *supposed* to be
disconnected. Cross-join risk is therefore evaluated per scope, never globally.

TPC-DS (like most warehouse schemas) leaves join columns unqualified and relies
on a table-abbreviation convention (``ss_item_sk`` -> ``store_sales``). We infer
that convention generically from the source names in scope rather than
hardcoding a TPC-DS prefix map, resolve columns of CTEs and derived tables
through their output column names, and count what we could not resolve instead
of guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope, find_all_in_scope

# Words that carry no identity in a table name and are dropped when deriving the
# secondary abbreviation (``time_dim`` -> ``t``, not ``td``).
_GENERIC_SUFFIXES = {"dim", "dimension", "fact", "tbl", "table", "t", "f", "d"}


def _prefix_specificity(prefix: str, source_name: str, alias: str | None) -> int:
    """How strongly a column prefix points at one source. 0 means no match.

    Warehouse SQL abbreviates table names in column prefixes several different
    ways at once — initials (``store_sales`` -> ``ss_``), initials minus the
    dimension suffix (``time_dim`` -> ``t_``), and plain truncation
    (``inventory`` -> ``inv_``). Scoring them on one scale, rather than trying
    a fixed ladder of rules, lets the most specific match win whichever form it
    takes.
    """
    name = source_name.lower()
    words = [w for w in name.split("_") if w]
    if not prefix or not words:
        return 0

    if prefix == name:
        return 100
    if alias and prefix == alias.lower():
        return 95
    if prefix == "".join(w[0] for w in words):
        return 90                                   # store_sales -> ss
    core = [w for w in words if w not in _GENERIC_SUFFIXES] or words
    if prefix == "".join(w[0] for w in core):
        return 80                                   # time_dim -> t
    if len(prefix) >= 2 and name.startswith(prefix):
        return 50 + len(prefix)                     # inventory -> inv
    if prefix == words[0][0]:
        return 10                                   # weakest: first letter only
    return 0


@dataclass
class JoinGraph:
    # data footprint (base tables only)
    nodes: int = 0
    edges: int = 0
    density: float = 0.0
    connected_components: int = 0
    max_degree: int = 0
    node_names: list[str] = field(default_factory=list)
    # structural complexity (widest single scope, all sources)
    max_scope_sources: int = 0
    max_scope_edges: int = 0
    max_scope_degree: int = 0
    widest_scope_shape: str = "single"
    # join style and risk
    implicit_joins: int = 0
    explicit_joins: int = 0
    cross_join_risk: int = 0
    unresolved_predicates: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


class _ScopeResolver:
    """Maps a column reference to one of the sources visible in a scope.

    Sources are base tables, CTE references and derived tables alike. A column
    of a derived source is matched against that source's output column list,
    which is how ``date_sk = d_date_sk`` links a derived table to ``date_dim``
    instead of registering as unresolved.
    """

    def __init__(self, scope):
        self.by_alias: dict[str, str] = {}
        self.aliases: dict[str, str | None] = {}
        self.output_columns: dict[str, set[str]] = {}
        self.base_tables: set[str] = set()
        self.node_names: list[str] = []

        # `selected_sources`, not `sources`: the latter carries every CTE defined
        # anywhere in the statement, so scopes that never reference a CTE would
        # still gain it as an orphan node and be flagged as a cartesian risk.
        for alias, (_, source) in scope.selected_sources.items():
            if isinstance(source, exp.Table):
                node = source.name.lower()
                self.base_tables.add(node)
            else:
                # A CTE or derived table: its scope-local name is its identity.
                node = (alias or "").lower()
                if not node:
                    continue
                try:
                    self.output_columns[node] = {
                        c.lower() for c in source.expression.named_selects if c
                    }
                except Exception:
                    self.output_columns[node] = set()

            self.node_names.append(node)
            self.by_alias[node] = node
            if alias:
                self.by_alias[alias.lower()] = node
            # An alias is itself a prefix convention: `ss.item_sk` and, in
            # sloppier legacy SQL, `ss_item_sk`.
            self.aliases[node] = alias.lower() if alias else None

    def resolve(self, col: exp.Column) -> str | None:
        qualifier = col.table
        if qualifier:
            return self.by_alias.get(qualifier.lower())

        name = col.name.lower()

        # A derived source declares exactly which columns it exposes, so an
        # exact name match beats any prefix guess.
        owners = [n for n, cols in self.output_columns.items() if name in cols]
        if len(owners) == 1:
            return owners[0]

        if "_" not in name:
            return None

        # Every underscore is a possible prefix boundary, so `web_site_sk` is
        # tried as both `web_` and `web_site_` — the latter names its table
        # outright and beats the abbreviation both candidates share.
        best, hits, remainder = 0, [], ""
        cut = -1
        while (cut := name.find("_", cut + 1)) != -1:
            prefix, rest = name[:cut], name[cut + 1:]
            for node in self.node_names:
                score = _prefix_specificity(prefix, node, self.aliases.get(node))
                if score > best:
                    best, hits, remainder = score, [node], rest
                elif score and score == best and node not in hits:
                    hits.append(node)

        if not best:
            return None
        if len(hits) == 1:
            return hits[0]

        # Two sources abbreviate the same way (`inventory` and `item` both give
        # `i_`). The rest of the column name usually spells out the owner:
        # `i_item_sk` belongs to `item`, not `inventory`.
        spelled = [n for n in hits if remainder.startswith(n)]
        return spelled[0] if len(spelled) == 1 else None


def _equality_predicates(scope_root: exp.Expression):
    """EQ nodes from this scope's own WHERE and JOIN..ON.

    Uses ``find_all_in_scope`` so predicates belonging to a nested subquery stay
    with that subquery. A plain ``find_all`` walks straight through scope
    boundaries and attributes inner-scope joins to the outer scope, which
    silently invents edges and inflates the unresolved count.
    """
    roots: list[exp.Expression] = []
    if isinstance(scope_root, exp.Select):
        where = scope_root.args.get("where")
        if where is not None:
            roots.append(where)
        for join in scope_root.args.get("joins") or []:
            on = join.args.get("on")
            if on is not None:
                roots.append(on)

    for root in roots:
        yield from find_all_in_scope(root, exp.EQ)


def _references_columns(node: exp.Expression) -> bool:
    """Does this expression read at least one column (possibly through a call)?"""
    return isinstance(node, exp.Column) or node.find(exp.Column) is not None


def build_join_graph(statements: exp.Expression | list[exp.Expression]) -> JoinGraph:
    """Union the per-scope join graphs of one or more statements.

    Statements are merged rather than summed, so a file holding two
    near-identical statements (TPC-DS q23) reports one join footprint instead of
    a doubled one.
    """
    if isinstance(statements, exp.Expression):
        statements = [statements]

    footprint: dict[str, set[str]] = {}
    unresolved = implicit = explicit = cross_join_risk = 0
    max_scope_sources = max_scope_edges = max_scope_degree = 0
    widest_shape, widest_width = "single", -1

    for statement in statements:
        for scope in traverse_scope(statement):
            if not scope.selected_sources:
                continue
            resolver = _ScopeResolver(scope)
            if not resolver.node_names:
                continue

            local: dict[str, set[str]] = {n: set() for n in resolver.node_names}
            for base in resolver.base_tables:
                footprint.setdefault(base, set())

            local_unresolved = 0
            for eq in _equality_predicates(scope.expression):
                left, right = eq.left, eq.right
                if not (isinstance(left, exp.Column) and isinstance(right, exp.Column)):
                    # A predicate joining two sources through function calls —
                    # `Substr(a.zip, 1, 2) = Substr(b.zip, 1, 2)` — is a join we
                    # cannot attribute, not the absence of one. Counting it as
                    # unresolved stops the scope being called a cartesian product.
                    if _references_columns(left) and _references_columns(right):
                        unresolved += 1
                        local_unresolved += 1
                    continue  # otherwise a literal filter
                a, b = resolver.resolve(left), resolver.resolve(right)
                if a is None or b is None:
                    unresolved += 1
                    local_unresolved += 1
                    continue
                if a == b:
                    continue
                local.setdefault(a, set()).add(b)
                local.setdefault(b, set()).add(a)
                # Only table-to-table links describe the data footprint; an edge
                # into a CTE is structure, not a relationship between datasets.
                if a in resolver.base_tables and b in resolver.base_tables:
                    footprint.setdefault(a, set()).add(b)
                    footprint.setdefault(b, set()).add(a)

            width = len(local)
            local_edges = sum(len(v) for v in local.values()) // 2
            local_degrees = {k: len(v) for k, v in local.items()}
            max_scope_sources = max(max_scope_sources, width)
            max_scope_edges = max(max_scope_edges, local_edges)
            max_scope_degree = max(max_scope_degree, max(local_degrees.values(), default=0))
            if width > widest_width:
                widest_width = width
                widest_shape = _classify_shape(
                    width, local_edges, local_degrees, _count_components(local)
                )
            # Only assert a cartesian product when every predicate in the scope
            # was understood. If anything went unresolved, an orphan source may
            # simply be joined by a predicate the resolver could not attribute —
            # and claiming a cross join there is a guess, which this extractor
            # does not make anywhere else.
            if width > 1 and local_unresolved == 0:
                cross_join_risk += sum(1 for d in local_degrees.values() if d == 0)

        for join in statement.find_all(exp.Join):
            if join.args.get("on") is None and not join.args.get("using"):
                implicit += 1
            else:
                explicit += 1

    nodes = sorted(footprint)
    n = len(nodes)
    edges = sum(len(v) for v in footprint.values()) // 2
    max_possible = n * (n - 1) / 2

    return JoinGraph(
        nodes=n,
        edges=edges,
        density=round(edges / max_possible, 4) if max_possible else 0.0,
        connected_components=_count_components(footprint),
        max_degree=max((len(v) for v in footprint.values()), default=0),
        node_names=nodes,
        max_scope_sources=max_scope_sources,
        max_scope_edges=max_scope_edges,
        max_scope_degree=max_scope_degree,
        widest_scope_shape=widest_shape,
        implicit_joins=implicit,
        explicit_joins=explicit,
        cross_join_risk=cross_join_risk,
        unresolved_predicates=unresolved,
    )


def _count_components(adjacency: dict[str, set[str]]) -> int:
    seen, components = set(), 0
    for start in adjacency:
        if start in seen:
            continue
        components += 1
        stack = [start]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adjacency.get(node, set()) - seen)
    return components


def _classify_shape(n: int, edges: int, degrees: dict[str, int], components: int) -> str:
    if n <= 1:
        return "single"
    if components > 1:
        return "disconnected"
    if edges == n - 1:
        # One hub touching everything is a star; a chain of joins is a snowflake.
        return "star" if max(degrees.values(), default=0) == n - 1 else "snowflake"
    return "mesh"
