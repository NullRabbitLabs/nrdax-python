from __future__ import annotations

import pytest

from nrdax import NRDAX
from nrdax.errors import NotFoundError
from tests.conftest import make_technique


def test_get_is_case_insensitive(fixture_registry):
    assert fixture_registry.get("nrdax-t0001").id == "NRDAX-T0001"


def test_get_unknown_raises(fixture_registry):
    with pytest.raises(NotFoundError):
        fixture_registry.get("NRDAX-T9999")


def test_find_returns_none(fixture_registry):
    assert fixture_registry.find("NRDAX-T9999") is None


def test_container_protocol(fixture_registry):
    assert len(fixture_registry) == 3
    assert "NRDAX-T0001" in fixture_registry
    assert "NRDAX-T9999" not in fixture_registry
    assert [t.id for t in fixture_registry] == ["NRDAX-T0001", "NRDAX-T0002", "NRDAX-T0003"]


def test_techniques_sorted_by_id():
    reg = NRDAX.from_memory([make_technique(id="NRDAX-T0003"), make_technique(id="NRDAX-T0001")])
    assert [t.id for t in reg] == ["NRDAX-T0001", "NRDAX-T0003"]


def test_duplicate_id_recorded_as_issue():
    reg = NRDAX.from_memory([make_technique(id="NRDAX-T0001"), make_technique(id="NRDAX-T0001")])
    assert len(reg) == 1
    assert any("duplicate" in i.message for i in reg.validate())


def test_families_include_zero_counts(fixture_registry):
    # The mechanism axis: always all five, zero counts included, so an empty family
    # reads as empty rather than missing.
    fams = {f.name: f.technique_count for f in fixture_registry.families()}
    assert fams["response_amp"] == 1
    assert fams["compute_amp"] == 1
    assert fams["fault_termination"] == 0
    assert len(fams) == 5
    assert all(f.axis == "mechanism" for f in fixture_registry.families())


def test_producer_families_are_a_separate_axis(fixture_registry):
    # The producing pipeline's own vocabulary, kept apart: `rpc_handler_cpu` is a
    # producer label whose only technique is compute_amp by mechanism.
    prod = {f.name: f.technique_count for f in fixture_registry.producer_families()}
    assert prod["rpc_handler_cpu"] == 1
    assert prod["benign"] == 0  # in the vocabulary, unused
    assert len(prod) == 29
    assert all(f.axis == "producer-class" for f in fixture_registry.producer_families())


def test_chains_and_instances(fixture_registry):
    assert "solana" in fixture_registry.chains()
    sol = fixture_registry.instances(chain="solana")
    assert all(inst.chain == "solana" for _, inst in sol)


def test_by_reference(fixture_registry):
    hits = fixture_registry.by_reference("CVE-2025-1111")
    assert [t.id for t in hits] == ["NRDAX-T0001"]


def test_known_coverage_unknown_target_is_warning():
    reg = NRDAX.from_memory(
        [make_technique(id="NRDAX-T0001")],
        known_coverage=[{"technique_id": "NRDAX-T9999", "chains": ["bitcoin"]}],
    )
    assert any("unknown technique" in i.message for i in reg.validate())


def test_to_release_dict_preserves_version_and_records(fixture_registry):
    rel = fixture_registry.to_release_dict()
    assert rel["version"] == "v1.0"
    assert rel["doi"] == "10.5281/zenodo.9990001"
    assert rel["technique_count"] == 3
    assert len(rel["techniques"]) == 3


def test_filter_composes(fixture_registry):
    # T0001 is response_amp with a solana instance
    hits = fixture_registry.filter(family="response_amp", chain="solana")
    assert [t.id for t in hits] == ["NRDAX-T0001"]


def test_fixture_loads_clean(fixture_registry):
    # A loaded dataset validates cleanly and indexes every technique.
    assert len(fixture_registry) == 3
    assert fixture_registry.validate() == []
