"""STIX 2.1 bundle source (parse NRDAX STIX back into techniques).

**STIX is an export format for NRDAX, not its internal model**, so parsing is
deliberately *lossy* and documented as such:

* Recovered: the NRDAX id (anchored in ``external_references`` under
  ``source_name: "nrdax"``), the name, mechanism (``description``), ``first_seen``
  (from ``created``), and the custom properties ``x_nrdax_family`` /
  ``x_nrdax_status`` / ``x_nrdax_chains``, plus all non-anchor references.
* **Not** recovered: per-instance detail (``primitive_id``, ``bundle_ref``,
  ``fidelity``, ``discovery_origin``) — STIX flattens instances into a chain list
  and a merged reference list. Imported techniques therefore have no ``instances``;
  the chain list is preserved verbatim under ``extra['x_nrdax_chains']``.

This is enough to round-trip *identity* and the coarse fields, matching what the
canonical backend's STIX round-trip guarantees.
"""

from __future__ import annotations

import json
from typing import Any

from ..errors import DataFormatError, SourceError
from . import RawDataset, SourceMeta


def _references(sdo: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    """Return ``(nrdax_id, other_references)`` from an SDO's external references."""
    nrdax_id: str | None = None
    others: list[dict[str, Any]] = []
    for ref in sdo.get("external_references", []) or []:
        if not isinstance(ref, dict):
            continue
        source = ref.get("source_name")
        ext_id = ref.get("external_id")
        if source == "nrdax":
            if isinstance(ext_id, str):
                nrdax_id = ext_id
            continue
        entry: dict[str, Any] = {"kind": source, "id": ext_id}
        if isinstance(ref.get("url"), str):
            entry["url"] = ref["url"]
        others.append(entry)
    return nrdax_id, others


def parse_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn a STIX bundle into raw technique dicts (identity + coarse fields)."""
    if bundle.get("type") != "bundle":
        raise DataFormatError("not a STIX bundle (type != 'bundle')")
    objects = bundle.get("objects")
    if not isinstance(objects, list):
        raise DataFormatError("STIX bundle has no 'objects' array")

    techniques: list[dict[str, Any]] = []
    for sdo in objects:
        if not isinstance(sdo, dict) or sdo.get("type") != "attack-pattern":
            continue
        nrdax_id, refs = _references(sdo)
        if not nrdax_id:
            continue  # not an NRDAX-anchored attack-pattern
        created = sdo.get("created", "")
        first_seen = created[:10] if isinstance(created, str) else ""
        tech: dict[str, Any] = {
            "id": nrdax_id,
            "name": sdo.get("name", ""),
            "mechanism": sdo.get("description", ""),
            "family": sdo.get("x_nrdax_family", ""),
            "status": sdo.get("x_nrdax_status", "active"),
            "first_seen": first_seen,
            "instances": [],
            "external_references": refs,
        }
        chains = sdo.get("x_nrdax_chains")
        if isinstance(chains, list):
            tech["x_nrdax_chains"] = chains  # preserved into Technique.extra
        techniques.append(tech)
    return techniques


class StixSource:
    """Load NRDAX identity + coarse fields from a STIX 2.1 bundle (path or object)."""

    def __init__(self, bundle: dict[str, Any] | None = None, *, path: str | None = None):
        if (bundle is None) == (path is None):
            raise ValueError("provide exactly one of bundle= or path=")
        self._bundle = bundle
        self._path = path

    def load(self) -> RawDataset:
        if self._path is not None:
            try:
                with open(self._path, encoding="utf-8") as fh:
                    bundle = json.load(fh)
            except FileNotFoundError as exc:
                raise SourceError(f"STIX file not found: {self._path}") from exc
            except json.JSONDecodeError as exc:
                raise DataFormatError(f"{self._path}: invalid JSON: {exc}") from exc
            location = self._path
        else:
            bundle = self._bundle
            location = "<stix bundle>"
        if not isinstance(bundle, dict):
            raise DataFormatError("STIX bundle must be a JSON object")
        return RawDataset(
            version="stix-import",
            doi=None,
            techniques=parse_bundle(bundle),
            meta=SourceMeta(kind="stix", location=location),
        )
