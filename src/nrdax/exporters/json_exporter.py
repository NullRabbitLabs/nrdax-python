"""JSON export.

Preserves identifiers and provenance: a wrapper records the dataset ``version`` and
``doi`` (when minted) alongside the records, so an exported subset still carries the
context needed to cite it. Full records round-trip the canonical feed layout; a
``fields`` projection selects a subset of (possibly derived) fields.
"""

from __future__ import annotations

import json
from typing import Any

from ..models import Technique
from ._fields import field_value, resolve_fields


def to_records(
    techniques: list[Technique], *, fields: list[str] | tuple[str, ...] | None = None
) -> list[dict[str, Any]]:
    if not fields:
        return [t.to_dict() for t in techniques]
    cols = resolve_fields(fields)
    return [{c: field_value(t, c) for c in cols} for t in techniques]


def export_json(
    techniques: list[Technique],
    *,
    version: str,
    doi: str | None = None,
    fields: list[str] | tuple[str, ...] | None = None,
    pretty: bool = True,
) -> str:
    """Serialise techniques to a provenance-preserving JSON document."""
    doc: dict[str, Any] = {"registry_version": version}
    if doi:
        doc["doi"] = doi
    records = to_records(techniques, fields=fields)
    doc["count"] = len(records)
    doc["techniques"] = records
    if pretty:
        return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    return json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n"
