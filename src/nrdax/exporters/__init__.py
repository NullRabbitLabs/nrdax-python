"""Format exporters: JSON, CSV, and STIX 2.1.

All three preserve NRDAX identifiers and provenance. STIX is treated as an *export*
format (not the internal model) and is byte-compatible with the canonical feed.
"""

from __future__ import annotations

from ..errors import InvalidArgumentError
from ..models import Technique
from ._fields import AVAILABLE_FIELDS, DEFAULT_FIELDS
from .csv_exporter import export_csv
from .json_exporter import export_json, to_records
from .stix_exporter import dumps as stix_dumps
from .stix_exporter import stix_bundle, technique_ids, validate_bundle

EXPORT_FORMATS = ("json", "csv", "stix")

__all__ = [
    "AVAILABLE_FIELDS",
    "DEFAULT_FIELDS",
    "EXPORT_FORMATS",
    "export",
    "export_csv",
    "export_json",
    "stix_bundle",
    "stix_dumps",
    "technique_ids",
    "to_records",
    "validate_bundle",
]


def export(
    techniques: list[Technique],
    fmt: str,
    *,
    version: str,
    doi: str | None = None,
    fields: list[str] | tuple[str, ...] | None = None,
    csv_rows: str = "techniques",
) -> str:
    """Export ``techniques`` in ``fmt`` (``json`` | ``csv`` | ``stix``) as text."""
    if fmt == "json":
        return export_json(techniques, version=version, doi=doi, fields=fields)
    if fmt == "csv":
        return export_csv(techniques, fields=fields, rows=csv_rows)
    if fmt == "stix":
        return stix_dumps(stix_bundle(techniques, version))
    raise InvalidArgumentError(
        f"unsupported export format: {fmt!r} (choose from {', '.join(EXPORT_FORMATS)})"
    )
