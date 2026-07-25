"""Typed domain models for NRDAX records.

The models mirror the canonical schema exactly (see ``IMPLEMENTATION_PLAN.md`` and
``docs/data-model.md``) and add only *derived* conveniences (``display``,
``chains``, ``reproduction_status``) that are computed, never stored. They:

* validate incoming data into an :class:`~nrdax.errors.IssueCollector` (lenient by
  default; ``strict`` raises on the first error);
* preserve unknown canonical extension fields in ``extra`` (round-tripped by
  :meth:`to_dict`) so a future field is never dropped;
* distinguish *missing* (``None``) from *empty* (``[]``).

``to_dict`` emits keys in canonical field order so JSON export matches the feed's
per-technique layout byte-for-byte.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, ClassVar

from .errors import IssueCollector
from .vocab import (
    BOUND_FAILURES,
    DISCOVERY_ORIGINS,
    FAMILIES,
    FIDELITY_CLASSES,
    MECHANISM_FAMILIES,
    NRDAX_SITE,
    REFERENCE_KINDS,
    STATUSES,
    SURFACES,
    TECHNIQUE_ID_PATTERN,
    fidelity_strength,
)

_ID_RE = re.compile(TECHNIQUE_ID_PATTERN)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _drop_known(data: dict[str, Any], known: set[str]) -> dict[str, Any]:
    """Return the subset of ``data`` whose keys are *not* in ``known`` (the
    unknown/extension fields to preserve verbatim in ``extra``)."""
    return {k: v for k, v in data.items() if k not in known}


def _require_str(
    data: dict[str, Any], key: str, issues: IssueCollector | None, locator: str
) -> str:
    value = data.get(key)
    if isinstance(value, str) and value != "":
        return value
    if issues is not None:
        kind = "missing" if key not in data else "not a non-empty string"
        issues.add(f"{locator}.{key}", f"required field {kind}")
    return value if isinstance(value, str) else ""


@dataclass
class ExternalReference:
    """A link out to a CVE, GHSA, vendor advisory, NR advisory, or NR research brief.

    ``id`` is the reference identifier as published. Note that in the current
    dataset some ``vendor-advisory`` references carry free-text/URL prose in ``id``
    rather than a clean identifier; this is preserved verbatim (see the validation
    report) and never rewritten.
    """

    kind: str
    id: str
    url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    _KNOWN: ClassVar[set[str]] = {"kind", "id", "url"}

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        issues: IssueCollector | None = None,
        locator: str = "external_reference",
    ) -> ExternalReference:
        kind = _require_str(data, "kind", issues, locator)
        if issues is not None and kind and kind not in REFERENCE_KINDS:
            issues.add(f"{locator}.kind", f"unknown reference kind {kind!r}", "warning")
        ref_id = _require_str(data, "id", issues, locator)
        url = data.get("url")
        if url is not None and not isinstance(url, str):
            if issues is not None:
                issues.add(f"{locator}.url", "url is not a string", "warning")
            url = None
        return cls(kind=kind, id=ref_id, url=url, extra=_drop_known(data, cls._KNOWN))

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": self.kind, "id": self.id}
        if self.url is not None:
            out["url"] = self.url
        out.update(self.extra)
        return out


@dataclass
class Instance:
    """A chain-specific occurrence of a technique — the evidence for its
    cross-chain claim."""

    chain: str
    primitive_id: str
    bundle_ref: str
    fidelity: str
    discovery_origin: str
    external_references: list[ExternalReference] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    _KNOWN: ClassVar[set[str]] = {
        "chain",
        "primitive_id",
        "bundle_ref",
        "fidelity",
        "discovery_origin",
        "external_references",
    }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        issues: IssueCollector | None = None,
        locator: str = "instance",
    ) -> Instance:
        chain = _require_str(data, "chain", issues, locator)
        primitive_id = _require_str(data, "primitive_id", issues, locator)
        bundle_ref = _require_str(data, "bundle_ref", issues, locator)
        fidelity = _require_str(data, "fidelity", issues, locator)
        if issues is not None and fidelity and fidelity not in FIDELITY_CLASSES:
            issues.add(f"{locator}.fidelity", f"unknown fidelity {fidelity!r}", "warning")
        origin = _require_str(data, "discovery_origin", issues, locator)
        if issues is not None and origin and origin not in DISCOVERY_ORIGINS:
            issues.add(
                f"{locator}.discovery_origin",
                f"unknown discovery_origin {origin!r}",
                "warning",
            )
        refs = _parse_refs(data.get("external_references"), issues, locator)
        return cls(
            chain=chain,
            primitive_id=primitive_id,
            bundle_ref=bundle_ref,
            fidelity=fidelity,
            discovery_origin=origin,
            external_references=refs,
            extra=_drop_known(data, cls._KNOWN),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "chain": self.chain,
            "primitive_id": self.primitive_id,
            "bundle_ref": self.bundle_ref,
            "fidelity": self.fidelity,
            "discovery_origin": self.discovery_origin,
            "external_references": [r.to_dict() for r in self.external_references],
        }
        out.update(self.extra)
        return out

    @property
    def fidelity_strength(self) -> int:
        return fidelity_strength(self.fidelity)


@dataclass
class Technique:
    """The citable unit. Opaque stable ``id``; ``family`` is an attribute (a
    technique can be reclassified without its id changing); zero or more instances
    and external references.

    ``family`` is the published MECHANISM taxonomy and is ``None`` while the registry
    has not classified the technique - it is never inferred from ``producer_family``,
    because the producer's surface-defined labels have no honest mechanical target.
    Anything grouping by family must treat ``None`` as unknown rather than as a shared
    value; see :meth:`is_classified`.
    """

    id: str
    name: str
    mechanism: str
    #: Published mechanism family, or None while pending classification.
    family: str | None
    status: str
    first_seen: str
    display_name: str | None = None
    #: The producing pipeline's own clustering label. Provenance, not the taxonomy.
    producer_family: str | None = None
    #: Where the attacker's input enters. Present only when classified.
    surface: str | None = None
    #: Why the node's bound failed to apply. Present only when classified.
    bound_failure: str | None = None
    #: Secondary family where a technique is genuinely dual and no reproduction
    #: measured which resource binds first.
    dual_with: str | None = None
    #: ``curated`` or ``pending``; always present on a current registry response.
    classification: str = "pending"
    instances: list[Instance] = field(default_factory=list)
    external_references: list[ExternalReference] = field(default_factory=list)
    provenance_note: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_classified(self) -> bool:
        """Whether this technique carries a mechanism family. Prefer this over
        truth-testing ``family``: it states the intent at the call site."""
        return self.family is not None

    _KNOWN: ClassVar[set[str]] = {
        "id",
        "name",
        "display_name",
        "mechanism",
        "family",
        "producer_family",
        "surface",
        "bound_failure",
        "dual_with",
        "classification",
        "status",
        "first_seen",
        "instances",
        "external_references",
        "provenance_note",
    }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        issues: IssueCollector | None = None,
    ) -> Technique:
        tid = _require_str(data, "id", issues, "technique")
        locator = tid or "technique(?)"
        if issues is not None and tid and not _ID_RE.match(tid):
            issues.add(f"{locator}.id", f"id does not match {TECHNIQUE_ID_PATTERN}")
        name = _require_str(data, "name", issues, locator)
        mechanism = _require_str(data, "mechanism", issues, locator)
        # `family` is nullable by contract: a technique the registry has not
        # classified is served null with classification "pending". That is a
        # well-formed record, not a malformed one, so an absent family is never
        # reported as an issue - only a present-but-unknown one.
        family = _optional_str(data, "family", issues, locator)
        if issues is not None and family and family not in MECHANISM_FAMILIES:
            issues.add(f"{locator}.family", f"unknown mechanism family {family!r}", "warning")
        producer_family = _optional_str(data, "producer_family", issues, locator)
        if issues is not None and producer_family and producer_family not in FAMILIES:
            issues.add(
                f"{locator}.producer_family",
                f"unknown producer family {producer_family!r}",
                "warning",
            )
        surface = _optional_str(data, "surface", issues, locator)
        if issues is not None and surface and surface not in SURFACES:
            issues.add(f"{locator}.surface", f"unknown surface {surface!r}", "warning")
        bound_failure = _optional_str(data, "bound_failure", issues, locator)
        if issues is not None and bound_failure and bound_failure not in BOUND_FAILURES:
            issues.add(
                f"{locator}.bound_failure",
                f"unknown bound failure {bound_failure!r}",
                "warning",
            )
        dual_with = _optional_str(data, "dual_with", issues, locator)
        classification = _optional_str(data, "classification", issues, locator) or (
            "curated" if family else "pending"
        )
        status = _require_str(data, "status", issues, locator)
        if issues is not None and status and status not in STATUSES:
            issues.add(f"{locator}.status", f"unknown status {status!r}", "warning")
        first_seen = _require_str(data, "first_seen", issues, locator)
        if issues is not None and first_seen and not _DATE_RE.match(first_seen):
            issues.add(f"{locator}.first_seen", f"malformed date {first_seen!r}")

        display_name = _optional_str(data, "display_name", issues, locator)
        provenance_note = _optional_str(data, "provenance_note", issues, locator)

        instances: list[Instance] = []
        raw_instances = data.get("instances", [])
        if isinstance(raw_instances, list):
            for i, raw in enumerate(raw_instances):
                if isinstance(raw, dict):
                    instances.append(Instance.from_dict(raw, issues, f"{locator}.instances[{i}]"))
                elif issues is not None:
                    issues.add(f"{locator}.instances[{i}]", "instance is not an object")
        elif issues is not None:
            issues.add(f"{locator}.instances", "instances is not an array")

        refs = _parse_refs(data.get("external_references"), issues, locator)
        return cls(
            id=tid,
            name=name,
            mechanism=mechanism,
            family=family,
            status=status,
            first_seen=first_seen,
            display_name=display_name,
            producer_family=producer_family,
            surface=surface,
            bound_failure=bound_failure,
            dual_with=dual_with,
            classification=classification,
            instances=instances,
            external_references=refs,
            provenance_note=provenance_note,
            extra=_drop_known(data, cls._KNOWN),
        )

    def to_dict(self) -> dict[str, Any]:
        # Canonical field order (matches the feed's per-technique JSON).
        out: dict[str, Any] = {"id": self.id, "name": self.name}
        if self.display_name is not None:
            out["display_name"] = self.display_name
        out["mechanism"] = self.mechanism
        out["family"] = self.family
        if self.producer_family is not None:
            out["producer_family"] = self.producer_family
        if self.surface is not None:
            out["surface"] = self.surface
        if self.bound_failure is not None:
            out["bound_failure"] = self.bound_failure
        if self.dual_with is not None:
            out["dual_with"] = self.dual_with
        out["classification"] = self.classification
        out["status"] = self.status
        out["first_seen"] = self.first_seen
        out["instances"] = [i.to_dict() for i in self.instances]
        out["external_references"] = [r.to_dict() for r in self.external_references]
        if self.provenance_note is not None:
            out["provenance_note"] = self.provenance_note
        out.update(self.extra)
        return out

    # -- derived (computed, never stored) --------------------------------------

    @property
    def display(self) -> str:
        """The human label: ``display_name`` when present, else the stable ``name``."""
        return self.display_name if self.display_name else self.name

    @property
    def url(self) -> str:
        """Permanent citable URL for this technique."""
        return f"{NRDAX_SITE}/techniques/{self.id}"

    @property
    def chains(self) -> list[str]:
        """Sorted, de-duplicated chains this technique has a reproduced instance on."""
        return sorted({i.chain for i in self.instances})

    @property
    def is_reproduced(self) -> bool:
        return bool(self.instances)

    @property
    def reproduction_status(self) -> str:
        """Derived: ``reproduced`` (has an instance) or ``known`` (no instance)."""
        return "reproduced" if self.instances else "known"

    def iter_references(self) -> Iterator[tuple[str, ExternalReference]]:
        """Yield ``(scope, reference)`` for every reference on the technique and on
        each instance. ``scope`` is ``"technique"`` or the owning chain."""
        for ref in self.external_references:
            yield "technique", ref
        for inst in self.instances:
            for ref in inst.external_references:
                yield inst.chain, ref

    @property
    def reference_ids(self) -> set[str]:
        return {ref.id for _, ref in self.iter_references()}

    def references_of_kind(self, *kinds: str) -> list[ExternalReference]:
        wanted = set(kinds)
        return [ref for _, ref in self.iter_references() if ref.kind in wanted]

    @property
    def strongest_fidelity(self) -> str | None:
        """The strongest fidelity across all instances, or ``None`` if known-only."""
        if not self.instances:
            return None
        return max(self.instances, key=lambda i: i.fidelity_strength).fidelity


def _optional_str(
    data: dict[str, Any], key: str, issues: IssueCollector | None, locator: str
) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        if issues is not None:
            issues.add(f"{locator}.{key}", f"{key} is not a string", "warning")
        return None
    return value


def _parse_refs(raw: Any, issues: IssueCollector | None, locator: str) -> list[ExternalReference]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        if issues is not None:
            issues.add(f"{locator}.external_references", "not an array")
        return []
    refs: list[ExternalReference] = []
    for i, item in enumerate(raw):
        if isinstance(item, dict):
            refs.append(
                ExternalReference.from_dict(item, issues, f"{locator}.external_references[{i}]")
            )
        elif issues is not None:
            issues.add(f"{locator}.external_references[{i}]", "reference is not an object")
    return refs


@dataclass(frozen=True)
class KnownCoverage:
    """A technique's known-but-not-reproduced chain coverage: chains a catalogued
    public disclosure names, with no reproduced instance."""

    technique_id: str
    chains: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnownCoverage:
        chains = data.get("chains", [])
        return cls(
            technique_id=str(data.get("technique_id", "")),
            chains=tuple(c for c in chains if isinstance(c, str)),
        )


@dataclass(frozen=True)
class CoverageCell:
    """A reproduced technique×chain cell, recording the strongest evidence there."""

    technique_id: str
    chain: str
    strongest_fidelity: str
    instance_count: int


@dataclass(frozen=True)
class KnownCell:
    """A known-but-not-reproduced technique×chain cell."""

    technique_id: str
    chain: str


@dataclass(frozen=True)
class CoverageMatrix:
    """The derived coverage matrix (technique × chain). ``cells`` are reproduced,
    ``known`` are catalogued-but-not-reproduced; anything in neither is a gap."""

    chains: tuple[str, ...]
    cells: tuple[CoverageCell, ...]
    known: tuple[KnownCell, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chains": list(self.chains),
            "cells": [
                {
                    "technique_id": c.technique_id,
                    "chain": c.chain,
                    "strongest_fidelity": c.strongest_fidelity,
                    "instance_count": c.instance_count,
                }
                for c in self.cells
            ],
            "known": [{"technique_id": k.technique_id, "chain": k.chain} for k in self.known],
        }


@dataclass(frozen=True)
class FamilyCount:
    """A family and how many techniques currently carry it.

    ``axis`` says which taxonomy the name belongs to: ``mechanism`` for the published
    families, ``producer-class`` for the producing pipeline's own labels. A name such
    as ``memory_amp`` occurs on both axes with different counts, so a count read
    without its axis is meaningless."""

    name: str
    technique_count: int
    axis: str = "mechanism"
