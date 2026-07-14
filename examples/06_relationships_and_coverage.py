"""Traverse derived relationships and read the coverage matrix.

Run:  python examples/06_relationships_and_coverage.py
"""

from __future__ import annotations

from nrdax import NRDAX


def main() -> None:
    registry = NRDAX.from_api()

    rel = registry.related("NRDAX-T0006")
    print(f"Relationships for {rel.technique_id} (all DERIVED from canonical fields):")
    print(f"  family {rel.family}: {len(rel.family_siblings)} siblings")
    for cn in rel.chains:
        print(f"  shares chain {cn.chain} with {len(cn.technique_ids)} technique(s)")
    for sr in rel.shared_references:
        print(f"  shares reference {sr.reference} with {sr.technique_ids}")
    print(f"  advisories: {len(rel.advisories)}, instances: {len(rel.instances)}")

    cov = registry.coverage
    print(f"\nCoverage matrix: {len(cov.chains)} chains, "
          f"{len(cov.cells)} reproduced cells, {len(cov.known)} known cells")
    print("Most-covered chains:", ", ".join(cov.chains[:8]))


if __name__ == "__main__":
    main()
