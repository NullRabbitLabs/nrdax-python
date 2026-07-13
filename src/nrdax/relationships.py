"""Relationship traversal.

NRDAX has **no asserted technique-to-technique relationship field** (no
parent/child/"related" edges in the schema), so this module surfaces only
relationships that are *derivable from canonical fields*, and labels them as
derived:

* **family** — sibling techniques sharing the same family;
* **chain** — techniques with a reproduced instance on a shared chain;
* **reference** — techniques sharing an external reference id (e.g. the same CVE),
  the strongest real link between two records;
* **instances** — the technique's own instances (its known reproductions);
* **advisories** — the technique's advisory-class references (cve/ghsa/vendor/nr);
* **briefs** — linked NullRabbit research briefs (evidence write-ups).

We never invent parent/child edges the data does not contain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import ExternalReference, Instance, Technique

if TYPE_CHECKING:
    from .registry import NRDAX

_ADVISORY_KINDS = ("cve", "ghsa", "vendor-advisory", "nr-advisory")


@dataclass(frozen=True)
class SharedReference:
    reference: str
    kind: str
    technique_ids: tuple[str, ...]


@dataclass(frozen=True)
class ChainNeighbours:
    chain: str
    technique_ids: tuple[str, ...]


@dataclass
class RelatedResult:
    """Derived relationships for one technique (all ids exclude the subject)."""

    technique_id: str
    family: str
    family_siblings: list[str] = field(default_factory=list)
    chains: list[ChainNeighbours] = field(default_factory=list)
    shared_references: list[SharedReference] = field(default_factory=list)
    instances: list[Instance] = field(default_factory=list)
    advisories: list[ExternalReference] = field(default_factory=list)
    briefs: list[ExternalReference] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (
            self.family_siblings
            or self.chains
            or self.shared_references
            or self.instances
            or self.advisories
            or self.briefs
        )


def related(registry: NRDAX, technique_id: str) -> RelatedResult:
    """Compute derived relationships for ``technique_id`` (raises if unknown)."""
    tech: Technique = registry.get(technique_id)
    tid = tech.id

    siblings = sorted(t.id for t in registry.techniques_by_family(tech.family) if t.id != tid)

    chains: list[ChainNeighbours] = []
    for chain in tech.chains:
        neighbours = sorted(t.id for t in registry.techniques_by_chain(chain) if t.id != tid)
        if neighbours:
            chains.append(ChainNeighbours(chain=chain, technique_ids=tuple(neighbours)))

    shared: list[SharedReference] = []
    seen_refs: set[str] = set()
    for _, ref in tech.iter_references():
        if ref.id in seen_refs:
            continue
        seen_refs.add(ref.id)
        others = sorted(t.id for t in registry.techniques_with_reference(ref.id) if t.id != tid)
        if others:
            shared.append(
                SharedReference(reference=ref.id, kind=ref.kind, technique_ids=tuple(others))
            )

    advisories = [ref for _, ref in tech.iter_references() if ref.kind in _ADVISORY_KINDS]
    briefs = [ref for _, ref in tech.iter_references() if ref.kind == "nr-brief"]

    return RelatedResult(
        technique_id=tid,
        family=tech.family,
        family_siblings=siblings,
        chains=chains,
        shared_references=shared,
        instances=list(tech.instances),
        advisories=advisories,
        briefs=briefs,
    )
