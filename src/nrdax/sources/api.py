"""Live read-API source (``https://api.nrdax.com``).

Paginates ``/techniques`` for the records, then pulls ``/families`` for the
vocabulary and ``/coverage`` for known coverage. This is the only *live* canonical
remote today (the static feed is not yet published at a stable public URL), so it
is what ``nrdax update`` fetches from by default. Every domain operation works
identically whichever source produced the data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..errors import DataFormatError
from ..vocab import NRDAX_API
from . import RawDataset, SourceMeta, _http

_PAGE = 200


class ApiSource:
    """Load NRDAX data from the live read API."""

    def __init__(self, base_url: str = NRDAX_API, *, page_size: int = _PAGE, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.page_size = page_size
        self.timeout = timeout

    def _get(self, path: str) -> Any:
        return _http.get_json(f"{self.base_url}{path}", timeout=self.timeout)

    def load(self) -> RawDataset:
        techniques: list[dict[str, Any]] = []
        version = "unknown"
        doi: str | None = None
        offset = 0
        while True:
            doc = self._get(f"/techniques?limit={self.page_size}&offset={offset}")
            if not isinstance(doc, dict) or not isinstance(doc.get("techniques"), list):
                raise DataFormatError("/techniques did not return a TechniquesResponse")
            if isinstance(doc.get("registry_version"), str):
                version = doc["registry_version"]
            if isinstance(doc.get("doi"), str):
                doi = doc["doi"]
            page = [t for t in doc["techniques"] if isinstance(t, dict)]
            techniques.extend(page)
            total = doc.get("total")
            offset += len(page)
            if not page or (isinstance(total, int) and offset >= total):
                break

        known = self._known_coverage()
        families = self._families()

        return RawDataset(
            version=version,
            doi=doi,
            techniques=techniques,
            known_coverage=known,
            families=families,
            meta=SourceMeta(
                kind="api",
                location=self.base_url,
                fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )

    def _known_coverage(self) -> list[dict[str, Any]]:
        try:
            cov = self._get("/coverage")
        except Exception:
            return []
        if not isinstance(cov, dict):
            return []
        by_tech: dict[str, list[str]] = {}
        # The feed exposes 'known'; tolerate its absence (some deployments emit 'gaps').
        for cell in cov.get("known", []) or []:
            if isinstance(cell, dict):
                tid, chain = cell.get("technique_id"), cell.get("chain")
                if isinstance(tid, str) and isinstance(chain, str):
                    by_tech.setdefault(tid, []).append(chain)
        return [{"technique_id": t, "chains": c} for t, c in sorted(by_tech.items())]

    def _families(self) -> list[str] | None:
        try:
            doc = self._get("/families")
        except Exception:
            return None
        if isinstance(doc, dict) and isinstance(doc.get("families"), list):
            return [
                f["name"]
                for f in doc["families"]
                if isinstance(f, dict) and isinstance(f.get("name"), str)
            ]
        return None
