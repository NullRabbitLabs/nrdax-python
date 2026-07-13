from __future__ import annotations

import csv
import io
import json

import pytest

from nrdax import NRDAX
from nrdax.errors import InvalidArgumentError
from nrdax.exporters import export, export_csv, export_json
from tests.conftest import make_instance, make_technique


def _reg():
    return NRDAX.from_memory(
        [
            make_technique(
                id="NRDAX-T0001",
                instances=[
                    make_instance(chain="solana"),
                    make_instance(chain="ethereum", primitive_id="p2"),
                ],
                external_references=[{"kind": "cve", "id": "CVE-2025-1"}],
            ),
            make_technique(id="NRDAX-T0002", family="connection_exhaustion", instances=[]),
        ],
        version="v9",
        doi="10.5281/zenodo.1",
    )


def test_json_preserves_provenance():
    doc = json.loads(export_json(list(_reg()), version="v9", doi="10.5281/zenodo.1"))
    assert doc["registry_version"] == "v9"
    assert doc["doi"] == "10.5281/zenodo.1"
    assert doc["count"] == 2
    assert doc["techniques"][0]["id"] == "NRDAX-T0001"


def test_json_field_projection():
    doc = json.loads(
        export_json(list(_reg()), version="v9", fields=["id", "reproduction_status", "chains"])
    )
    row = doc["techniques"][0]
    assert set(row) == {"id", "reproduction_status", "chains"}
    assert row["chains"] == ["ethereum", "solana"]


def test_json_unknown_field_errors():
    with pytest.raises(InvalidArgumentError):
        export_json(list(_reg()), version="v9", fields=["nope"])


def test_csv_technique_rows_flatten_lists():
    text = export_csv(list(_reg()), fields=["id", "chains", "instance_count"])
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0] == ["id", "chains", "instance_count"]
    assert rows[1] == ["NRDAX-T0001", "ethereum;solana", "2"]


def test_csv_instance_rows():
    text = export_csv(list(_reg()), rows="instances")
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0][0] == "technique_id"
    # T0001 has two instances, T0002 none -> 2 data rows
    assert len(rows) == 3


def test_csv_unknown_rows_mode():
    with pytest.raises(InvalidArgumentError):
        export_csv(list(_reg()), rows="galaxies")


def test_export_dispatch_and_unknown_format():
    assert export(list(_reg()), "json", version="v9").startswith("{")
    with pytest.raises(InvalidArgumentError):
        export(list(_reg()), "xml", version="v9")
