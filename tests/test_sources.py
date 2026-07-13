from __future__ import annotations

import json

import pytest

from nrdax import NRDAX
from nrdax.errors import DataFormatError, SourceError
from nrdax.sources.feed import known_coverage_from_matrix, read_jsonl
from nrdax.sources.file import FileSource
from nrdax.sources.stix import StixSource, parse_bundle
from tests.conftest import make_technique


def test_feed_source_loads_fixture(fixture_registry):
    assert fixture_registry.version == "v1.0"
    assert len(fixture_registry) == 3
    assert fixture_registry.doi == "10.5281/zenodo.9990001"


def test_read_jsonl_skips_blank_lines():
    text = '{"id":"NRDAX-T0001"}\n\n{"id":"NRDAX-T0002"}\n'
    assert len(read_jsonl(text)) == 2


def test_read_jsonl_rejects_non_object():
    with pytest.raises(DataFormatError):
        read_jsonl("[1,2,3]")


def test_known_coverage_reconstructed_from_matrix():
    matrix = {"known": [{"technique_id": "NRDAX-T0001", "chain": "bitcoin"}]}
    assert known_coverage_from_matrix(matrix) == [
        {"technique_id": "NRDAX-T0001", "chains": ["bitcoin"]}
    ]


def test_memory_source_accepts_dicts_and_models():
    reg = NRDAX.from_memory([make_technique(id="NRDAX-T0001")], version="mem")
    assert reg.version == "mem"
    assert reg.get("NRDAX-T0001")


def test_file_source_jsonl(tmp_path):
    p = tmp_path / "r.jsonl"
    p.write_text(json.dumps(make_technique()) + "\n")
    reg = NRDAX.from_file(str(p))
    assert len(reg) == 1


def test_file_source_bundle_object(tmp_path):
    p = tmp_path / "bundle.json"
    p.write_text(json.dumps({"version": "1.9", "techniques": [make_technique()]}))
    reg = NRDAX.from_file(str(p))
    assert reg.version == "1.9"


def test_file_source_single_technique(tmp_path):
    p = tmp_path / "one.json"
    p.write_text(json.dumps(make_technique()))
    reg = NRDAX.from_file(str(p))
    assert len(reg) == 1


def test_file_source_array(tmp_path):
    p = tmp_path / "arr.json"
    p.write_text(json.dumps([make_technique(id="NRDAX-T0001"), make_technique(id="NRDAX-T0002")]))
    reg = NRDAX.from_file(str(p))
    assert len(reg) == 2


def test_file_source_missing_raises():
    with pytest.raises(SourceError):
        FileSource("/no/such/file.jsonl").load()


def test_file_source_bad_shape(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"nope": 1}))
    with pytest.raises(DataFormatError):
        NRDAX.from_file(str(p))


def test_stix_source_round_trips_identity(fixture_registry):
    from nrdax.exporters import stix_bundle

    bundle = stix_bundle(list(fixture_registry), fixture_registry.version)
    reparsed = parse_bundle(bundle)
    ids = {t["id"] for t in reparsed}
    assert ids == {"NRDAX-T0001", "NRDAX-T0002", "NRDAX-T0003"}
    # STIX import is lossy: no instances recovered, but chains preserved in extra.
    reg = NRDAX.from_stix(bundle=bundle)
    t = reg.get("NRDAX-T0001")
    assert t.instances == []
    assert t.extra.get("x_nrdax_chains") == ["ethereum", "solana"]


def test_stix_source_non_bundle_raises():
    with pytest.raises(DataFormatError):
        StixSource(bundle={"type": "not-a-bundle"}).load()


def test_stix_source_requires_exactly_one_input():
    with pytest.raises(ValueError):
        StixSource()
