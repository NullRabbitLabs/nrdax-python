"""Single local-file source.

Accepts any of:

* ``*.jsonl`` — a ``registry.jsonl`` (one technique per line);
* a JSON array of technique objects;
* a JSON object with a ``techniques`` array (optionally ``version``, ``doi``,
  ``known_coverage``) — i.e. a release/bundle;
* a JSON object that is itself a single technique (has an ``id``).

Version defaults to ``"local"`` when the file does not declare one.
"""

from __future__ import annotations

import json
import os

from ..errors import DataFormatError, SourceError
from . import RawDataset, SourceMeta
from .feed import read_jsonl


class FileSource:
    """Load NRDAX data from a single local file."""

    def __init__(self, path: str):
        self.path = path

    def load(self) -> RawDataset:
        try:
            with open(self.path, encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError as exc:
            raise SourceError(f"file not found: {self.path}") from exc

        meta = SourceMeta(kind="file", location=self.path)

        if self.path.endswith(".jsonl"):
            return RawDataset("local", None, read_jsonl(text), meta=meta)

        try:
            doc = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DataFormatError(f"{self.path}: invalid JSON: {exc}") from exc

        if isinstance(doc, list):
            return RawDataset("local", None, [d for d in doc if isinstance(d, dict)], meta=meta)

        if isinstance(doc, dict):
            if isinstance(doc.get("techniques"), list):
                return RawDataset(
                    version=doc.get("version", "local")
                    if isinstance(doc.get("version"), str)
                    else "local",
                    doi=doc.get("doi") if isinstance(doc.get("doi"), str) else None,
                    techniques=[t for t in doc["techniques"] if isinstance(t, dict)],
                    known_coverage=[
                        k for k in doc.get("known_coverage", []) if isinstance(k, dict)
                    ],
                    families=None,
                    meta=meta,
                )
            if "id" in doc:  # a bare single technique
                return RawDataset("local", None, [doc], meta=meta)

        raise DataFormatError(
            f"{self.path}: unrecognised shape (expected jsonl, a technique array, "
            "a {{techniques: [...]}} object, or a single technique)"
        )


def source_for_path(path: str) -> FileSource:
    """Convenience: build a :class:`FileSource`, checking the path exists."""
    if not os.path.exists(path):
        raise SourceError(f"file not found: {path}")
    return FileSource(path)
