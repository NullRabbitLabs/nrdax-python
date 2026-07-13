from __future__ import annotations

from nrdax import NRDAX, cache
from nrdax.registry import default_source
from nrdax.sources.bundled import BundledSource
from nrdax.sources.memory import MemorySource
from tests.conftest import make_technique


def test_write_read_round_trip(tmp_cache):
    raw = MemorySource(
        [make_technique(id="NRDAX-T0001")],
        version="v-cache",
        doi="10.5281/zenodo.2",
        known_coverage=[{"technique_id": "NRDAX-T0001", "chains": ["bitcoin"]}],
    ).load()
    cache.write_snapshot(raw)
    assert cache.has_snapshot()

    reg = NRDAX.from_cache()
    assert reg.version == "v-cache"
    assert reg.doi == "10.5281/zenodo.2"
    assert reg.get("NRDAX-T0001")
    assert reg.source_meta.kind == "cache"


def test_info_reports_presence(tmp_cache):
    assert cache.info()["snapshot_present"] is False
    cache.write_snapshot(BundledSource().load())
    info = cache.info()
    assert info["snapshot_present"] is True
    assert info["technique_count"] == 381


def test_clear(tmp_cache):
    cache.write_snapshot(BundledSource().load())
    assert cache.clear() is True
    assert cache.has_snapshot() is False
    assert cache.clear() is False  # already gone


def test_default_source_prefers_cache_when_present(tmp_cache):
    assert isinstance(default_source(), BundledSource)  # no snapshot yet
    cache.write_snapshot(MemorySource([make_technique()], version="cached").load())
    from nrdax.cache import CacheSource

    assert isinstance(default_source(), CacheSource)


def test_offline_reload_after_update(tmp_cache):
    # Simulate `nrdax update` then loading with no network available.
    cache.write_snapshot(MemorySource([make_technique(id="NRDAX-T0001")], version="pinned").load())
    reg = NRDAX.load()  # default source resolves to the cache
    assert reg.version == "pinned"
