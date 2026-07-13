from __future__ import annotations

import pytest

from nrdax import NRDAX
from nrdax.errors import NotFoundError
from tests.conftest import make_instance, make_technique


def _reg():
    # Two techniques share CVE-2025-9 (strongest link) and the ethereum chain;
    # a third only shares the family with T0001.
    return NRDAX.from_memory(
        [
            make_technique(
                id="NRDAX-T0001",
                family="response_amp",
                external_references=[{"kind": "cve", "id": "CVE-2025-9"}],
                instances=[make_instance(chain="ethereum", primitive_id="p1")],
            ),
            make_technique(
                id="NRDAX-T0002",
                family="connection_exhaustion",
                external_references=[{"kind": "cve", "id": "CVE-2025-9"}],
                instances=[make_instance(chain="ethereum", primitive_id="p2")],
            ),
            make_technique(id="NRDAX-T0003", family="response_amp", instances=[]),
        ]
    )


def test_family_siblings():
    rel = _reg().related("NRDAX-T0001")
    assert rel.family == "response_amp"
    assert rel.family_siblings == ["NRDAX-T0003"]


def test_shared_chain():
    rel = _reg().related("NRDAX-T0001")
    chains = {c.chain: c.technique_ids for c in rel.chains}
    assert chains["ethereum"] == ("NRDAX-T0002",)


def test_shared_reference_is_strongest_link():
    rel = _reg().related("NRDAX-T0001")
    refs = {s.reference: s.technique_ids for s in rel.shared_references}
    assert refs["CVE-2025-9"] == ("NRDAX-T0002",)


def test_instances_and_advisories():
    rel = _reg().related("NRDAX-T0001")
    assert len(rel.instances) == 1
    assert [r.id for r in rel.advisories] == ["CVE-2025-9"]


def test_isolated_technique_has_empty_relations():
    reg = NRDAX.from_memory([make_technique(id="NRDAX-T0009", family="benign", instances=[])])
    rel = reg.related("NRDAX-T0009")
    assert rel.is_empty()


def test_related_unknown_raises():
    with pytest.raises(NotFoundError):
        _reg().related("NRDAX-T9999")
