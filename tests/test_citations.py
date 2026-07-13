from __future__ import annotations

import json

import pytest

from nrdax import NRDAX
from nrdax.citations import cite
from nrdax.errors import InvalidArgumentError
from tests.conftest import make_technique


def _reg(doi=None):
    return NRDAX.from_memory(
        [
            make_technique(
                id="NRDAX-T0006",
                display_name="Async Runtime Blocking VM Execution",
                first_seen="2026-07-09",
            )
        ],
        version="v0.1-import",
        doi=doi,
    )


def test_text_citation():
    out = cite(_reg(), "NRDAX-T0006", accessed="2026-07-13")
    assert "Async Runtime Blocking VM Execution" in out
    assert "NRDAX-T0006" in out
    assert "https://nrdax.com/techniques/NRDAX-T0006" in out
    assert "v0.1-import" in out


def test_no_doi_is_not_fabricated():
    for style in ("text", "markdown", "bibtex"):
        out = cite(_reg(doi=None), "NRDAX-T0006", style=style, accessed="2026-07-13")
        assert "doi" not in out.lower()


def test_doi_included_when_present():
    out = cite(_reg(doi="10.5281/zenodo.1"), "NRDAX-T0006", style="text", accessed="2026-07-13")
    assert "10.5281/zenodo.1" in out


def test_bibtex_shape():
    out = cite(_reg(), "NRDAX-T0006", style="bibtex", accessed="2026-07-13")
    assert out.startswith("@online{NRDAX-T0006,")
    assert "author       = {NullRabbit Labs}" in out
    assert out.rstrip().endswith("}")


def test_csl_json_is_valid_json():
    out = cite(_reg(doi="10.5281/zenodo.1"), "NRDAX-T0006", style="json", accessed="2026-07-13")
    doc = json.loads(out)
    assert doc["id"] == "NRDAX-T0006"
    assert doc["type"] == "dataset"
    assert doc["DOI"] == "10.5281/zenodo.1"
    assert doc["issued"] == {"date-parts": [[2026, 7, 9]]}


def test_no_em_dashes_in_output():
    for style in ("text", "markdown", "bibtex", "json"):
        out = cite(_reg(), "NRDAX-T0006", style=style, accessed="2026-07-13")
        assert "—" not in out and "–" not in out


def test_unknown_style_raises():
    with pytest.raises(InvalidArgumentError):
        cite(_reg(), "NRDAX-T0006", style="chicago")
