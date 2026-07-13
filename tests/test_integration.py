"""Opt-in integration tests against the live NRDAX API.

Deselected by default (the normal suite never touches the network). Run with::

    pytest -m integration

They are skipped automatically if the API is unreachable, so CI without network
egress stays green.
"""

from __future__ import annotations

import pytest

from nrdax import NRDAX
from nrdax.errors import SourceError

pytestmark = pytest.mark.integration


def _load_api() -> NRDAX:
    try:
        return NRDAX.from_api()
    except SourceError as exc:  # pragma: no cover - network dependent
        pytest.skip(f"live API unreachable: {exc}")


def test_live_api_loads_and_matches_schema():
    reg = _load_api()
    assert len(reg) > 0
    assert reg.validate() == [] or all(i.severity != "error" for i in reg.validate())
    # A record retrievable and STIX-exportable.
    first = next(iter(reg))
    from nrdax.exporters import stix_bundle, validate_bundle

    assert validate_bundle(stix_bundle([first], reg.version)) == []


def test_live_get_known_technique():
    reg = _load_api()
    t = reg.get("NRDAX-T0001")
    assert t.id == "NRDAX-T0001"
