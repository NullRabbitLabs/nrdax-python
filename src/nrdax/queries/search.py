"""Deterministic, explainable keyword search.

Ranks techniques by weighted field matches. No network, no embeddings, no LLM —
same query in, same ranking out (ties broken by id). The live API additionally
offers semantic (pgvector) search; this local search is the default and is always
available offline. Each result records *which* fields matched, so the CLI can
explain a hit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..models import Technique
from ..vocab import TECHNIQUE_ID_PATTERN

_ID_RE = re.compile(TECHNIQUE_ID_PATTERN, re.IGNORECASE)

# Field weights. Id matches dominate; free-text mechanism matches are the floor.
_WEIGHTS: dict[str, float] = {
    "id": 100.0,
    "name": 8.0,
    "display_name": 8.0,
    "family": 5.0,
    "chain": 4.0,
    "primitive_id": 3.0,
    "reference": 3.0,
    "mechanism": 2.0,
    "bundle_ref": 1.0,
}
_PHRASE_BONUS = 2.0

# All searchable field keys (order fixed for deterministic explanations).
FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "display_name",
    "family",
    "chain",
    "primitive_id",
    "reference",
    "mechanism",
    "bundle_ref",
)


@dataclass(frozen=True)
class SearchResult:
    technique: Technique
    score: float
    matched_fields: tuple[str, ...] = field(default_factory=tuple)


def _field_texts(t: Technique) -> dict[str, list[str]]:
    return {
        "id": [t.id],
        "name": [t.name],
        "display_name": [t.display_name] if t.display_name else [],
        "family": [t.family],
        "chain": [i.chain for i in t.instances],
        "primitive_id": [i.primitive_id for i in t.instances],
        "reference": [ref.id for _, ref in t.iter_references()]
        + [ref.url for _, ref in t.iter_references() if ref.url],
        "mechanism": [t.mechanism],
        "bundle_ref": [i.bundle_ref for i in t.instances],
    }


def _score_one(
    t: Technique, terms: list[str], phrase: str, fields: tuple[str, ...]
) -> tuple[float, tuple[str, ...]]:
    texts = _field_texts(t)
    score = 0.0
    matched: list[str] = []

    # Exact id match short-circuits to the top, deterministically.
    if _ID_RE.match(phrase) and t.id.lower() == phrase.lower():
        return 1000.0, ("id",)

    for fname in fields:
        weight = _WEIGHTS[fname]
        blob = "  ".join(texts.get(fname, [])).lower()
        if not blob:
            continue
        field_hit = False
        for term in terms:
            if term and term in blob:
                score += weight
                field_hit = True
        if len(terms) > 1 and phrase in blob:
            score += _PHRASE_BONUS
            field_hit = True
        if field_hit:
            matched.append(fname)

    return score, tuple(matched)


def search(
    techniques: list[Technique],
    query: str,
    *,
    limit: int | None = None,
    fields: tuple[str, ...] | None = None,
) -> list[SearchResult]:
    """Return techniques ranked by relevance to ``query`` (empty query → no results).

    ``fields`` optionally restricts the searched fields (defaults to all of
    :data:`FIELDS`). Results are sorted by descending score, ties broken by id.
    """
    phrase = query.strip().lower()
    if not phrase:
        return []
    terms = phrase.split()
    use_fields = fields or FIELDS

    scored: list[SearchResult] = []
    for t in techniques:
        score, matched = _score_one(t, terms, phrase, use_fields)
        if score > 0:
            scored.append(SearchResult(technique=t, score=score, matched_fields=matched))

    scored.sort(key=lambda r: (-r.score, r.technique.id))
    return scored[:limit] if limit is not None else scored
