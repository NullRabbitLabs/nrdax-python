"""The :class:`NRDAX` facade — the one object users load and query.

Turns a :class:`~nrdax.sources.RawDataset` (from any source) into a validated,
indexed, queryable registry. All domain operations live here or in the small
modules it delegates to (``queries``, ``relationships``, ``coverage``), never in
the CLI. Loading is source-independent: the read behaviour is identical whether the
data came from the bundled snapshot, a feed, the live API, a file, or STIX.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator
from functools import cached_property

from . import cache as _cache
from . import relationships as _relationships
from .coverage import coverage_matrix
from .errors import IssueCollector, NotFoundError, ValidationIssue
from .models import (
    CoverageMatrix,
    FamilyCount,
    Instance,
    KnownCoverage,
    Technique,
)
from .queries import filters as _filters
from .queries.search import SearchResult
from .queries.search import search as _search
from .relationships import RelatedResult
from .sources import RawDataset, Source, SourceMeta
from .sources.bundled import BundledSource
from .vocab import FAMILIES, NRDAX_SCHEMA_VERSION


def default_source() -> Source:
    """The zero-config source: the freshest local data available offline — the
    cached snapshot if ``nrdax update`` has run, otherwise the bundled snapshot."""
    if _cache.has_snapshot():
        return _cache.CacheSource()
    return BundledSource()


class NRDAX:
    """A loaded, indexed NRDAX registry."""

    def __init__(self, raw: RawDataset, *, strict: bool = False):
        self.version = raw.version
        self.doi = raw.doi
        self.source_meta: SourceMeta | None = raw.meta
        self.schema_version = NRDAX_SCHEMA_VERSION

        collector = IssueCollector(strict=strict)
        techniques: list[Technique] = []
        by_id: dict[str, Technique] = {}
        for raw_t in raw.techniques:
            tech = Technique.from_dict(raw_t, collector)
            if tech.id and tech.id in by_id:
                collector.add(tech.id, "duplicate technique id", "error")
                continue
            techniques.append(tech)
            if tech.id:
                by_id[tech.id] = tech

        techniques.sort(key=lambda t: t.id)
        self.techniques: list[Technique] = techniques
        self._by_id = by_id

        self.known_coverage: list[KnownCoverage] = [
            KnownCoverage.from_dict(k) for k in raw.known_coverage
        ]
        for kc in self.known_coverage:
            if kc.technique_id not in by_id:
                collector.add(
                    kc.technique_id,
                    "known-coverage entry references an unknown technique id",
                    "warning",
                )

        # Family vocabulary: the fixed taxonomy ∪ what the source declared ∪ what
        # the data actually uses (so an unexpected family still appears with a count).
        vocab = set(FAMILIES)
        if raw.families:
            vocab.update(raw.families)
        vocab.update(t.family for t in techniques if t.family)
        self.families_vocab: list[str] = sorted(vocab)

        self.issues: list[ValidationIssue] = collector.issues
        self._build_indexes()

    def _build_indexes(self) -> None:
        by_family: dict[str, list[Technique]] = defaultdict(list)
        by_chain: dict[str, list[Technique]] = defaultdict(list)
        by_reference: dict[str, list[Technique]] = defaultdict(list)
        for tech in self.techniques:
            by_family[tech.family].append(tech)
            for chain in tech.chains:
                by_chain[chain].append(tech)
            for ref_id in tech.reference_ids:
                by_reference[ref_id].append(tech)
        self._by_family = by_family
        self._by_chain = by_chain
        self._by_reference = by_reference

    # -- construction ----------------------------------------------------------

    @classmethod
    def load(cls, source: Source | None = None, *, strict: bool = False) -> NRDAX:
        """Load a registry. With no ``source``, use the zero-config default
        (cached snapshot if present, else the bundled snapshot)."""
        src = source if source is not None else default_source()
        return cls(src.load(), strict=strict)

    @classmethod
    def from_source(cls, source: Source, *, strict: bool = False) -> NRDAX:
        return cls(source.load(), strict=strict)

    @classmethod
    def bundled(cls, *, strict: bool = False) -> NRDAX:
        return cls(BundledSource().load(), strict=strict)

    @classmethod
    def from_cache(cls, *, strict: bool = False) -> NRDAX:
        return cls(_cache.CacheSource().load(), strict=strict)

    @classmethod
    def from_feed(cls, location: str, *, strict: bool = False) -> NRDAX:
        from .sources.feed import FeedSource

        return cls(FeedSource(location).load(), strict=strict)

    @classmethod
    def from_api(cls, base_url: str | None = None, *, strict: bool = False) -> NRDAX:
        from .sources.api import ApiSource

        src = ApiSource(base_url) if base_url else ApiSource()
        return cls(src.load(), strict=strict)

    @classmethod
    def from_file(cls, path: str, *, strict: bool = False) -> NRDAX:
        from .sources.file import FileSource

        return cls(FileSource(path).load(), strict=strict)

    @classmethod
    def from_stix(
        cls, path: str | None = None, *, bundle: dict | None = None, strict: bool = False
    ) -> NRDAX:
        from .sources.stix import StixSource

        return cls(StixSource(bundle=bundle, path=path).load(), strict=strict)

    @classmethod
    def from_memory(cls, techniques: Iterable, *, strict: bool = False, **kw) -> NRDAX:
        from .sources.memory import MemorySource

        return cls(MemorySource(techniques, **kw).load(), strict=strict)

    # -- container protocol ----------------------------------------------------

    def __len__(self) -> int:
        return len(self.techniques)

    def __iter__(self) -> Iterator[Technique]:
        return iter(self.techniques)

    def __contains__(self, technique_id: object) -> bool:
        return isinstance(technique_id, str) and technique_id.strip().upper() in self._by_id

    # -- retrieval -------------------------------------------------------------

    def get(self, technique_id: str) -> Technique:
        """Return a technique by id (case-insensitive). Raises
        :class:`~nrdax.errors.NotFoundError` if absent."""
        tech = self._by_id.get(technique_id.strip().upper())
        if tech is None:
            raise NotFoundError(f"no such technique: {technique_id}")
        return tech

    def find(self, technique_id: str) -> Technique | None:
        """Like :meth:`get` but returns ``None`` instead of raising."""
        return self._by_id.get(technique_id.strip().upper())

    # -- search & filter -------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        limit: int | None = None,
        fields: tuple[str, ...] | None = None,
    ) -> list[SearchResult]:
        return _search(self.techniques, query, limit=limit, fields=fields)

    def filter(self, **criteria) -> list[Technique]:
        """Return techniques matching all given criteria (see
        :func:`nrdax.queries.filters.build_predicate`), sorted by id."""
        predicate = _filters.build_predicate(**criteria)
        return [t for t in self.techniques if predicate(t)]

    # alias that reads naturally on the CLI
    list_techniques = filter

    # -- relationships & derived views -----------------------------------------

    def related(self, technique_id: str) -> RelatedResult:
        return _relationships.related(self, technique_id)

    @cached_property
    def coverage(self) -> CoverageMatrix:
        return coverage_matrix(self.techniques, self.known_coverage)

    def families(self) -> list[FamilyCount]:
        """Every family in the vocabulary with its technique count (incl. zero)."""
        counts: dict[str, int] = defaultdict(int)
        for tech in self.techniques:
            counts[tech.family] += 1
        return [
            FamilyCount(name=name, technique_count=counts[name]) for name in self.families_vocab
        ]

    def chains(self) -> list[str]:
        """Chains with at least one reproduced instance, sorted."""
        return sorted(self._by_chain)

    def instances(
        self, *, chain: str | None = None, discovery_origin: str | None = None
    ) -> list[tuple[str, Instance]]:
        """All instances (annotated with their technique id), optionally filtered."""
        out: list[tuple[str, Instance]] = []
        for tech in self.techniques:
            for inst in tech.instances:
                if chain is not None and inst.chain != chain:
                    continue
                if discovery_origin is not None and inst.discovery_origin != discovery_origin:
                    continue
                out.append((tech.id, inst))
        return out

    def by_reference(self, reference_id: str) -> list[Technique]:
        """Techniques carrying an external reference with this id (the ``/cve/{ref}``
        semantics)."""
        return list(self._by_reference.get(reference_id, []))

    # -- indexes used by relationship traversal --------------------------------

    def techniques_by_family(self, family: str) -> list[Technique]:
        return list(self._by_family.get(family, []))

    def techniques_by_chain(self, chain: str) -> list[Technique]:
        return list(self._by_chain.get(chain, []))

    def techniques_with_reference(self, reference_id: str) -> list[Technique]:
        return list(self._by_reference.get(reference_id, []))

    # -- validation & serialization --------------------------------------------

    def validate(self) -> list[ValidationIssue]:
        """The validation issues found while loading (empty means clean)."""
        return list(self.issues)

    def to_records(self) -> list[dict]:
        """Every technique as a canonical dict (round-trips the feed layout)."""
        return [t.to_dict() for t in self.techniques]

    def to_release_dict(self) -> dict:
        """The whole registry as one object (version, doi, techniques, coverage)."""
        out: dict = {"version": self.version}
        if self.doi:
            out["doi"] = self.doi
        out["technique_count"] = len(self.techniques)
        out["techniques"] = self.to_records()
        if self.known_coverage:
            out["known_coverage"] = [
                {"technique_id": kc.technique_id, "chains": list(kc.chains)}
                for kc in self.known_coverage
            ]
        return out
