"""The mechanism classification: a nullable ``family`` and the axes beside it.

The registry serves ``family`` as the published MECHANISM taxonomy. A technique it
has not classified yet is served ``family: null`` with ``classification: "pending"``,
and the producing pipeline's own label is kept separately as ``producer_family``.

Nullability is the part that bites. Anything grouping techniques by family has to
treat "pending" as unknown rather than as a shared value, or every unclassified
technique becomes a sibling of every other one. On the live registry that is 323 of
420 techniques.
"""

from __future__ import annotations

from nrdax import NRDAX
from nrdax.models import Technique
from nrdax.queries.filters import by_family, by_producer_family
from nrdax.relationships import related
from nrdax.vocab import BOUND_FAILURES, MECHANISM_FAMILIES, SURFACES


def technique(tid: str, **over) -> Technique:
    data = {
        "id": tid,
        "name": tid.lower(),
        "mechanism": "mech",
        "family": None,
        "producer_family": "gossip_abuse",
        "classification": "pending",
        "status": "active",
        "first_seen": "2026-01-01",
        "instances": [],
        "external_references": [],
    }
    data.update(over)
    return Technique.from_dict(data)


# ── parsing ───────────────────────────────────────────────────────────────────


def test_pending_technique_parses_with_a_null_family() -> None:
    t = technique("NRDAX-T0999")
    assert t.family is None
    assert t.classification == "pending"
    assert t.producer_family == "gossip_abuse"
    assert t.surface is None
    assert t.bound_failure is None
    assert not t.is_classified


def test_curated_technique_carries_the_full_classification() -> None:
    t = technique(
        "NRDAX-T0392",
        family="fault_termination",
        producer_family="protocol_logic_exploit",
        surface="p2p-gossip",
        bound_failure="absent-invariant",
        classification="curated",
    )
    assert t.family == "fault_termination"
    assert t.producer_family == "protocol_logic_exploit"
    assert t.surface == "p2p-gossip"
    assert t.bound_failure == "absent-invariant"
    assert t.is_classified


def test_dual_marking_is_preserved() -> None:
    t = technique(
        "NRDAX-T0408",
        family="compute_amp",
        producer_family="memory_amp",
        surface="consensus-ingest",
        bound_failure="late",
        dual_with="memory_amp",
        classification="curated",
    )
    assert t.dual_with == "memory_amp"


def test_a_null_family_is_not_reported_as_a_validation_issue() -> None:
    """A pending technique is well-formed, not malformed. Reporting it as an issue
    would make the registry's own honest gap look like a data defect."""
    from nrdax.models import IssueCollector

    issues = IssueCollector()
    technique("NRDAX-T0999")
    Technique.from_dict(
        {
            "id": "NRDAX-T0999",
            "name": "x",
            "mechanism": "m",
            "family": None,
            "producer_family": "gossip_abuse",
            "classification": "pending",
            "status": "active",
            "first_seen": "2026-01-01",
        },
        issues,
    )
    assert not [i for i in issues.issues if "family" in i.locator]


def test_an_unknown_mechanism_family_is_still_flagged() -> None:
    from nrdax.models import IssueCollector

    issues = IssueCollector()
    Technique.from_dict(
        {
            "id": "NRDAX-T0001",
            "name": "x",
            "mechanism": "m",
            "family": "not_a_family",
            "producer_family": "memory_amp",
            "classification": "curated",
            "status": "active",
            "first_seen": "2026-01-01",
        },
        issues,
    )
    assert [i for i in issues.issues if "family" in i.locator]


def test_round_trip_preserves_both_axes() -> None:
    t = technique(
        "NRDAX-T0100",
        family="compute_amp",
        producer_family="connection_exhaustion",
        surface="p2p-gossip",
        bound_failure="late",
        classification="curated",
    )
    d = t.to_dict()
    assert d["family"] == "compute_amp"
    assert d["producer_family"] == "connection_exhaustion"
    assert Technique.from_dict(d).family == "compute_amp"


