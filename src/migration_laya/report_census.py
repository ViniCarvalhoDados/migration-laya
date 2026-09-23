"""Human-readable corpus profile, written to reports/census.md.

This report is the deliverable of step zero: it is what the team reads before
agreeing to the rubric thresholds, and it stands on its own whether or not Laya
proves usable.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .census import PERCENTILES

# Features worth showing in the percentile table; the CSV holds the rest.
_HEADLINE = (
    "loc_code", "statements", "source_tables", "subquery_count",
    "correlated_subquery_count", "cte_count", "window_function_count",
    "set_operation_count", "case_expression_count", "max_nesting_depth",
    "graph_nodes", "graph_edges", "graph_max_degree", "graph_max_scope_sources",
)


def _histogram(values: list[int], width: int = 40, bins: int = 8) -> list[str]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if lo == hi:
        return [f"  {lo:>6} | {'#' * min(width, len(values))} {len(values)}"]
    step = (hi - lo) / bins
    counts = Counter(min(bins - 1, int((v - lo) / step)) for v in values)
    peak = max(counts.values())
    lines = []
    for b in range(bins):
        start, end = lo + b * step, lo + (b + 1) * step
        n = counts.get(b, 0)
        bar = "#" * int(round(width * n / peak)) if peak else ""
        lines.append(f"  {start:>6.0f}-{end:<6.0f} | {bar:<{width}} {n}")
    return lines


def render(rows: list[dict], profile: dict, rubric: dict, corpus: str) -> str:
    n = len(rows)
    out: list[str] = []
    a = out.append

    a(f"# Censo do corpus — `{corpus}`\n")
    a(f"**n = {n} scripts.** Extração 100% determinística (sqlglot). "
      "Nenhum modelo envolvido: estes números são o gabarito do estudo.\n")

    # ---- parse health -------------------------------------------------
    failed = [r for r in rows if not r.get("parse_ok")]
    dialects = Counter(r.get("parse_dialect", "") for r in rows if r.get("parse_ok"))
    a("## 1. Saúde do parse\n")
    a(f"- Parseados: **{n - len(failed)}/{n}**")
    for dialect, count in dialects.most_common():
        a(f"  - `{dialect}`: {count}")
    if failed:
        a(f"- **Falhas ({len(failed)}):**")
        for r in failed:
            a(f"  - `{r['name']}` — {r.get('parse_error', '')[:120]}")
    else:
        a("- Nenhuma falha de parse.")

    total_unresolved = sum(int(r.get("unresolved_predicates", 0)) for r in rows)
    total_edges = sum(int(r.get("graph_edges", 0)) for r in rows)
    denom = total_unresolved + total_edges
    coverage = (100.0 * total_edges / denom) if denom else 100.0
    a(f"\n- Predicados de join resolvidos: **{coverage:.1f}%** "
      f"({total_edges} resolvidos, {total_unresolved} não resolvidos).")
    a("  Um predicado não resolvido é uma coluna que o extrator não conseguiu\n"
      "  atribuir a uma fonte; ele é contado, nunca chutado.\n")

    # ---- distributions -------------------------------------------------
    a("## 2. Distribuição por feature\n")
    header = ["feature", "min"] + [f"p{p}" for p in PERCENTILES] + ["max", "média", "zeros"]
    a("| " + " | ".join(header) + " |")
    a("|" + "---|" * len(header))
    for feat in _HEADLINE:
        s = profile.get(feat)
        if not s:
            continue
        cells = [f"`{feat}`", str(s["min"])]
        cells += [str(s[f"p{p}"]) for p in PERCENTILES]
        cells += [str(s["max"]), str(s["mean"]), f"{s['zeros']}/{n}"]
        a("| " + " | ".join(cells) + " |")

    a("\n> `zeros` importa: quando a maioria dos scripts tem 0 de uma feature,\n"
      "> o percentil baixo é 0 e o limiar da rubrica cai para 1 — ou seja,\n"
      "> **ter** a feature já é o sinal, e não *quanto* dela se tem.\n")

    # ---- histograms ----------------------------------------------------
    a("## 3. Histogramas\n")
    for feat in ("loc_code", "source_tables", "graph_edges"):
        if feat not in profile:
            continue
        a(f"**{feat}**\n```")
        out.extend(_histogram([int(r.get(feat, 0) or 0) for r in rows]))
        a("```\n")

    # ---- rubric --------------------------------------------------------
    a("## 4. Rubrica derivada\n")
    meta = rubric.get("meta", {})
    a(f"_{meta.get('band_note', '')}_\n")
    a("| feature | +1 a partir de | +2 a partir de | percentis usados |")
    a("|---|---|---|---|")
    for t in rubric.get("thresholds", []):
        upper = t.get("upper", "—")
        src = t.get("lower_from", "")
        if t.get("upper_from"):
            src += f" / {t['upper_from']}"
        a(f"| `{t['feature']}` | {t['lower']} | {upper} | {src} |")
    a("\n**Regras fixas (+1 cada):**\n")
    for name, doc in rubric.get("flat_rule_docs", {}).items():
        a(f"- `{name}` — {doc}")
    bands = rubric.get("bands", {})
    a(f"\n**Bandas:** low `{bands.get('low')}` · medium `{bands.get('medium')}` "
      f"· high `{bands.get('high')}`\n")

    # ---- band distribution ---------------------------------------------
    band_counts = Counter(r.get("rubric_band", "") for r in rows)
    a("## 5. Distribuição de complexidade\n")
    a("| banda | scripts | % |")
    a("|---|---|---|")
    for band in ("low", "medium", "high"):
        c = band_counts.get(band, 0)
        a(f"| {band} | {c} | {100.0 * c / n:.0f}% |")

    # ---- ranking -------------------------------------------------------
    ranked = sorted(rows, key=lambda r: -int(r.get("rubric_points", 0)))
    a("\n## 6. Os 12 scripts mais complexos\n")
    a("| # | script | pontos | banda | loc | fontes | subq | CTE | win | setop | arestas |")
    a("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(ranked[:12], 1):
        a(f"| {i} | `{r['name']}` | **{r['rubric_points']}** | {r['rubric_band']} | "
          f"{r['loc_code']} | {r['source_tables']} | {r['subquery_count']} | "
          f"{r['cte_count']} | {r['window_function_count']} | "
          f"{r['set_operation_count']} | {r['graph_edges']} |")

    a("\n## 7. Os 8 mais simples\n")
    a("| # | script | pontos | banda | loc | fontes | arestas | forma |")
    a("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(ranked[::-1][:8], 1):
        a(f"| {i} | `{r['name']}` | {r['rubric_points']} | {r['rubric_band']} | "
          f"{r['loc_code']} | {r['source_tables']} | {r['graph_edges']} | "
          f"{r['graph_shape']} |")

    # ---- portability ---------------------------------------------------
    markers = Counter()
    for r in rows:
        raw = r.get("nonportable_markers") or []
        for m in (raw if isinstance(raw, list) else str(raw).split("|")):
            if m:
                markers[m] += 1
    a("\n## 8. Marcadores de não-portabilidade\n")
    if markers:
        a("| marcador | scripts |")
        a("|---|---|")
        for marker, count in markers.most_common():
            a(f"| `{marker}` | {count} |")
    else:
        a("Nenhum detectado.")

    shapes = Counter(r.get("graph_shape", "") for r in rows)
    a("\n## 9. Forma do join mais largo\n")
    a("| forma | scripts |")
    a("|---|---|")
    for shape, count in shapes.most_common():
        a(f"| {shape} | {count} |")

    return "\n".join(out) + "\n"


def write(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
