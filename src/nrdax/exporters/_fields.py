"""Field accessors shared by the JSON/CSV exporters and the CLI table renderer.

Exposes the canonical fields plus a few *derived* projections (``reproduction_status``,
``chains``, ``instance_count`` …) under stable names. These names are the export
compatibility surface — see ``docs/cli.md``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..errors import InvalidArgumentError
from ..models import Technique

# name -> accessor. List-valued accessors return lists (CSV joins them with ';').
_ACCESSORS: dict[str, Callable[[Technique], Any]] = {
    "id": lambda t: t.id,
    "name": lambda t: t.name,
    "display_name": lambda t: t.display_name,
    "display": lambda t: t.display,
    "mechanism": lambda t: t.mechanism,
    "family": lambda t: t.family,
    "status": lambda t: t.status,
    "first_seen": lambda t: t.first_seen,
    "provenance_note": lambda t: t.provenance_note,
    "reproduction_status": lambda t: t.reproduction_status,
    "is_reproduced": lambda t: t.is_reproduced,
    "instance_count": lambda t: len(t.instances),
    "chains": lambda t: t.chains,
    "strongest_fidelity": lambda t: t.strongest_fidelity,
    "url": lambda t: t.url,
    "reference_ids": lambda t: sorted(t.reference_ids),
    "cve_ids": lambda t: sorted(r.id for r in t.references_of_kind("cve")),
    "ghsa_ids": lambda t: sorted(r.id for r in t.references_of_kind("ghsa")),
    "advisory_ids": lambda t: sorted(
        r.id for r in t.references_of_kind("nr-advisory", "vendor-advisory")
    ),
    "brief_ids": lambda t: sorted(r.id for r in t.references_of_kind("nr-brief")),
}

#: Field names available for ``--fields`` and CSV columns.
AVAILABLE_FIELDS: tuple[str, ...] = tuple(_ACCESSORS)

#: Sensible default column set for tabular output.
DEFAULT_FIELDS: tuple[str, ...] = (
    "id",
    "display",
    "family",
    "status",
    "reproduction_status",
    "instance_count",
    "chains",
    "first_seen",
)


def resolve_fields(fields: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    """Validate a requested field list, returning the defaults when ``None``."""
    if not fields:
        return DEFAULT_FIELDS
    unknown = [f for f in fields if f not in _ACCESSORS]
    if unknown:
        raise InvalidArgumentError(
            f"unknown field(s): {', '.join(unknown)}. Available: {', '.join(AVAILABLE_FIELDS)}"
        )
    return tuple(fields)


def field_value(tech: Technique, name: str) -> Any:
    try:
        return _ACCESSORS[name](tech)
    except KeyError:
        raise InvalidArgumentError(f"unknown field: {name}") from None


def scalar(value: Any, *, sep: str = ";") -> str:
    """Render a field value as a CSV/table scalar (lists joined, ``None`` → '')."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return sep.join(str(v) for v in value)
    return str(value)
