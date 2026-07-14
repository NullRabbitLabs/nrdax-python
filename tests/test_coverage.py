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


def test_bundled_coverage_is_well_formed(bundled_registry):
    # Structural (refresh-proof) checks on the real dataset: the matrix is non-empty
    # and every cell references a real technique and an axis chain.
    cov = bundled_registry.coverage
    assert cov.chains and cov.cells and cov.known
    ids = {t.id for t in bundled_registry}
    axis = set(cov.chains)
    for cell in cov.cells:
        assert cell.technique_id in ids
        assert cell.chain in axis
        assert cell.instance_count >= 1
    for known in cov.known:
        assert known.technique_id in ids
        assert known.chain in axis
