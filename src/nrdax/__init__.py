"""nrdax - the open-source Python library and CLI for the NRDAX registry.

NRDAX (NullRabbit Decentralised Attack indeX) is NullRabbit's canonical,
chain-agnostic registry of techniques for attacks on decentralised infrastructure.
This package is the standard programmatic interface to the public NRDAX dataset:
load it, search and filter it, traverse relationships, export it (JSON / CSV /
STIX), cite it, and inspect changes.

Quick start::

    from nrdax import NRDAX
    registry = NRDAX.from_api()             # live registry (or NRDAX.load() after `nrdax update`)
    technique = registry.get("NRDAX-T0006")
    results = registry.search("rpc exhaustion")
    related = registry.related("NRDAX-T0006")

No dataset is bundled in the package: fetch it with ``nrdax update`` (cached for
offline use) or load a source directly (``from_api`` / ``from_feed`` / ``from_file``).

The CLI (``nrdax``) is built entirely on this library.
"""

from __future__ import annotations

from ._version import __version__
from .citations import CitationData, cite
from .errors import (
    DataFormatError,
    ExitCode,
    InvalidArgumentError,
    NotFoundError,
    NrdaxError,
    SchemaVersionError,
    SourceError,
    ValidationError,
    ValidationIssue,
)
from .models import (
    CoverageCell,
    CoverageMatrix,
    ExternalReference,
    FamilyCount,
    Instance,
    KnownCell,
    KnownCoverage,
    Technique,
)
from .queries.search import SearchResult
from .registry import NRDAX
from .relationships import RelatedResult
from .sources import RawDataset, Source, SourceMeta
from .sources.api import ApiSource
from .sources.feed import FeedSource
from .sources.file import FileSource
from .sources.memory import MemorySource
from .sources.stix import StixSource
from .vocab import (
    DISCOVERY_ORIGINS,
    FAMILIES,
    FIDELITY_CLASSES,
    NRDAX_API,
    NRDAX_SCHEMA_VERSION,
    NRDAX_SITE,
    REFERENCE_KINDS,
    REPRODUCTION_STATUSES,
    STATUSES,
)

__all__ = [
    "__version__",
    # facade
    "NRDAX",
    # models
    "Technique",
    "Instance",
    "ExternalReference",
    "KnownCoverage",
    "CoverageMatrix",
    "CoverageCell",
    "KnownCell",
    "FamilyCount",
    "SearchResult",
    "RelatedResult",
    "CitationData",
    "cite",
    # sources
    "Source",
    "RawDataset",
    "SourceMeta",
    "FeedSource",
    "ApiSource",
    "FileSource",
    "StixSource",
    "MemorySource",
    # errors
    "NrdaxError",
    "NotFoundError",
    "InvalidArgumentError",
    "SourceError",
    "DataFormatError",
    "SchemaVersionError",
    "ValidationError",
    "ValidationIssue",
    "ExitCode",
    # vocab
    "FAMILIES",
    "STATUSES",
    "FIDELITY_CLASSES",
    "DISCOVERY_ORIGINS",
    "REFERENCE_KINDS",
    "REPRODUCTION_STATUSES",
    "NRDAX_SCHEMA_VERSION",
    "NRDAX_SITE",
    "NRDAX_API",
]
