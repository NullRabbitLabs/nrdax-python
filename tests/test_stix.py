from __future__ import annotations

import dataclasses
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


def test_full_dataset_valid(fixture_registry):
    bundle = stix_bundle(list(fixture_registry), fixture_registry.version)
    assert validate_bundle(bundle) == []
    assert len(technique_ids(bundle)) == len(fixture_registry)


def test_bundle_id_is_deterministic(fixture_registry):
    a = stix_bundle(list(fixture_registry), "v1.0")["id"]
    b = stix_bundle(list(fixture_registry), "v1.0")["id"]
    c = stix_bundle(list(fixture_registry), "v2.0")["id"]
    assert a == b and a != c


def test_validate_flags_null_properties_and_empty_lists():
    # STIX 2.1 (and the OASIS validator): no property may be null and no list empty,
    # at any depth. The backend's validate_bundle enforces the same rule.
    def bundle(**extra):
        ap = {
            "type": "attack-pattern",
            "spec_version": "2.1",
            "id": "attack-pattern--b3bcddec-2c42-5bfd-a0fa-f75afef5d7d1",
            "created": "2025-01-01T00:00:00.000Z",
            "modified": "2025-01-01T00:00:00.000Z",
            "name": "n",
            **extra,
        }
        return {
            "type": "bundle",
            "id": "bundle--b3bcddec-2c42-5bfd-a0fa-f75afef5d7d1",
            "objects": [ap],
        }

    assert validate_bundle(bundle()) == []
    assert any("x_nrdax_family" in e for e in validate_bundle(bundle(x_nrdax_family=None)))
    assert any("x_nrdax_chains" in e for e in validate_bundle(bundle(x_nrdax_chains=[])))
    assert validate_bundle(
        bundle(external_references=[{"source_name": "s", "url": None}])
    ), "the rule holds inside nested objects too"


def test_pending_technique_without_instances_omits_rather_than_nulls(fixture_registry):
    # The dominant production shape: classification pending, no reproduced instance,
    # and here no producer label either. Each such property is omitted, not null/[].
    t = dataclasses.replace(
        fixture_registry.get("NRDAX-T0002"),
        family=None,
        surface=None,
        bound_failure=None,
        producer_family=None,
        classification="pending",
        instances=[],
    )
    ap = attack_pattern(t)
    for absent in (
        "x_nrdax_family",
        "x_nrdax_surface",
        "x_nrdax_bound_failure",
        "x_nrdax_producer_family",
        "x_nrdax_chains",
    ):
        assert absent not in ap, f"{absent} is omitted, not null/empty"
    assert ap["x_nrdax_classification"] == "pending"
    assert validate_bundle({"type": "bundle", "id": "bundle--b3bcddec-2c42-5bfd-a0fa-f75afef5d7d1", "objects": [ap]}) == []
