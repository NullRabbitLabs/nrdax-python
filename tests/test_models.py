from __future__ import annotations

import pytest

from nrdax.errors import IssueCollector, ValidationError
from nrdax.models import ExternalReference, Instance, Technique
from tests.conftest import make_instance, make_technique


def test_round_trip_preserves_canonical_shape():
    data = make_technique(
        instances=[
            make_instance(external_references=[{"kind": "cve", "id": "CVE-2025-1", "url": "u"}])
        ],
        external_references=[{"kind": "nr-advisory", "id": "NR-2025-014"}],
    )
    t = Technique.from_dict(data)
    assert t.to_dict() == data  # exact round-trip, canonical field order


def test_missing_vs_empty_are_distinguished():
    without = Technique.from_dict(make_technique(display_name=None))
    # display_name absent -> None (missing); instances present-but-empty -> []
    d = make_technique()
    del d["display_name"]
    del d["instances"]
    parsed = Technique.from_dict(d)
    assert parsed.display_name is None
    assert parsed.instances == []
    assert "display_name" not in parsed.to_dict()
    assert without.display_name is None


def test_unknown_fields_preserved_in_extra_and_round_trip():
    data = make_technique(x_custom="keepme", another={"nested": 1})
    t = Technique.from_dict(data)
    assert t.extra["x_custom"] == "keepme"
    assert t.to_dict()["another"] == {"nested": 1}


def test_derived_properties():
    t = Technique.from_dict(
        make_technique(
            display_name=None,
            instances=[
                make_instance(chain="solana", fidelity="lab"),
                make_instance(chain="ethereum", fidelity="proxy", primitive_id="p2"),
            ],
        )
    )
    assert t.display == t.name  # falls back to slug when no display_name
    assert t.chains == ["ethereum", "solana"]
    assert t.is_reproduced is True
    assert t.reproduction_status == "reproduced"
    assert t.strongest_fidelity == "lab"  # lab(2) > proxy(1)


def test_known_only_reproduction_status():
    t = Technique.from_dict(make_technique(instances=[]))
    assert t.reproduction_status == "known"
    assert t.strongest_fidelity is None


def test_iter_references_covers_technique_and_instances():
    t = Technique.from_dict(
        make_technique(
            external_references=[{"kind": "nr-advisory", "id": "NR-1"}],
            instances=[make_instance(external_references=[{"kind": "cve", "id": "CVE-1"}])],
        )
    )
    scopes = {scope for scope, _ in t.iter_references()}
    assert scopes == {"technique", "solana"}
    assert t.reference_ids == {"NR-1", "CVE-1"}


def test_lenient_collects_issues_without_raising():
    issues = IssueCollector()
    Technique.from_dict({"id": "BAD-ID", "name": "", "family": "nope"}, issues)
    locators = {i.locator for i in issues.issues}
    assert any("id" in loc for loc in locators)
    assert issues.errors  # missing required fields recorded as errors


def test_strict_raises_on_first_error():
    issues = IssueCollector(strict=True)
    with pytest.raises(ValidationError):
        Technique.from_dict({"name": "x"}, issues)  # missing id


def test_unknown_vocab_values_are_warnings_not_errors():
    issues = IssueCollector()
    Technique.from_dict(make_technique(family="totally_new_family", status="active"), issues)
    assert issues.errors == []
    assert any("family" in w.locator for w in issues.warnings)


def test_external_reference_optional_url():
    r = ExternalReference.from_dict({"kind": "cve", "id": "CVE-1"})
    assert r.url is None
    assert r.to_dict() == {"kind": "cve", "id": "CVE-1"}


def test_instance_fidelity_strength():
    inst = Instance.from_dict(make_instance(fidelity="production-captured"))
    assert inst.fidelity_strength == 4
