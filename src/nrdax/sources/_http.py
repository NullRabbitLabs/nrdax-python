"""Minimal stdlib HTTP helpers (no third-party dependency).

Kept tiny on purpose: the CLI must start fast and install with zero required
dependencies. Network access is confined to :class:`~nrdax.sources.feed.FeedSource`
(URL mode) and :class:`~nrdax.sources.api.ApiSource`; nothing else in the package
touches the network.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .._version import __version__
from ..errors import DataFormatError, SourceError

USER_AGENT = f"nrdax-python/{__version__} (+https://github.com/NullRabbitLabs/nrdax-python)"
DEFAULT_TIMEOUT = 30.0


def _request(url: str, *, accept: str, timeout: float) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return body, headers
    except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
        raise SourceError(f"GET {url} failed: HTTP {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - network dependent
        raise SourceError(f"GET {url} failed: {exc.reason}") from exc
    except TimeoutError as exc:  # pragma: no cover - network dependent
        raise SourceError(f"GET {url} timed out after {timeout}s") from exc


def get_bytes(url: str, *, accept: str = "*/*", timeout: float = DEFAULT_TIMEOUT) -> bytes:
    body, _ = _request(url, accept=accept, timeout=timeout)
    return body


def get_text(url: str, *, accept: str = "*/*", timeout: float = DEFAULT_TIMEOUT) -> str:
    return get_bytes(url, accept=accept, timeout=timeout).decode("utf-8")


def get_json(
    url: str, *, accept: str = "application/json", timeout: float = DEFAULT_TIMEOUT
) -> Any:
    text = get_text(url, accept=accept, timeout=timeout)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise DataFormatError(f"GET {url} did not return valid JSON: {exc}") from exc
