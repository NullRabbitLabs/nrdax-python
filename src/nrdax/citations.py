"""Citation generation for NRDAX techniques.

Uses the canonical URL and the metadata that actually exists: the technique's
``display`` title, ``first_seen`` date, the dataset ``version``, and the DOI *only
when one is minted*. It never fabricates bibliographic metadata — the current
dataset has no DOI, so citations omit it rather than inventing one.

Styles: ``text`` (plain), ``markdown``, ``bibtex`` (``@online``), and ``json``
(CSL-JSON, importable by reference managers). House style: hyphens, never em dashes.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .errors import InvalidArgumentError
from .models import Technique

if TYPE_CHECKING:
    from .registry import NRDAX

AUTHOR = "NullRabbit Labs"
PUBLISHER = "NullRabbit"
CONTAINER = "NRDAX - NullRabbit Decentralised Attack indeX"
CITATION_STYLES = ("text", "markdown", "bibtex", "json")


@dataclass(frozen=True)
class CitationData:
    """The resolved, source-backed fields a citation is built from."""

    id: str
    title: str
    url: str
    author: str
    publisher: str
    container: str
    version: str
    first_seen: str
    accessed: str
    doi: str | None = None

    @property
    def year(self) -> str:
        return self.first_seen[:4] if self.first_seen else ""


def _accessed(accessed: str | _dt.date | None) -> str:
    if accessed is None:
        return _dt.date.today().isoformat()
    if isinstance(accessed, _dt.date):
        return accessed.isoformat()
    return accessed


def build(
    technique: Technique,
    *,
    version: str,
    doi: str | None = None,
    accessed: str | _dt.date | None = None,
) -> CitationData:
    return CitationData(
        id=technique.id,
        title=technique.display,
        url=technique.url,
        author=AUTHOR,
        publisher=PUBLISHER,
        container=CONTAINER,
        version=version,
        first_seen=technique.first_seen,
        accessed=_accessed(accessed),
        doi=doi,
    )


def _text(c: CitationData) -> str:
    doi = f" https://doi.org/{c.doi}" if c.doi else ""
    year = f" ({c.year})" if c.year else ""
    return (
        f"{c.author}.{year} {c.title} ({c.id}). {c.container}, version {c.version}. "
        f"Retrieved {c.accessed}, from {c.url}.{doi}"
    )


def _markdown(c: CitationData) -> str:
    doi = f" [doi:{c.doi}](https://doi.org/{c.doi})" if c.doi else ""
    year = f" ({c.year})" if c.year else ""
    return (
        f"{c.author}.{year} *{c.title}* ({c.id}). {c.container}, version {c.version}. "
        f"Retrieved {c.accessed}, from [{c.url}]({c.url}).{doi}"
    )


def _bibtex(c: CitationData) -> str:
    lines = [
        f"@online{{{c.id},",
        f"  author       = {{{c.author}}},",
        f"  title        = {{{{{c.title}}}}},",
    ]
    if c.year:
        lines.append(f"  year         = {{{c.year}}},")
    lines += [
        f"  organization = {{{c.publisher}}},",
        f"  howpublished = {{{c.container}}},",
        f"  version      = {{{c.version}}},",
        f"  number       = {{{c.id}}},",
        f"  url          = {{{c.url}}},",
        f"  urldate      = {{{c.accessed}}},",
    ]
    if c.doi:
        lines.append(f"  doi          = {{{c.doi}}},")
    lines.append(f"  note         = {{NRDAX technique {c.id}}}")
    lines.append("}")
    return "\n".join(lines)


def _csl_json(c: CitationData) -> str:
    parts = c.first_seen.split("-")
    issued: dict[str, Any] = {}
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        issued = {"date-parts": [[int(parts[0]), int(parts[1]), int(parts[2])]]}
    acc = c.accessed.split("-")
    accessed_obj: dict[str, Any] = {}
    if len(acc) == 3 and all(p.isdigit() for p in acc):
        accessed_obj = {"date-parts": [[int(acc[0]), int(acc[1]), int(acc[2])]]}

    doc: dict[str, Any] = {
        "id": c.id,
        "type": "dataset",
        "title": c.title,
        "author": [{"literal": c.author}],
        "publisher": c.publisher,
        "container-title": c.container,
        "version": c.version,
        "number": c.id,
        "URL": c.url,
        "note": f"NRDAX technique {c.id}",
    }
    if issued:
        doc["issued"] = issued
    if accessed_obj:
        doc["accessed"] = accessed_obj
    if c.doi:
        doc["DOI"] = c.doi
    return json.dumps(doc, indent=2, ensure_ascii=False)


_RENDERERS = {
    "text": _text,
    "markdown": _markdown,
    "bibtex": _bibtex,
    "json": _csl_json,
}


def render(citation: CitationData, style: str = "text") -> str:
    try:
        return _RENDERERS[style](citation)
    except KeyError:
        raise InvalidArgumentError(
            f"unknown citation style {style!r} (choose from {', '.join(CITATION_STYLES)})"
        ) from None


def cite(
    registry: NRDAX,
    technique_id: str,
    *,
    style: str = "text",
    accessed: str | _dt.date | None = None,
) -> str:
    """Build and render a citation for a technique in ``registry``."""
    technique = registry.get(technique_id)
    data = build(technique, version=registry.version, doi=registry.doi, accessed=accessed)
    return render(data, style)
