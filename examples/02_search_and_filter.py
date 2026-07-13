"""Search and compose filters.

Run:  python examples/02_search_and_filter.py
"""

from __future__ import annotations

from nrdax import NRDAX


def main() -> None:
    registry = NRDAX.load()

    print("Top 5 for 'rpc resource exhaustion':")
    for r in registry.search("rpc resource exhaustion", limit=5):
        t = r.technique
        print(f"  {r.score:6.1f}  {t.id}  {t.display}  (matched: {', '.join(r.matched_fields)})")

    print("\nReproduced compute_amp techniques on solana:")
    hits = registry.filter(
        family="compute_amp", chain="solana", reproduction_status="reproduced"
    )
    for t in hits:
        print(f"  {t.id}  {t.display}  [{', '.join(t.chains)}]")

    print("\nEverything carrying a given advisory reference:")
    for t in registry.filter(implementation="agave")[:5]:
        print(f"  {t.id}  {t.display}")


if __name__ == "__main__":
    main()
