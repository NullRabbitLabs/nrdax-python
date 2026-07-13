from __future__ import annotations

import pytest

from nrdax import NRDAX
from nrdax.errors import InvalidArgumentError
from nrdax.queries import filters
from tests.conftest import make_instance, make_technique


def _reg():
    return NRDAX.from_memory(
        [
            make_technique(
                id="NRDAX-T0001",
                family="response_amp",
                instances=[
                    make_instance(
                        chain="solana",
                        fidelity="lab",
                        discovery_origin="original-research",
                        external_references=[{"kind": "cve", "id": "CVE-2025-1"}],
                    )
                ],
            ),
            make_technique(id="NRDAX-T0002", family="connection_exhaustion", instances=[]),
        ]
    )


def test_by_family():
    assert [t.id for t in _reg().filter(family="response_amp")] == ["NRDAX-T0001"]


def test_by_chain_case_insensitive():
    assert [t.id for t in _reg().filter(chain="SOLANA")] == ["NRDAX-T0001"]


def test_by_reproduction_status():
    assert [t.id for t in _reg().filter(reproduction_status="known")] == ["NRDAX-T0002"]
    assert [t.id for t in _reg().filter(reproduction_status="reproduced")] == ["NRDAX-T0001"]


def test_by_fidelity_and_origin():
    assert [t.id for t in _reg().filter(fidelity="lab")] == ["NRDAX-T0001"]
    assert [t.id for t in _reg().filter(discovery_origin="original-research")] == ["NRDAX-T0001"]


def test_by_reference_exact_and_contains():
    assert [t.id for t in _reg().filter(reference="CVE-2025-1")] == ["NRDAX-T0001"]
    assert _reg().filter(reference="2025") == []
    assert [t.id for t in _reg().filter(reference="2025", reference_contains=True)] == [
        "NRDAX-T0001"
    ]


def test_composition_ands():
    assert _reg().filter(family="response_amp", chain="sui") == []


def test_invalid_values_raise():
    # Closed vocabularies validate; family is intentionally open (data may extend it),
    # so the library does not restrict it (the CLI's --family uses argparse choices).
    with pytest.raises(InvalidArgumentError):
        _reg().filter(status="nope")
    with pytest.raises(InvalidArgumentError):
        _reg().filter(fidelity="nope")
    with pytest.raises(InvalidArgumentError):
        _reg().filter(discovery_origin="nope")
    with pytest.raises(InvalidArgumentError):
        _reg().filter(reproduction_status="maybe")


def test_implementation_is_text_heuristic():
    reg = NRDAX.from_memory(
        [
            make_technique(
                id="NRDAX-T0001", instances=[make_instance(primitive_id="agave_rpc_flood")]
            )
        ]
    )
    assert [t.id for t in reg.filter(implementation="agave")] == ["NRDAX-T0001"]


def test_empty_predicate_matches_all():
    pred = filters.build_predicate()
    assert all(pred(t) for t in _reg())
