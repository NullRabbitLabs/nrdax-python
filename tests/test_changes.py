from __future__ import annotations

from nrdax import NRDAX
from nrdax.changes import diff, since
from tests.conftest import make_instance, make_technique


def test_since_uses_first_seen(fixture_registry):
    # fixture first_seen dates: T0001 2025-01-15, T0002 2025-02-20, T0003 2024-11-02
    hits = since(fixture_registry, "2025-02-01")
    assert [t.id for t in hits] == ["NRDAX-T0002"]


def test_since_ordering(bundled_registry):
    hits = since(bundled_registry, "2026-07-01")
    dates = [t.first_seen for t in hits]
    assert dates == sorted(dates)


def test_diff_added_and_removed():
    old = NRDAX.from_memory([make_technique(id="NRDAX-T0001")], version="1")
    new = NRDAX.from_memory(
        [make_technique(id="NRDAX-T0001"), make_technique(id="NRDAX-T0002")], version="2"
    )
    cs = diff(old, new)
    kinds = cs.counts_by_kind()
    assert kinds.get("technique_added") == 1
    assert cs.from_version == "1" and cs.to_version == "2"


def test_diff_field_changes():
    old = NRDAX.from_memory([make_technique(id="NRDAX-T0001", family="response_amp", instances=[])])
    new = NRDAX.from_memory(
        [
            make_technique(
                id="NRDAX-T0001",
                family="compute_amp",
                instances=[make_instance(chain="solana")],
                external_references=[{"kind": "cve", "id": "CVE-2025-1"}],
            )
        ]
    )
    kinds = diff(old, new).counts_by_kind()
    assert kinds["family_changed"] == 1
    assert kinds["reproduction_status_changed"] == 1
    assert kinds["instance_added"] == 1
    assert kinds["chain_added"] == 1
    assert kinds["advisory_added"] == 1


def test_diff_predicate_filters():
    old = NRDAX.from_memory([])
    new = NRDAX.from_memory(
        [
            make_technique(id="NRDAX-T0001", family="response_amp"),
            make_technique(id="NRDAX-T0002", family="compute_amp"),
        ]
    )
    from nrdax.queries.filters import build_predicate

    cs = diff(old, new, predicate=build_predicate(family="response_amp"))
    assert cs.counts_by_kind() == {"technique_added": 1}
