from __future__ import annotations

from nrdax import NRDAX
from nrdax.queries.search import search
from tests.conftest import make_instance, make_technique


def _reg():
    return NRDAX.from_memory(
        [
            make_technique(
                id="NRDAX-T0001",
                display_name="RPC getBlock response amplification",
                mechanism="unauthenticated getBlock request amplifies response size",
                instances=[make_instance(chain="solana")],
            ),
            make_technique(
                id="NRDAX-T0002",
                display_name="TCP connection table exhaustion",
                mechanism="half-open connections exhaust the connection table",
                family="connection_exhaustion",
                instances=[make_instance(chain="sui", primitive_id="sui_conn")],
            ),
        ]
    )


def test_exact_id_short_circuits_to_top():
    results = _reg().search("nrdax-t0002")
    assert results[0].technique.id == "NRDAX-T0002"
    assert results[0].matched_fields == ("id",)


def test_empty_query_returns_nothing():
    assert _reg().search("") == []
    assert _reg().search("   ") == []


def test_ranking_is_deterministic_and_scored():
    r = _reg().search("connection exhaustion")
    assert r[0].technique.id == "NRDAX-T0002"
    assert r[0].score > 0


def test_matched_fields_reported():
    r = _reg().search("getBlock")
    top = r[0]
    assert "mechanism" in top.matched_fields or "display_name" in top.matched_fields


def test_field_restriction():
    reg = _reg()
    # 'solana' only appears in a chain field
    none = reg.search("solana", fields=("mechanism",))
    some = reg.search("solana", fields=("chain",))
    assert none == []
    assert some and some[0].technique.id == "NRDAX-T0001"


def test_tie_break_by_id():
    reg = NRDAX.from_memory(
        [
            make_technique(id="NRDAX-T0002", mechanism="alpha token here"),
            make_technique(id="NRDAX-T0001", mechanism="alpha token here"),
        ]
    )
    r = reg.search("alpha")
    assert [x.technique.id for x in r] == ["NRDAX-T0001", "NRDAX-T0002"]


def test_limit_applies():
    reg = _reg()
    assert len(reg.search("exhaustion amplification", limit=1)) == 1


def test_module_search_matches_registry(fixture_registry):
    a = fixture_registry.search("amplification")
    b = search(list(fixture_registry), "amplification")
    assert [x.technique.id for x in a] == [x.technique.id for x in b]
