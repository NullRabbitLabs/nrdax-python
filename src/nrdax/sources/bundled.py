"""The snapshot shipped inside the package (the zero-config default).

``NRDAX.load()`` uses this: it works offline, needs no configuration, and pins a
known dataset version for reproducible research. Refresh to the live dataset with
``nrdax update`` (which writes a newer snapshot into the local cache). The bundled
snapshot's provenance is recorded in ``src/nrdax/data/snapshot/SNAPSHOT.md``.
"""

from __future__ import annotations

import json
from importlib import resources

from . import RawDataset, SourceMeta
from .feed import known_coverage_from_matrix, read_jsonl


def _read(name: str) -> str:
    root = resources.files("nrdax")
    return (root / "data" / "snapshot" / name).read_text(encoding="utf-8")


class BundledSource:
    """Load the dataset snapshot bundled with the installed package."""

    def load(self) -> RawDataset:
        index = json.loads(_read("index.json"))
        techniques = read_jsonl(_read("registry.jsonl"))
        try:
            matrix = json.loads(_read("coverage-matrix.json"))
            known = known_coverage_from_matrix(matrix)
        except FileNotFoundError:  # pragma: no cover - snapshot always ships it
            known = []
        try:
            families_doc = json.loads(_read("families.json"))
            families = [f["name"] for f in families_doc.get("families", [])]
        except FileNotFoundError:  # pragma: no cover
            families = None
        return RawDataset(
            version=index["version"],
            doi=index.get("doi"),
            techniques=techniques,
            known_coverage=known,
            families=families,
            meta=SourceMeta(kind="bundled", location="<bundled snapshot>"),
        )
