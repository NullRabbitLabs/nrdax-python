from __future__ import annotations

import uuid

from nrdax.exporters import stix_bundle, stix_dumps, technique_ids, validate_bundle
from nrdax.exporters.stix_exporter import NAMESPACE, attack_pattern
from tests.conftest import FIXTURE_FEED


def test_byte_identical_to_backend_golden(fixture_registry):
    mine = stix_dumps(stix_bundle(list(fixture_registry), fixture_registry.version))
    golden = (FIXTURE_FEED / "stix.json").read_text()
    assert mine == golden


def test_deterministic_uuid5_matches_backend():
    assert str(uuid.uuid5(NAMESPACE, "NRDAX-T0001")) == "b3bcddec-2c42-5bfd-a0fa-f75afef5d7d1"


def test_identity_round_trips(fixture_registry):
    bundle = stix_bundle(list(fixture_registry), fixture_registry.version)
    assert technique_ids(bundle) == ["NRDAX-T0001", "NRDAX-T0002", "NRDAX-T0003"]


def test_custom_properties_present(fixture_registry):
    ap = attack_pattern(fixture_registry.get("NRDAX-T0001"))
    assert ap["x_nrdax_family"] == "response_amp"
    assert ap["x_nrdax_status"] == "active"
    assert ap["x_nrdax_chains"] == ["ethereum", "solana"]
    # NRDAX id anchored in external_references
    assert ap["external_references"][0]["source_name"] == "nrdax"


def test_validate_clean(fixture_registry):
    bundle = stix_bundle(list(fixture_registry), fixture_registry.version)
    assert validate_bundle(bundle) == []


def test_validate_flags_bad_bundle():
    errors = validate_bundle({"type": "notbundle", "objects": [{"type": "attack-pattern"}]})
    assert errors  # multiple structural problems


def test_full_dataset_valid(bundled_registry):
    bundle = stix_bundle(list(bundled_registry), bundled_registry.version)
    assert validate_bundle(bundle) == []
    assert len(technique_ids(bundle)) == 381


def test_bundle_id_is_deterministic(fixture_registry):
    a = stix_bundle(list(fixture_registry), "v1.0")["id"]
    b = stix_bundle(list(fixture_registry), "v1.0")["id"]
    c = stix_bundle(list(fixture_registry), "v2.0")["id"]
    assert a == b and a != c
