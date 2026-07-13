from __future__ import annotations

import json

import pytest

from nrdax.cli.main import main
from nrdax.errors import ExitCode
from tests.conftest import FIXTURE_FEED

FEED = str(FIXTURE_FEED)


def run(capsys, *argv):
    code = main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_version(capsys):
    code, out, _ = run(capsys, "version")
    assert code == ExitCode.OK
    assert "nrdax" in out


def test_version_json(capsys):
    code, out, _ = run(capsys, "version", "--format", "json")
    doc = json.loads(out)
    assert doc["cli_version"] and doc["schema_version"]


def test_get_table(capsys):
    code, out, _ = run(capsys, "get", "NRDAX-T0001", "--source", FEED)
    assert code == ExitCode.OK
    assert "NRDAX-T0001" in out
    assert "response_amp" in out


def test_get_json(capsys):
    code, out, _ = run(capsys, "get", "NRDAX-T0001", "--source", FEED, "--format", "json")
    doc = json.loads(out)
    assert doc["id"] == "NRDAX-T0001"
    assert "reproduction_status" in doc


def test_get_stix(capsys):
    code, out, _ = run(capsys, "get", "NRDAX-T0001", "--source", FEED, "--format", "stix")
    doc = json.loads(out)
    assert doc["type"] == "bundle"


def test_get_unknown_exit_3(capsys):
    code, out, err = run(capsys, "get", "NRDAX-T9999", "--source", FEED)
    assert code == ExitCode.NOT_FOUND
    assert "no such technique" in err


def test_get_unknown_json_error_body(capsys):
    code, out, _ = run(capsys, "get", "NRDAX-T9999", "--source", FEED, "--format", "json")
    doc = json.loads(out)
    assert doc["error"]["code"] == "not_found"
    assert code == ExitCode.NOT_FOUND


def test_search(capsys):
    code, out, _ = run(capsys, "search", "amplification", "--source", FEED)
    assert code == ExitCode.OK
    assert "NRDAX-T0001" in out


def test_search_json(capsys):
    code, out, _ = run(capsys, "search", "amplification", "--source", FEED, "--format", "json")
    doc = json.loads(out)
    assert doc["query"] == "amplification"
    assert doc["count"] >= 1


def test_list_filter(capsys):
    code, out, _ = run(capsys, "list", "--chain", "solana", "--source", FEED)
    assert code == ExitCode.OK
    assert "NRDAX-T0001" in out


def test_list_json(capsys):
    code, out, _ = run(
        capsys, "list", "--family", "response_amp", "--source", FEED, "--format", "json"
    )
    doc = json.loads(out)
    assert doc["count"] == 1


def test_related(capsys):
    code, out, _ = run(capsys, "related", "NRDAX-T0001", "--source", FEED)
    assert code == ExitCode.OK
    assert "DERIVED" in out


def test_export_json_to_file(capsys, tmp_path):
    out_file = tmp_path / "out.json"
    code, _, err = run(
        capsys, "export", "--source", FEED, "--format", "json", "--output", str(out_file)
    )
    assert code == ExitCode.OK
    doc = json.loads(out_file.read_text())
    assert doc["count"] == 3


def test_export_bad_format_exit_2(capsys):
    with pytest.raises(SystemExit) as exc:  # argparse choices -> SystemExit(2)
        main(["export", "--source", FEED, "--format", "xml"])
    assert exc.value.code == 2


def test_cite_bibtex(capsys):
    code, out, _ = run(capsys, "cite", "NRDAX-T0001", "--source", FEED, "--format", "bibtex")
    assert code == ExitCode.OK
    assert out.startswith("@online{NRDAX-T0001")


def test_changes_since(capsys):
    code, out, err = run(capsys, "changes", "--source", FEED, "--since", "2025-02-01")
    assert code == ExitCode.OK
    assert "NRDAX-T0002" in out


def test_changes_from_version_unsupported_exit_4(capsys):
    code, out, err = run(capsys, "changes", "--from-version", "1.0", "--to-version", "2.0")
    assert code == ExitCode.INVALID_ARG
    assert "not available" in err


def test_changes_between_sources(capsys):
    code, out, _ = run(capsys, "changes", "--from", "bundled", "--to", FEED, "--format", "json")
    doc = json.loads(out)
    assert "counts_by_kind" in doc


def test_schema_json(capsys):
    code, out, _ = run(capsys, "schema", "--format", "json")
    doc = json.loads(out)
    assert doc["schema_version"]
    assert "families" in doc["vocabularies"]


def test_info(capsys):
    code, out, _ = run(capsys, "info", "--source", FEED, "--format", "json")
    doc = json.loads(out)
    assert doc["dataset_version"] == "v1.0"
    assert doc["technique_count"] == 3


def test_update_cache_lifecycle(capsys, tmp_cache):
    code, out, _ = run(capsys, "update", "--source", f"feed:{FEED}")
    assert code == ExitCode.OK
    assert "updated cache" in out

    code, out, _ = run(capsys, "cache", "info", "--format", "json")
    doc = json.loads(out)
    assert doc["snapshot_present"] is True
    assert doc["version"] == "v1.0"

    code, out, _ = run(capsys, "cache", "clear")
    assert "cleared" in out


def test_update_version_mismatch_exit_4(capsys, tmp_cache):
    code, out, err = run(capsys, "update", "--source", f"feed:{FEED}", "--version", "v9.9")
    assert code == ExitCode.INVALID_ARG
    assert "requested version" in err
