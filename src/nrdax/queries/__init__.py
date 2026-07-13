"""Query subpackage: deterministic search and composable filters."""

from __future__ import annotations

from .filters import Predicate, build_predicate
from .search import FIELDS, SearchResult, search

__all__ = ["FIELDS", "Predicate", "SearchResult", "build_predicate", "search"]
