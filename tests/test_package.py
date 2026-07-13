"""Packaging / import sanity + backward-compatibility with the shipped snapshot."""

from __future__ import annotations

from importlib import resources

import nrdax


def test_version_exposed():
    assert isinstance(nrdax.__version__, str)
    assert nrdax.__version__.count(".") >= 2


def test_public_api_importable():
    for name in nrdax.__all__:
        assert hasattr(nrdax, name), name


def test_py_typed_ships():
    assert (resources.files("nrdax") / "py.typed").is_file()


def test_bundled_snapshot_ships_and_loads():
    reg = nrdax.NRDAX.load()
    assert len(reg) == 381
    assert reg.version == "v0.1-import"
    # Fixture backward-compat: a known technique from the prompt examples resolves.
    assert reg.get("NRDAX-T0006").family == "compute_amp"


def test_quickstart_snippet_from_readme():
    registry = nrdax.NRDAX.load()
    technique = registry.get("NRDAX-T0006")
    results = registry.search("rpc exhaustion")
    related = registry.related("NRDAX-T0006")
    assert technique.id == "NRDAX-T0006"
    assert isinstance(results, list)
    assert related.family == "compute_amp"
