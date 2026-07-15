"""The live-API source targets the versioned surface (``/v1``)."""

from __future__ import annotations

from typing import Any

from nrdax.sources import _http
from nrdax.sources.api import ApiSource
from nrdax.vocab import NRDAX_API


def test_default_base_is_the_versioned_surface():
    assert NRDAX_API == "https://api.nrdax.com/v1"


def test_load_requests_v1_paths(monkeypatch):
    seen: list[str] = []

    def fake_get_json(url: str, *, timeout: float) -> Any:
        seen.append(url)
        if "/techniques" in url:
            return {"techniques": [], "total": 0, "registry_version": "v0.2"}
        if "/coverage" in url:
            return {"known": []}
        if "/families" in url:
            return {"families": []}
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(_http, "get_json", fake_get_json)
    ApiSource().load()

    assert seen[0].startswith("https://api.nrdax.com/v1/techniques")
    assert all(u.startswith("https://api.nrdax.com/v1/") for u in seen)
