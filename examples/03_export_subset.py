"""Export a filtered subset as JSON and CSV (provenance preserved).

Run:  python examples/03_export_subset.py
Writes agave-subset.json and agave-subset.csv in the current directory.
"""

from __future__ import annotations

from nrdax import NRDAX
from nrdax.exporters import export_csv, export_json


def main() -> None:
    registry = NRDAX.load()
    subset = registry.filter(implementation="agave")
    print(f"Selected {len(subset)} techniques (implementation heuristic 'agave')")

    doc = export_json(
        subset,
        version=registry.version,
        doi=registry.doi,
        fields=["id", "name", "family", "reproduction_status", "chains"],
    )
    with open("agave-subset.json", "w", encoding="utf-8") as fh:
        fh.write(doc)

    csv_text = export_csv(subset, fields=["id", "display", "family", "chains", "first_seen"])
    with open("agave-subset.csv", "w", encoding="utf-8") as fh:
        fh.write(csv_text)

    print("Wrote agave-subset.json and agave-subset.csv")
    print("The JSON wrapper carries registry_version so the subset stays citable.")


if __name__ == "__main__":
    main()
