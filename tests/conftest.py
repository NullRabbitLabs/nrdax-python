"""Shared test fixtures. Everything here is small and deterministic; no test in the
default suite touches the network (see ``tests/test_integration.py`` for the opt-in
live-API path)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from nrdax import NRDAX

ROOT = Path(__file__).parent
FIXTURE_FEED = ROOT / "fixtures" / "feed"


def make_technique(**overrides: Any) -> dict[str, Any]:
    """A minimal valid technique dict, overridable per-field."""
    base: dict[str, Any] = {
        "id": "NRDAX-T0001",
        "name": "slug-one",
        "display_name": "Display One",
        "mechanism": "An unauthenticated JSON-RPC call amplifies load on the validator.",
        "family": "response_amp",
        "status": "active",
        "first_seen": "2025-01-15",
        "instances": [],
        "external_references": [],
    }
    base.update(overrides)
    return base


def make_instance(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "chain": "solana",
        "primitive_id": "solana_response_amp_getblock",
        "bundle_ref": "corpus_v1.3/solana_response_amp_getblock/0001",
        "fidelity": "lab",
        "discovery_origin": "original-research",
        "external_references": [],
    }
    base.update(overrides)
    return base


@pytest.fixture
def fixture_registry() -> NRDAX:
    """The 3-technique golden feed (byte-identical to the backend's golden)."""
    return NRDAX.from_feed(str(FIXTURE_FEED))


@pytest.fixture
def bundled_registry() -> NRDAX:
    """The real dataset snapshot shipped with the package."""
    return NRDAX.bundled()


@pytest.fixture
def tmp_cache(tmp_path, monkeypatch) -> Path:
    """Redirect the cache to an isolated temp dir for the test."""
    cache = tmp_path / "cache"
    monkeypatch.setenv("NRDAX_CACHE_DIR", str(cache))
    return cache
