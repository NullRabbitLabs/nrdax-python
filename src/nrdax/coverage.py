"""Derive the coverage matrix from techniques + known coverage.

Mirrors the canonical backend's derivation (``views/coverage.rs``): reproduced
cells record the strongest fidelity per chain; known cells are the chains a
disclosure names minus any already reproduced; the chain axis is ordered
most-covered first (ties by name). Deterministic: never depends on iteration order.
"""

from __future__ import annotations

from collections import defaultdict

from .models import CoverageCell, CoverageMatrix, KnownCell, KnownCoverage, Technique
from .vocab import fidelity_strength


def coverage_matrix(
    techniques: list[Technique], known_coverage: list[KnownCoverage]
) -> CoverageMatrix:
    known_by_id: dict[str, tuple[str, ...]] = {kc.technique_id: kc.chains for kc in known_coverage}
    chain_count: dict[str, int] = defaultdict(int)
    cells: list[CoverageCell] = []
    known: list[KnownCell] = []

    for tech in techniques:
        by_chain: dict[str, list] = defaultdict(list)
        for inst in tech.instances:
            by_chain[inst.chain].append(inst)
        for chain in sorted(by_chain):
            insts = by_chain[chain]
            chain_count[chain] += 1
            strongest = max(insts, key=lambda i: fidelity_strength(i.fidelity))
            cells.append(
                CoverageCell(
                    technique_id=tech.id,
                    chain=chain,
                    strongest_fidelity=strongest.fidelity,
                    instance_count=len(insts),
                )
            )

        reproduced = {inst.chain for inst in tech.instances}
        for chain in known_by_id.get(tech.id, ()):
            if chain in reproduced:
                continue
            chain_count[chain] += 1
            known.append(KnownCell(technique_id=tech.id, chain=chain))

    # Axis: most-covered first, ties by name.
    chains = tuple(c for c, _ in sorted(chain_count.items(), key=lambda kv: (-kv[1], kv[0])))
    cells.sort(key=lambda c: (c.technique_id, c.chain))
    known.sort(key=lambda k: (k.technique_id, k.chain))
    return CoverageMatrix(chains=chains, cells=tuple(cells), known=tuple(known))
