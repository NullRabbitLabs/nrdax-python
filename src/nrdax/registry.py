"""The :class:`NRDAX` facade — the one object users load and query.

Turns a :class:`~nrdax.sources.RawDataset` (from any source) into a validated,
indexed, queryable registry. All domain operations live here or in the small
modules it delegates to (``queries``, ``relationships``, ``coverage``), never in
the CLI. Loading is source-independent: the read behaviour is identical whether the
data came from the local cache, a feed, the live API, a file, or STIX.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator
from functools import cached_property

from . import cache as _cache
from . import relationships as _relationships
from .coverage import coverage_matrix
from .errors import IssueCollector, NotFoundError, SourceError, ValidationIssue
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
from .vocab import FAMILIES, MECHANISM_FAMILIES, NRDAX_SCHEMA_VERSION


def default_source() -> Source:
    """The zero-config source: the cached snapshot from a prior ``nrdax update``.

    No dataset is bundled in the package (the data is versioned and distributed
    separately). If the cache is empty there is nothing to load offline, so this
    raises — fetch first with ``nrdax update`` or pass an explicit source such as
    ``--source api`` (``NRDAX.from_api()``)."""
    if _cache.has_snapshot():
        return _cache.CacheSource()
    raise SourceError(
        "no local NRDAX data: run `nrdax update` to fetch the dataset into the cache, "
        "or load an explicit source such as `--source api` (Python: NRDAX.from_api())."
    )


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
        by_producer_family: dict[str, list[Technique]] = defaultdict(list)
        by_chain: dict[str, list[Technique]] = defaultdict(list)
        by_reference: dict[str, list[Technique]] = defaultdict(list)
        unclassified: list[Technique] = []
        for tech in self.techniques:
            # Only classified techniques are indexed by mechanism family. Indexing
            # `None` would put every pending technique in one bucket and make them
            # each other's family siblings - 323 of 420 on the live registry.
            if tech.family is not None:
                by_family[tech.family].append(tech)
            else:
                unclassified.append(tech)
            if tech.producer_family is not None:
                by_producer_family[tech.producer_family].append(tech)
            for chain in tech.chains:
                by_chain[chain].append(tech)
            for ref_id in tech.reference_ids:
                by_reference[ref_id].append(tech)
        self._by_family = by_family
        self._by_producer_family = by_producer_family
        self._by_chain = by_chain
        self._by_reference = by_reference
        self._unclassified = unclassified

    # -- construction ----------------------------------------------------------

    @classmethod
    def load(cls, source: Source | None = None, *, strict: bool = False) -> NRDAX:
        """Load a registry. With no ``source``, use the zero-config default: the
        cached snapshot from a prior ``nrdax update``. The package bundles no data,
        so this raises :class:`~nrdax.errors.SourceError` when the cache is empty —
        fetch first (``nrdax update``) or pass an explicit source (e.g.
        ``NRDAX.from_api()``)."""
        src = source if source is not None else default_source()
        return cls(src.load(), strict=strict)

    @classmethod
    def from_source(cls, source: Source, *, strict: bool = False) -> NRDAX:
        return cls(source.load(), strict=strict)

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
        """Every MECHANISM family with its technique count, including zero counts.

        This is the published taxonomy. For the producing pipeline's own labels see
        :meth:`producer_families`; the two are separate axes and a name such as
        ``memory_amp`` occurs on both with different counts."""
        counts: dict[str, int] = defaultdict(int)
        for tech in self.techniques:
            if tech.family is not None:
                counts[tech.family] += 1
        return [
            FamilyCount(name=name, technique_count=counts[name], axis="mechanism")
            for name in MECHANISM_FAMILIES
        ]

    def producer_families(self) -> list[FamilyCount]:
        """Every producer-label family with its technique count, including zeros."""
        counts: dict[str, int] = defaultdict(int)
        for tech in self.techniques:
            if tech.producer_family is not None:
                counts[tech.producer_family] += 1
        return [
            FamilyCount(name=name, technique_count=counts[name], axis="producer-class")
            for name in self.families_vocab
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

    def techniques_by_family(self, family: str | None) -> list[Technique]:
        """Techniques carrying this mechanism family. ``None`` returns an empty list
        rather than every unclassified technique; use :meth:`unclassified` for those."""
        if family is None:
            return []
        return list(self._by_family.get(family, []))

    def techniques_by_producer_family(self, family: str | None) -> list[Technique]:
        """Techniques carrying this producer label (a different axis)."""
        if family is None:
            return []
        return list(self._by_producer_family.get(family, []))

    def unclassified(self) -> list[Technique]:
        """Techniques with no mechanism family yet, in registry order."""
        return list(self._unclassified)

    def classified(self) -> list[Technique]:
        """Techniques carrying a mechanism family, in registry order."""
        return [t for t in self.techniques if t.family is not None]

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
