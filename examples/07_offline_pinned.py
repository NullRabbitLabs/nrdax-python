"""Pin an exact dataset for reproducible research, and diff two snapshots.

Run:  python examples/07_offline_pinned.py
Demonstrates loading from a feed directory and diffing two datasets, using the
test fixture feed shipped in the repo (no network).
"""

from __future__ import annotations

from pathlib import Path

from nrdax import NRDAX
from nrdax.changes import diff, since

# The repo ships a tiny 3-technique feed fixture; a real pin points at a saved feed.
FIXTURE_FEED = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "feed"


def main() -> None:
    pinned = NRDAX.from_feed(str(FIXTURE_FEED))
    print(f"Pinned dataset version: {pinned.version} ({len(pinned)} techniques)")

    recent = since(pinned, "2025-02-01")
    print(f"Techniques first seen since 2025-02-01: {[t.id for t in recent]}")

    # Diff the pinned snapshot against a hypothetical newer one. We synthesise the
    # "newer" side in memory (dropping one technique) so the example needs no network;
    # in practice the other side is a fresh `NRDAX.from_api()` or another saved feed.
    newer = NRDAX.from_memory([t.to_dict() for t in list(pinned)[1:]], version="newer")
    changes = diff(pinned, newer)
    print(f"\nDiff {changes.from_version} -> {changes.to_version}: {len(changes)} changes")
    for kind, count in changes.counts_by_kind().items():
        print(f"  {kind}: {count}")


if __name__ == "__main__":
    main()
