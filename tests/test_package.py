"""Packaging / import sanity. The wheel ships code only — no dataset is bundled."""

from __future__ import annotations

from importlib import resources

import pytest

import nrdax


def test_version_exposed():
    assert isinstance(nrdax.__version__, str)
    assert nrdax.__version__.count(".") >= 2


def test_public_api_importable():
    for name in nrdax.__all__:
        assert hasattr(nrdax, name), name


def test_py_typed_ships():
    assert (resources.files("nrdax") / "py.typed").is_file()


def test_no_dataset_is_bundled():
    # The dataset is versioned and distributed separately; the wheel ships no data.
    assert not (resources.files("nrdax") / "data").is_dir()


def test_load_without_cache_errors(tmp_cache):
    # With no bundled data and an empty cache there is nothing to load offline.
    with pytest.raises(nrdax.SourceError):
        nrdax.NRDAX.load()


def test_quickstart_snippet(fixture_registry):
    # Mirrors the README quick start against an explicit source.
    registry = fixture_registry
    technique = registry.get("NRDAX-T0001")
    results = registry.search("amplification")
    related = registry.related("NRDAX-T0001")
    assert technique.id == "NRDAX-T0001"
    assert isinstance(results, list)
    assert related is not None
