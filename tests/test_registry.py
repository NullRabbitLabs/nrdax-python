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
    fams = {f.name: f.technique_count for f in fixture_registry.families()}
    assert fams["response_amp"] == 1
    assert fams["benign"] == 0  # in the vocabulary, unused
    assert len(fams) == 29


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


def test_bundled_loads_clean(bundled_registry):
    # Increment-only registry: never shrinks below the shipped snapshot size.
    assert len(bundled_registry) >= 388
    assert bundled_registry.validate() == []