# ── grouping must not collapse the pending techniques together ────────────────


def _registry(techs: list[Technique]) -> NRDAX:
    return NRDAX.from_memory([t.to_dict() for t in techs])


def test_techniques_by_family_never_groups_pending_techniques() -> None:
    a = technique("NRDAX-T0001")
    b = technique("NRDAX-T0002")
    c = technique("NRDAX-T0003", family="memory_amp", classification="curated")
    reg = _registry([a, b, c])
    assert [t.id for t in reg.techniques_by_family("memory_amp")] == ["NRDAX-T0003"]
    # The pending ones are reachable, but not under any mechanism family.
    assert reg.techniques_by_family(None) == []
    for fam in MECHANISM_FAMILIES:
        assert a not in reg.techniques_by_family(fam)


def test_unclassified_is_queryable_as_its_own_thing() -> None:
    a = technique("NRDAX-T0001")
    c = technique("NRDAX-T0003", family="memory_amp", classification="curated")
    reg = _registry([a, c])
    assert [t.id for t in reg.unclassified()] == ["NRDAX-T0001"]
    assert [t.id for t in reg.classified()] == ["NRDAX-T0003"]


def test_techniques_by_producer_family_still_works() -> None:
    a = technique("NRDAX-T0001", producer_family="gossip_abuse")
    b = technique(
        "NRDAX-T0002",
        family="compute_amp",
        producer_family="rpc_handler_cpu",
        classification="curated",
    )
    reg = _registry([a, b])
    assert [t.id for t in reg.techniques_by_producer_family("rpc_handler_cpu")] == ["NRDAX-T0002"]


# ── relationships ─────────────────────────────────────────────────────────────


def test_two_pending_techniques_are_never_family_siblings() -> None:
    a = technique("NRDAX-T0001")
    b = technique("NRDAX-T0002")
    reg = _registry([a, b])
    assert related(reg, "NRDAX-T0001").family_siblings == []


def test_classified_techniques_are_siblings_when_they_share_a_family() -> None:
    a = technique("NRDAX-T0001", family="memory_amp", classification="curated")
    b = technique("NRDAX-T0002", family="memory_amp", classification="curated")
    c = technique("NRDAX-T0003", family="compute_amp", classification="curated")
    reg = _registry([a, b, c])
    assert related(reg, "NRDAX-T0001").family_siblings == ["NRDAX-T0002"]


# ── filters ───────────────────────────────────────────────────────────────────


def test_by_family_filters_on_the_mechanism_axis() -> None:
    a = technique(
        "NRDAX-T0001",
        family="compute_amp",
        producer_family="rpc_handler_cpu",
        classification="curated",
    )
    b = technique("NRDAX-T0002")
    assert by_family("compute_amp")(a)
    assert not by_family("compute_amp")(b)
    assert not by_family("rpc_handler_cpu")(a), "the producer label is a different axis"


def test_by_producer_family_filters_on_the_producer_axis() -> None:
    a = technique(
        "NRDAX-T0001",
        family="compute_amp",
        producer_family="rpc_handler_cpu",
        classification="curated",
    )
    assert by_producer_family("rpc_handler_cpu")(a)
    assert not by_producer_family("compute_amp")(a)


# ── vocabularies ──────────────────────────────────────────────────────────────


def test_the_mechanism_vocabularies_match_the_registry() -> None:
    assert set(MECHANISM_FAMILIES) == {
        "compute_amp",
        "connection_exhaustion",
        "fault_termination",
        "memory_amp",
        "response_amp",
    }
    assert set(SURFACES) == {
        "consensus-ingest",
        "control-plane",
        "p2p-gossip",
        "rpc-api",
        "sync-state-import",
    }
    assert set(BOUND_FAILURES) == {
        "absent-invariant",
        "late",
        "mis-quantified",
        "mis-scoped",
        "no-bound",
    }
