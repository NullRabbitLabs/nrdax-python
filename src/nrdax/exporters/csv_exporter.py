"""CSV export.

Two shapes:

* ``rows="techniques"`` (default) — one row per technique. Nested collections are
  flattened deterministically: list-valued fields (``chains``, ``*_ids``) are joined
  with ``;`` and ``instance_count`` is included, so no field is *silently* dropped —
  the flattening is documented, not lossy-by-omission.
* ``rows="instances"`` — one row per instance, annotated with its technique id
  (the natural tabular shape for instance-level analysis).
"""

from __future__ import annotations

import csv
import io

from ..models import Technique
from ._fields import field_value, resolve_fields, scalar

_INSTANCE_COLUMNS = (
    "technique_id",
    "technique_name",
    "chain",
    "primitive_id",
    "bundle_ref",
    "fidelity",
    "discovery_origin",
    "reference_ids",
)


def export_csv(
    techniques: list[Technique],
    *,
    fields: list[str] | tuple[str, ...] | None = None,
    rows: str = "techniques",
) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")

    if rows == "instances":
        writer.writerow(_INSTANCE_COLUMNS)
        for t in techniques:
            for inst in t.instances:
                writer.writerow(
                    [
                        t.id,
                        t.display,
                        inst.chain,
                        inst.primitive_id,
                        inst.bundle_ref,
                        inst.fidelity,
                        inst.discovery_origin,
                        ";".join(sorted(r.id for r in inst.external_references)),
                    ]
                )
        return buf.getvalue()

    if rows != "techniques":
        from ..errors import InvalidArgumentError

        raise InvalidArgumentError(f"unknown csv rows mode: {rows!r} (use techniques|instances)")

    cols = resolve_fields(fields)
    writer.writerow(cols)
    for t in techniques:
        writer.writerow([scalar(field_value(t, c)) for c in cols])
    return buf.getvalue()
