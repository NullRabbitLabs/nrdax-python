"""Export STIX 2.1, validate it, and show that identity round-trips.

Run:  python examples/05_stix_export.py
"""

from __future__ import annotations

from nrdax import NRDAX
from nrdax.exporters import stix_bundle, technique_ids, validate_bundle


def main() -> None:
    registry = NRDAX.load()
    subset = registry.filter(chain="solana")

    bundle = stix_bundle(subset, registry.version)
    print(f"Bundle {bundle['id']} with {len(bundle['objects'])} attack-pattern(s)")

    errors = validate_bundle(bundle)
    print(f"STIX 2.1 validation: {'valid' if not errors else errors}")

    ids = technique_ids(bundle)
    print(f"Identity round-trips: {len(ids)} NRDAX ids anchored in the bundle")

    # Re-import the bundle (lossy: identity + coarse fields only).
    reimported = NRDAX.from_stix(bundle=bundle)
    print(f"Re-imported {len(reimported)} techniques from the STIX bundle")
    sample = next(iter(reimported))
    print(f"  {sample.id}: {sample.display} (chains preserved: {sample.extra.get('x_nrdax_chains')})")


if __name__ == "__main__":
    main()
