from __future__ import annotations

import json

from tests.conftest import FIXTURE_FEED


def test_derived_matrix_matches_golden(fixture_registry):
    golden = json.loads((FIXTURE_FEED / "coverage-matrix.json").read_text())
    derived = fixture_registry.coverage.to_dict()
    assert derived == golden


def test_chain_axis_ordered_most_covered_first(fixture_registry):
    # ethereum appears in two techniques, so it leads the axis.
    assert fixture_registry.coverage.chains[0] == "ethereum"


def test_cells_record_strongest_fidelity(fixture_registry):
    cells = {(c.technique_id, c.chain): c for c in fixture_registry.coverage.cells}
    cell = cells[("NRDAX-T0001", "solana")]
    assert cell.strongest_fidelity == "lab"
    assert cell.instance_count == 1


def test_bundled_coverage_matches_feed(bundled_registry):
    cov = bundled_registry.coverage
    assert len(cov.chains) == 64
    assert len(cov.cells) == 130
    assert len(cov.known) == 495
