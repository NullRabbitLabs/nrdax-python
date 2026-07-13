"""Rendering helpers for the CLI (human tables/detail and machine JSON shapes).

Kept separate from command handlers so output shapes are testable in isolation.
Machine-readable JSON uses stable field names (documented in ``docs/cli.md``).
"""

from __future__ import annotations

import json
import textwrap
from typing import Any

from ..changes import ChangeSet
from ..exporters._fields import field_value, resolve_fields, scalar
from ..models import Technique
from ..queries.search import SearchResult
from ..relationships import RelatedResult


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def truncate(text: str, width: int) -> str:
    text = text.replace("\n", " ").strip()
    return text if len(text) <= width else text[: width - 3] + "..."


def render_table(headers: list[str], rows: list[list[str]], *, max_col: int = 60) -> str:
    """A minimal left-aligned column table (no external dependency)."""
    if not rows:
        return "(no results)"
    cols = list(zip(*[headers, *rows], strict=False))
    widths = [min(max(len(str(c)) for c in col), max_col) for col in cols]

    def fmt_row(cells: list[str]) -> str:
        return "  ".join(truncate(str(c), w).ljust(w) for c, w in zip(cells, widths, strict=False))

    sep = "  ".join("-" * w for w in widths)
    return "\n".join([fmt_row(headers), sep, *(fmt_row(r) for r in rows)])


# -- techniques -----------------------------------------------------------------


def technique_rows(techniques: list[Technique], fields: tuple[str, ...]) -> list[list[str]]:
    return [[scalar(field_value(t, f)) for f in fields] for t in techniques]


def technique_table(techniques: list[Technique], fields: tuple[str, ...] | None = None) -> str:
    cols = resolve_fields(list(fields) if fields else None)
    return render_table(list(cols), technique_rows(techniques, cols))


def technique_detail(t: Technique) -> str:
    lines = [
        f"{t.id}  {t.display}",
        "=" * (len(t.id) + 2 + len(t.display)),
        f"slug (name)        {t.name}",
        f"family             {t.family}",
        f"status             {t.status}",
        f"reproduction       {t.reproduction_status}",
        f"first seen         {t.first_seen}",
        f"chains             {', '.join(t.chains) or '(none reproduced)'}",
        f"url                {t.url}",
    ]
    if t.provenance_note:
        lines.append(f"provenance         {t.provenance_note}")
    lines.append("")
    lines.append("mechanism")
    lines.append(textwrap.fill(t.mechanism, width=88, initial_indent="  ", subsequent_indent="  "))

    if t.instances:
        lines.append("")
        lines.append(f"instances ({len(t.instances)})")
        for inst in t.instances:
            lines.append(
                f"  - {inst.chain}: {inst.primitive_id}  "
                f"[{inst.fidelity} / {inst.discovery_origin}]"
            )
            for ref in inst.external_references:
                lines.append(f"      ref {ref.kind}: {truncate(ref.id, 80)}")
    else:
        lines.append("")
        lines.append("instances          (known-but-not-reproduced)")

    if t.external_references:
        lines.append("")
        lines.append("references")
        for ref in t.external_references:
            url = f"  {ref.url}" if ref.url else ""
            lines.append(f"  - {ref.kind}: {truncate(ref.id, 80)}{url}")
    return "\n".join(lines)


def technique_json(t: Technique) -> dict[str, Any]:
    d = t.to_dict()
    d["reproduction_status"] = t.reproduction_status
    d["chains"] = t.chains
    d["url"] = t.url
    return d


# -- search ---------------------------------------------------------------------


def search_table(results: list[SearchResult], *, explain: bool = False) -> str:
    headers = ["score", "id", "display", "family", "repro"]
    if explain:
        headers.append("matched")
    rows = []
    for r in results:
        t = r.technique
        row = [f"{r.score:g}", t.id, truncate(t.display, 50), t.family, t.reproduction_status]
        if explain:
            row.append(",".join(r.matched_fields))
        rows.append(row)
    return render_table(headers, rows)


def search_json(query: str, results: list[SearchResult]) -> dict[str, Any]:
    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "score": r.score,
                "matched_fields": list(r.matched_fields),
                "technique": technique_json(r.technique),
            }
            for r in results
        ],
    }


# -- related --------------------------------------------------------------------


def related_detail(rel: RelatedResult) -> str:
    lines = [f"related to {rel.technique_id}  (all relationships are DERIVED, not asserted)"]
    lines.append(f"\nfamily: {rel.family}")
    lines.append(
        "  siblings: " + (", ".join(rel.family_siblings) if rel.family_siblings else "(none)")
    )
    if rel.chains:
        lines.append("\nshared chains:")
        for cn in rel.chains:
            lines.append(f"  {cn.chain}: {', '.join(cn.technique_ids)}")
    if rel.shared_references:
        lines.append("\nshared references (strongest links):")
        for sr in rel.shared_references:
            lines.append(f"  {sr.reference} ({sr.kind}): {', '.join(sr.technique_ids)}")
    if rel.instances:
        lines.append(f"\ninstances / reproductions ({len(rel.instances)}):")
        for inst in rel.instances:
            lines.append(f"  {inst.chain}: {inst.primitive_id} [{inst.fidelity}]")
    if rel.advisories:
        lines.append("\nadvisories:")
        for ref in rel.advisories:
            lines.append(f"  {ref.kind}: {truncate(ref.id, 80)}")
    if rel.briefs:
        lines.append("\nresearch briefs:")
        for ref in rel.briefs:
            lines.append(f"  {truncate(ref.id, 80)}")
    if rel.is_empty():
        lines.append("\n(no derived relationships found)")
    return "\n".join(lines)


def related_json(rel: RelatedResult) -> dict[str, Any]:
    return {
        "technique_id": rel.technique_id,
        "note": "relationships are derived from canonical fields, not asserted edges",
        "family": rel.family,
        "family_siblings": rel.family_siblings,
        "chains": [{"chain": c.chain, "technique_ids": list(c.technique_ids)} for c in rel.chains],
        "shared_references": [
            {"reference": s.reference, "kind": s.kind, "technique_ids": list(s.technique_ids)}
            for s in rel.shared_references
        ],
        "instances": [i.to_dict() for i in rel.instances],
        "advisories": [r.to_dict() for r in rel.advisories],
        "briefs": [r.to_dict() for r in rel.briefs],
    }


# -- changes --------------------------------------------------------------------


def changes_detail(cs: ChangeSet) -> str:
    header = f"changes {cs.from_version} -> {cs.to_version}: {len(cs)} change(s)"
    if not cs.changes:
        return header + "\n(no changes)"
    counts = ", ".join(f"{k}={v}" for k, v in cs.counts_by_kind().items())
    rows = [[c.technique_id, c.kind, truncate(c.detail, 70)] for c in cs.changes]
    return header + f"\n{counts}\n\n" + render_table(["technique", "change", "detail"], rows)


def changes_json(cs: ChangeSet) -> dict[str, Any]:
    return {
        "from_version": cs.from_version,
        "to_version": cs.to_version,
        "count": len(cs),
        "counts_by_kind": cs.counts_by_kind(),
        "changes": [
            {
                "kind": c.kind,
                "technique_id": c.technique_id,
                "detail": c.detail,
                "old": c.old,
                "new": c.new,
            }
            for c in cs.changes
        ],
    }
