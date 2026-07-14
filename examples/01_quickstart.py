"""Quick start: load the live registry and retrieve a technique.

Run:  python examples/01_quickstart.py
Everything here works offline against the snapshot shipped with the package.
"""

from __future__ import annotations

from nrdax import NRDAX


def main() -> None:
    registry = NRDAX.from_api()
    print(f"Loaded NRDAX {registry.version} with {len(registry)} techniques")
    print(f"  reproduced: {sum(1 for t in registry if t.is_reproduced)}")
    print(f"  known-only: {sum(1 for t in registry if not t.is_reproduced)}")

    technique = registry.get("NRDAX-T0006")
    print(f"\n{technique.id}: {technique.display}")
    print(f"  family:       {technique.family}")
    print(f"  status:       {technique.status} ({technique.reproduction_status})")
    print(f"  first seen:   {technique.first_seen}")
    print(f"  chains:       {', '.join(technique.chains)}")
    print(f"  url:          {technique.url}")
    print(f"  mechanism:    {technique.mechanism[:120]}...")


if __name__ == "__main__":
    main()
