"""STIX 2.1 export — byte-for-byte compatible with the canonical NRDAX emitter.

Reproduces the backend's deterministic scheme (``stix/mod.rs``): ids are UUIDv5
under a fixed namespace, timestamps come from ``first_seen`` (no wall-clock), the
NRDAX id is anchored in ``external_references`` (``source_name: "nrdax"``), and the
NRDAX-specific fields ride as custom properties ``x_nrdax_family`` /
``x_nrdax_status`` / ``x_nrdax_chains``. Keys are alphabetically sorted and the
document is 2-space-indented with a trailing newline, matching the feed's
``stix.json`` exactly — so a bundle exported here is identical to the one served.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from ..models import Technique

#: Fixed namespace for deterministic STIX identifiers (matches the backend).
NAMESPACE = uuid.UUID("6e727669-615f-5f5f-8000-000000000001")

#: Advertised STIX content type.
CONTENT_TYPE = "application/stix+json;version=2.1"


def _reference(kind: str, ref_id: str, url: str | None) -> dict[str, Any]:
    obj: dict[str, Any] = {"source_name": kind, "external_id": ref_id}
    if url is not None:
        obj["url"] = url
    return obj


def attack_pattern(technique: Technique) -> dict[str, Any]:
    """One technique as a STIX ``attack-pattern`` SDO."""
    ap_uuid = uuid.uuid5(NAMESPACE, technique.id)
    timestamp = f"{technique.first_seen}T00:00:00.000Z"

    refs: list[dict[str, Any]] = [
        {
            "source_name": "nrdax",
            "external_id": technique.id,
            "url": technique.url,
        }
    ]
    for ref in technique.external_references:
        refs.append(_reference(ref.kind, ref.id, ref.url))
    for inst in technique.instances:
        for ref in inst.external_references:
            refs.append(_reference(ref.kind, ref.id, ref.url))

    chains = sorted({inst.chain for inst in technique.instances})

    return {
        "type": "attack-pattern",
        "spec_version": "2.1",
        "id": f"attack-pattern--{ap_uuid}",
        "created": timestamp,
        "modified": timestamp,
        "name": technique.display,
        "description": technique.mechanism,
        "external_references": refs,
        "x_nrdax_family": technique.family,
        "x_nrdax_status": technique.status,
        "x_nrdax_chains": chains,
    }


def stix_bundle(techniques: list[Technique], version: str) -> dict[str, Any]:
    """A STIX bundle of the given techniques, with a deterministic bundle id."""
    objects = [attack_pattern(t) for t in techniques]
    seed = version + "".join(f"|{t.id}" for t in techniques)
    bundle_id = uuid.uuid5(NAMESPACE, seed)
    return {
        "type": "bundle",
        "id": f"bundle--{bundle_id}",
        "objects": objects,
    }


def dumps(bundle: dict[str, Any]) -> str:
    """Serialise a bundle exactly as the feed's ``stix.json`` (sorted keys,
    2-space indent, trailing newline)."""
    return json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def technique_ids(bundle: dict[str, Any]) -> list[str]:
    """Extract the NRDAX ids anchored in a bundle — proves identity round-trips."""
    ids: list[str] = []
    for obj in bundle.get("objects", []) or []:
        if not isinstance(obj, dict):
            continue
        for ref in obj.get("external_references", []) or []:
            if isinstance(ref, dict) and ref.get("source_name") == "nrdax":
                ext = ref.get("external_id")
                if isinstance(ext, str):
                    ids.append(ext)
    return ids


def validate_bundle(bundle: dict[str, Any]) -> list[str]:
    """Structural STIX 2.1 validation (mirrors the backend's checks).

    Returns a list of problems (empty means valid). If the optional ``stix2``
    package is installed, callers may additionally run its stricter parser; this
    zero-dependency check is always available.
    """
    errors: list[str] = []
    if bundle.get("type") != "bundle":
        errors.append('bundle.type must be "bundle"')
    if not _is_stix_id(bundle.get("id"), "bundle"):
        errors.append("bundle.id must be a valid STIX identifier")
    objects = bundle.get("objects")
    if not isinstance(objects, list):
        return [*errors, "bundle.objects must be an array"]

    for i, obj in enumerate(objects):
        if not isinstance(obj, dict):
            errors.append(f"objects[{i}] must be an object")
            continue
        otype = obj.get("type")
        if not otype:
            errors.append(f"objects[{i}].type is required")
        if obj.get("spec_version") != "2.1":
            errors.append(f'objects[{i}].spec_version must be "2.1"')
        if not _is_stix_id(obj.get("id"), otype if isinstance(otype, str) else ""):
            errors.append(f"objects[{i}].id must be a valid STIX identifier of its type")
        if otype == "attack-pattern":
            if not obj.get("name"):
                errors.append(f"objects[{i}].name is required")
            for fld in ("created", "modified"):
                if not _is_stix_timestamp(obj.get(fld)):
                    errors.append(f"objects[{i}].{fld} must be a STIX timestamp")
            for j, ref in enumerate(obj.get("external_references", []) or []):
                if not isinstance(ref, dict) or not ref.get("source_name"):
                    errors.append(f"objects[{i}].external_references[{j}].source_name is required")
    return errors


def _is_stix_id(value: Any, expected_type: str) -> bool:
    if not isinstance(value, str) or "--" not in value:
        return False
    kind, _, suffix = value.partition("--")
    if kind != expected_type:
        return False
    try:
        uuid.UUID(suffix)
    except ValueError:
        return False
    return True


def _is_stix_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        return False
    date, _, time = value.partition("T")
    parts = date.split("-")
    if len(parts) != 3 or [len(p) for p in parts] != [4, 2, 2]:
        return False
    hms = time[:-1].split(".")[0]
    segs = hms.split(":")
    return len(segs) == 3 and all(s.isdigit() for s in segs)
