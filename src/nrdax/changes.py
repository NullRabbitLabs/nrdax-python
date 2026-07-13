"""Change inspection.

NRDAX does not (yet) publish historical versioned releases addressable by version
number, so cross-version comparison is implemented as a **real diff between two
datasets the caller supplies** (two snapshots, cache vs current, bundled vs live) —
never simulated. ``since`` derives "added since a date" from ``first_seen``, which
*is* available on every record. See ``docs/guides/compare-changes.md`` for the
source limitation and how to pin snapshots for reproducible diffs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import Technique

if TYPE_CHECKING:
    from .registry import NRDAX

Predicate = Callable[[Technique], bool]

_ADVISORY_KINDS = frozenset({"cve", "ghsa", "vendor-advisory", "nr-advisory"})


@dataclass(frozen=True)
class Change:
    kind: str  # e.g. "technique_added", "status_changed", "advisory_added"
    technique_id: str
    detail: str
    old: str | None = None
    new: str | None = None


@dataclass
class ChangeSet:
    from_version: str
    to_version: str
    changes: list[Change] = field(default_factory=list)

    def counts_by_kind(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.changes:
            out[c.kind] = out.get(c.kind, 0) + 1
        return dict(sorted(out.items()))

    def __len__(self) -> int:
        return len(self.changes)


def _refs(t: Technique) -> set[tuple[str, str]]:
    return {(ref.kind, ref.id) for _, ref in t.iter_references()}


def _instances(t: Technique) -> dict[tuple[str, str], str]:
    # (chain, primitive_id) -> fidelity
    return {(i.chain, i.primitive_id): i.fidelity for i in t.instances}


def _diff_pair(old: Technique, new: Technique, out: list[Change]) -> None:
    tid = new.id
    if old.display != new.display:
        out.append(Change("name_changed", tid, "display name changed", old.display, new.display))
    if old.family != new.family:
        out.append(Change("family_changed", tid, "family changed", old.family, new.family))
    if old.status != new.status:
        out.append(Change("status_changed", tid, "status changed", old.status, new.status))
    if old.first_seen != new.first_seen:
        out.append(
            Change("first_seen_changed", tid, "first_seen changed", old.first_seen, new.first_seen)
        )
    if old.reproduction_status != new.reproduction_status:
        out.append(
            Change(
                "reproduction_status_changed",
                tid,
                "reproduction status changed",
                old.reproduction_status,
                new.reproduction_status,
            )
        )

    old_inst, new_inst = _instances(old), _instances(new)
    for key in sorted(new_inst.keys() - old_inst.keys()):
        out.append(
            Change("instance_added", tid, f"instance added on {key[0]} ({key[1]})", new=key[1])
        )
    for key in sorted(old_inst.keys() - new_inst.keys()):
        out.append(
            Change("instance_removed", tid, f"instance removed on {key[0]} ({key[1]})", old=key[1])
        )

    old_chains, new_chains = set(old.chains), set(new.chains)
    for chain in sorted(new_chains - old_chains):
        out.append(Change("chain_added", tid, f"chain added: {chain}", new=chain))

    old_refs, new_refs = _refs(old), _refs(new)
    for kind, rid in sorted(new_refs - old_refs):
        if kind in _ADVISORY_KINDS:
            out.append(Change("advisory_added", tid, f"advisory linked: {rid} ({kind})", new=rid))
        elif kind == "nr-brief":
            out.append(Change("brief_added", tid, f"research brief linked: {rid}", new=rid))
        else:
            out.append(Change("reference_added", tid, f"reference added: {rid} ({kind})", new=rid))
    for kind, rid in sorted(old_refs - new_refs):
        out.append(Change("reference_removed", tid, f"reference removed: {rid} ({kind})", old=rid))


def diff(old: NRDAX, new: NRDAX, *, predicate: Predicate | None = None) -> ChangeSet:
    """Compute the changes from ``old`` to ``new`` (optionally filtered to
    techniques matching ``predicate``)."""
    keep = predicate or (lambda _t: True)
    old_ids = {t.id for t in old if keep(t)}
    new_ids = {t.id for t in new if keep(t)}
    changes: list[Change] = []

    for tid in sorted(new_ids - old_ids):
        t = new.get(tid)
        changes.append(Change("technique_added", tid, f"technique added: {t.display}"))
    for tid in sorted(old_ids - new_ids):
        t = old.get(tid)
        changes.append(Change("technique_removed", tid, f"technique removed: {t.display}"))
    for tid in sorted(old_ids & new_ids):
        _diff_pair(old.get(tid), new.get(tid), changes)

    changes.sort(key=lambda c: (c.technique_id, c.kind, c.detail))
    return ChangeSet(from_version=old.version, to_version=new.version, changes=changes)


def since(registry: NRDAX, date: str, *, predicate: Predicate | None = None) -> list[Technique]:
    """Techniques first seen on or after ``date`` (``YYYY-MM-DD``), sorted by
    ``first_seen`` then id."""
    keep = predicate or (lambda _t: True)
    hits = [t for t in registry if keep(t) and t.first_seen and t.first_seen >= date]
    hits.sort(key=lambda t: (t.first_seen, t.id))
    return hits
