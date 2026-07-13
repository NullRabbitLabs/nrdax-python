"""In-memory source (for tests and programmatic construction).

Accepts raw technique dicts or already-built :class:`~nrdax.models.Technique`
objects; the latter are serialised back to dicts so the normal parse/validate path
still runs.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..models import Technique
from . import RawDataset, SourceMeta


class MemorySource:
    """Load NRDAX data from an in-memory collection."""

    def __init__(
        self,
        techniques: Iterable[dict[str, Any] | Technique],
        *,
        version: str = "memory",
        doi: str | None = None,
        known_coverage: list[dict[str, Any]] | None = None,
        families: list[str] | None = None,
    ):
        self._techniques = [t.to_dict() if isinstance(t, Technique) else t for t in techniques]
        self._version = version
        self._doi = doi
        self._known = known_coverage or []
        self._families = families

    def load(self) -> RawDataset:
        return RawDataset(
            version=self._version,
            doi=self._doi,
            techniques=self._techniques,
            known_coverage=self._known,
            families=self._families,
            meta=SourceMeta(kind="memory", location="<memory>"),
        )
