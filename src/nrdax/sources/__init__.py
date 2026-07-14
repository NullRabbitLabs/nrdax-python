"""Data-source adapters.

Domain operations are independent of *where* the dataset came from. A source's
only job is to produce a :class:`RawDataset` — the version, optional DOI, the raw
technique dicts, the known-coverage dicts, and the family vocabulary — which the
:class:`~nrdax.registry.NRDAX` facade parses and indexes.

Supported sources: :class:`~nrdax.sources.api.ApiSource` (the live read API),
:class:`~nrdax.sources.feed.FeedSource` (a static-feed directory or base URL),
:class:`~nrdax.sources.file.FileSource` (a local ``registry.jsonl`` / bundle),
:class:`~nrdax.sources.stix.StixSource` (a STIX 2.1 bundle),
:class:`~nrdax.sources.memory.MemorySource` (in-memory, for tests), and the local
cache written by ``nrdax update`` (:class:`~nrdax.cache.CacheSource`). No dataset is
bundled in the package; ``nrdax update`` fetches one for offline/pinned use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class SourceMeta:
    """Provenance of a loaded dataset — surfaced by ``nrdax info``."""

    kind: str  # "cache" | "feed" | "api" | "file" | "stix" | "memory"
    location: str  # path, URL, or "<memory>"
    fetched_at: str | None = None  # ISO-8601 if fetched over the network


@dataclass
class RawDataset:
    """The raw, unparsed dataset a source yields."""

    version: str
    doi: str | None
    techniques: list[dict[str, Any]]
    known_coverage: list[dict[str, Any]] = field(default_factory=list)
    families: list[str] | None = None  # authoritative vocab (names), if the source has one
    meta: SourceMeta | None = None


@runtime_checkable
class Source(Protocol):
    """Anything that can produce a :class:`RawDataset`."""

    def load(self) -> RawDataset: ...


__all__ = ["RawDataset", "Source", "SourceMeta"]
