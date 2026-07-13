"""Composable record filters.

Each builder returns a predicate ``Technique -> bool``; :func:`build_predicate`
ANDs a set of keyword criteria together (composable where reasonable). Values for
closed vocabularies (family, status, fidelity, discovery origin, reproduction
status) are validated up front so an invalid filter fails clearly rather than
silently returning nothing.

Two filters are **derived heuristics**, not schema-backed fields (NRDAX has no
``implementation`` or ``surface`` field): :func:`by_implementation` and
:func:`by_text` match across ``primitive_id`` + ``mechanism`` + references + name.
Callers should surface this to users (the CLI does).
"""

from __future__ import annotations

from collections.abc import Callable

from ..errors import InvalidArgumentError
from ..models import Technique
from ..vocab import (
    DISCOVERY_ORIGINS,
    FIDELITY_CLASSES,
    REPRODUCTION_STATUSES,
    STATUSES,
)

Predicate = Callable[[Technique], bool]


def _validate(value: str, allowed: tuple[str, ...], what: str) -> str:
    if value not in allowed:
        raise InvalidArgumentError(f"invalid {what} {value!r}; choose one of: {', '.join(allowed)}")
    return value


def by_family(name: str) -> Predicate:
    return lambda t: t.family == name


def by_status(status: str) -> Predicate:
    _validate(status, STATUSES, "status")
    return lambda t: t.status == status


def by_chain(chain: str) -> Predicate:
    lowered = chain.lower()
    return lambda t: any(i.chain.lower() == lowered for i in t.instances)


def by_fidelity(fidelity: str) -> Predicate:
    _validate(fidelity, FIDELITY_CLASSES, "fidelity")
    return lambda t: any(i.fidelity == fidelity for i in t.instances)


def by_discovery_origin(origin: str) -> Predicate:
    _validate(origin, DISCOVERY_ORIGINS, "discovery origin")
    return lambda t: any(i.discovery_origin == origin for i in t.instances)


def by_reproduction_status(status: str) -> Predicate:
    _validate(status, REPRODUCTION_STATUSES, "reproduction status")
    return lambda t: t.reproduction_status == status


def by_reference(ref_id: str, *, contains: bool = False) -> Predicate:
    """Match techniques carrying an external reference with this id.

    Exact by default (advisory/CVE lookups); ``contains=True`` matches substrings,
    which is useful given some references carry long free-text ids.
    """
    if contains:
        needle = ref_id.lower()
        return lambda t: any(needle in rid.lower() for rid in t.reference_ids)
    return lambda t: ref_id in t.reference_ids


def by_text(needle: str) -> Predicate:
    """Case-insensitive match across the technique's searchable text (name,
    display name, mechanism, primitive ids, and reference ids/urls)."""
    q = needle.lower()

    def pred(t: Technique) -> bool:
        haystacks = [t.name, t.display_name or "", t.mechanism]
        for inst in t.instances:
            haystacks.append(inst.primitive_id)
            haystacks.append(inst.chain)
        for _, ref in t.iter_references():
            haystacks.append(ref.id)
            if ref.url:
                haystacks.append(ref.url)
        return any(q in h.lower() for h in haystacks)

    return pred


def by_implementation(token: str) -> Predicate:
    """DERIVED heuristic filter for an affected implementation/client.

    NRDAX has no first-class ``implementation`` field, so this matches ``token``
    across ``primitive_id``, ``mechanism``, and reference text. Treat results as a
    best-effort text match, not an authoritative implementation list.
    """
    return by_text(token)


def all_of(*predicates: Predicate) -> Predicate:
    return lambda t: all(p(t) for p in predicates)


def build_predicate(
    *,
    family: str | None = None,
    status: str | None = None,
    chain: str | None = None,
    fidelity: str | None = None,
    discovery_origin: str | None = None,
    reproduction_status: str | None = None,
    reference: str | None = None,
    reference_contains: bool = False,
    implementation: str | None = None,
    text: str | None = None,
) -> Predicate:
    """Combine the given criteria into a single AND predicate. Unspecified
    criteria are ignored; an all-``None`` call matches everything."""
    preds: list[Predicate] = []
    if family is not None:
        preds.append(by_family(family))
    if status is not None:
        preds.append(by_status(status))
    if chain is not None:
        preds.append(by_chain(chain))
    if fidelity is not None:
        preds.append(by_fidelity(fidelity))
    if discovery_origin is not None:
        preds.append(by_discovery_origin(discovery_origin))
    if reproduction_status is not None:
        preds.append(by_reproduction_status(reproduction_status))
    if reference is not None:
        preds.append(by_reference(reference, contains=reference_contains))
    if implementation is not None:
        preds.append(by_implementation(implementation))
    if text is not None:
        preds.append(by_text(text))
    return all_of(*preds) if preds else (lambda t: True)
