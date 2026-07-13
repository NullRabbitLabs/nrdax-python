"""Static-feed source: a directory or base URL laid out like ``nrdax-emit`` output.

The static feed is the **canonical dataset format** — the version-pinnable,
offline snapshot the whole package is designed around. A feed is the set of files:

* ``index.json``          — ``version``, ``doi``, and the ordered technique ids;
* ``registry.jsonl``      — one technique object per line (the records);
* ``coverage-matrix.json``— derived coverage (used to recover known coverage);
* ``families.json``       — the family vocabulary with counts (optional).

``FeedSource`` reads a local directory or an ``http(s)`` base URL identically.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from ..errors import DataFormatError, SourceError
from . import RawDataset, SourceMeta, _http


def read_jsonl(text: str) -> list[dict[str, Any]]:
    """Parse a ``registry.jsonl`` body into technique dicts (one per non-blank line)."""
    records: list[dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DataFormatError(f"registry.jsonl line {lineno}: invalid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise DataFormatError(f"registry.jsonl line {lineno}: expected an object")
        records.append(obj)
    return records


def known_coverage_from_matrix(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    """Recover per-technique known coverage from a ``coverage-matrix.json`` body.

    The feed emits derived ``known`` cells (technique×chain), already excluding
    reproduced chains. Grouping them back by technique reconstructs the
    known-coverage the registry's own derivation consumes, so re-deriving the
    matrix reproduces the feed exactly.
    """
    by_tech: dict[str, list[str]] = {}
    for cell in matrix.get("known", []) or []:
        if not isinstance(cell, dict):
            continue
        tid = cell.get("technique_id")
        chain = cell.get("chain")
        if isinstance(tid, str) and isinstance(chain, str):
            by_tech.setdefault(tid, []).append(chain)
    return [{"technique_id": tid, "chains": chains} for tid, chains in sorted(by_tech.items())]


class _Reader:
    """Reads named feed files from a local dir or an http(s) base URL."""

    def __init__(self, location: str):
        self.is_url = location.startswith(("http://", "https://"))
        self.location = location.rstrip("/") if self.is_url else location

    def _path(self, name: str) -> str:
        return f"{self.location}/{name}" if self.is_url else os.path.join(self.location, name)

    def text(self, name: str) -> str:
        if self.is_url:
            return _http.get_text(self._path(name))
        try:
            with open(self._path(name), encoding="utf-8") as fh:
                return fh.read()
        except FileNotFoundError as exc:
            raise SourceError(f"feed file not found: {self._path(name)}") from exc

    def json(self, name: str) -> Any:
        raw = self.text(name)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DataFormatError(f"{name}: invalid JSON: {exc}") from exc

    def optional_json(self, name: str) -> Any | None:
        try:
            return self.json(name)
        except SourceError:
            return None


def load_feed(location: str, *, meta_kind: str = "feed") -> RawDataset:
    """Load a :class:`RawDataset` from a feed directory or base URL."""
    reader = _Reader(location)
    index = reader.json("index.json")
    if not isinstance(index, dict):
        raise DataFormatError("index.json must be a JSON object")
    version = index.get("version")
    if not isinstance(version, str) or not version:
        raise DataFormatError("index.json is missing a string 'version'")

    techniques = read_jsonl(reader.text("registry.jsonl"))

    matrix = reader.optional_json("coverage-matrix.json")
    known = known_coverage_from_matrix(matrix) if isinstance(matrix, dict) else []

    families_doc = reader.optional_json("families.json")
    families: list[str] | None = None
    if isinstance(families_doc, dict) and isinstance(families_doc.get("families"), list):
        families = [
            f["name"]
            for f in families_doc["families"]
            if isinstance(f, dict) and isinstance(f.get("name"), str)
        ]

    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds") if reader.is_url else None
    return RawDataset(
        version=version,
        doi=index.get("doi") if isinstance(index.get("doi"), str) else None,
        techniques=techniques,
        known_coverage=known,
        families=families,
        meta=SourceMeta(kind=meta_kind, location=location, fetched_at=fetched_at),
    )


class FeedSource:
    """Load NRDAX data from a static-feed directory or base URL."""

    def __init__(self, location: str):
        self.location = location

    def load(self) -> RawDataset:
        return load_feed(self.location)
