"""Local snapshot cache for offline and pinned use.

``nrdax update`` writes the fetched dataset here; subsequent commands load it so
work continues offline. Nothing is hidden: :func:`info` reports the cached version
and fetch time so stale data is always visible, and ``nrdax cache clear`` removes
it. Location precedence: ``$NRDAX_CACHE_DIR`` → ``$XDG_CACHE_HOME/nrdax`` →
``~/.cache/nrdax`` (``%LOCALAPPDATA%\\nrdax`` on Windows).
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from .sources import RawDataset, SourceMeta

_META = "meta.json"
_JSONL = "registry.jsonl"
_KNOWN = "known_coverage.json"
_FAMILIES = "families.json"


def cache_dir() -> Path:
    override = os.environ.get("NRDAX_CACHE_DIR")
    if override:
        return Path(override)
    if os.name == "nt":  # pragma: no cover - platform dependent
        win_base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(win_base) / "nrdax"
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "nrdax"


def snapshot_dir() -> Path:
    return cache_dir() / "snapshot"


def has_snapshot() -> bool:
    d = snapshot_dir()
    return (d / _META).is_file() and (d / _JSONL).is_file()


def write_snapshot(raw: RawDataset) -> Path:
    """Persist ``raw`` to the cache and return the snapshot directory."""
    d = snapshot_dir()
    d.mkdir(parents=True, exist_ok=True)

    with (d / _JSONL).open("w", encoding="utf-8") as fh:
        for tech in raw.techniques:
            fh.write(json.dumps(tech, separators=(",", ":"), ensure_ascii=False))
            fh.write("\n")

    (d / _KNOWN).write_text(json.dumps(raw.known_coverage, ensure_ascii=False), encoding="utf-8")
    if raw.families is not None:
        (d / _FAMILIES).write_text(
            json.dumps({"families": raw.families}, ensure_ascii=False), encoding="utf-8"
        )

    src = raw.meta
    meta = {
        "version": raw.version,
        "doi": raw.doi,
        "technique_count": len(raw.techniques),
        "fetched_at": src.fetched_at if src else None,
        "source_kind": src.kind if src else "unknown",
        "source_location": src.location if src else "unknown",
    }
    (d / _META).write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return d


def read_snapshot() -> RawDataset:
    """Load the cached snapshot into a :class:`RawDataset`."""
    from .sources.feed import read_jsonl  # local import avoids a cycle at import time

    d = snapshot_dir()
    meta = json.loads((d / _META).read_text(encoding="utf-8"))
    techniques = read_jsonl((d / _JSONL).read_text(encoding="utf-8"))
    known = []
    if (d / _KNOWN).is_file():
        known = json.loads((d / _KNOWN).read_text(encoding="utf-8"))
    families = None
    if (d / _FAMILIES).is_file():
        families = json.loads((d / _FAMILIES).read_text(encoding="utf-8")).get("families")

    location = f"{meta.get('source_kind', '?')}:{meta.get('source_location', '?')}"
    return RawDataset(
        version=meta.get("version", "cache"),
        doi=meta.get("doi"),
        techniques=techniques,
        known_coverage=known,
        families=families,
        meta=SourceMeta(kind="cache", location=location, fetched_at=meta.get("fetched_at")),
    )


def clear() -> bool:
    """Remove the cache directory. Returns ``True`` if anything was removed."""
    d = cache_dir()
    if d.exists():
        shutil.rmtree(d)
        return True
    return False


def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def info() -> dict[str, Any]:
    """A summary of cache state for ``nrdax cache info`` / ``nrdax info``."""
    d = snapshot_dir()
    present = has_snapshot()
    out: dict[str, Any] = {
        "cache_dir": str(cache_dir()),
        "snapshot_present": present,
    }
    if present:
        meta = json.loads((d / _META).read_text(encoding="utf-8"))
        out.update(
            {
                "version": meta.get("version"),
                "doi": meta.get("doi"),
                "technique_count": meta.get("technique_count"),
                "fetched_at": meta.get("fetched_at"),
                "source": f"{meta.get('source_kind')}:{meta.get('source_location')}",
                "size_bytes": _dir_size(d),
            }
        )
    return out


class CacheSource:
    """Load the cached snapshot as a source (used as the default when present)."""

    def load(self) -> RawDataset:
        return read_snapshot()
