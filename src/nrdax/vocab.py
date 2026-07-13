"""The NRDAX controlled vocabularies.

These mirror the canonical registry's own vocabularies (the Rust backend's
``domain/vocab.rs``). They are used for *validation* and for user-facing help, but
loading is deliberately lenient: an unknown value is preserved and reported as a
:class:`~nrdax.errors.ValidationIssue`, never silently dropped and never a hard
failure unless ``strict=True`` is requested. The canonical registry owns the
invariants; this client reads already-published data and refuses to fabricate or
discard it.
"""

from __future__ import annotations

from typing import Final

#: The NRDAX contract/schema version this client targets. The feed does **not**
#: carry a ``schema_version`` field, so this is tool-tracked rather than read from
#: the data. Bump only on a breaking change to the field set.
NRDAX_SCHEMA_VERSION: Final = "1.4"

#: The canonical public host for human pages and citations.
NRDAX_SITE: Final = "https://nrdax.com"
#: The live read API base URL.
NRDAX_API: Final = "https://api.nrdax.com"

#: Regex source for a technique id. Ids are opaque, stable, and never reused.
TECHNIQUE_ID_PATTERN: Final = r"^NRDAX-T[0-9]{4}$"

#: The fixed family taxonomy (union of the fine-grained reproduced families and the
#: coarse ``class`` axis carried by known-but-not-reproduced techniques).
FAMILIES: Final[tuple[str, ...]] = (
    # Fine-grained families (the reproduced slice).
    "amm_value_extraction",
    "auth_bypass",
    "benign",
    "bridge_message_abuse",
    "compute_amp",
    "connection_exhaustion",
    "consensus_abuse",
    "gossip_abuse",
    "governance_capture",
    "liquidation_abuse",
    "memory_amp",
    "oracle_manipulation",
    "protocol_logic_exploit",
    "rate_limiter_bypass",
    "reconnaissance",
    "response_amp",
    "rpc_handler_cpu",
    "service_misconfig",
    "state_import_abuse",
    "subscription_cpu_amp",
    # Coarse ``class`` axis (known-but-not-reproduced techniques).
    "bridge",
    "consensus",
    "crypto",
    "economic-defi",
    "governance",
    "ledger-tx",
    "network-p2p",
    "network-rpc",
    "supply-chain",
)

#: Registry lifecycle statuses (distinct from *reproduction* status).
STATUSES: Final[tuple[str, ...]] = ("active", "deprecated", "superseded")

#: How faithfully an instance reproduces the real attack on the wire, weakest to
#: strongest. The order encodes evidence strength (see :func:`fidelity_strength`).
FIDELITY_CLASSES: Final[tuple[str, ...]] = (
    "stub",
    "proxy",
    "lab",
    "production-derived",
    "production-captured",
)

#: How a finding was discovered (a distinct axis from capture provenance).
DISCOVERY_ORIGINS: Final[tuple[str, ...]] = (
    "original-research",
    "reverse-engineered-cve",
    "disclosed-advisory",
)

#: The kinds of external references a technique or instance can carry.
REFERENCE_KINDS: Final[tuple[str, ...]] = (
    "cve",
    "ghsa",
    "vendor-advisory",
    "nr-advisory",
    "nr-brief",
)

#: Derived reproduction-status values (not a stored field). ``reproduced`` iff the
#: technique has at least one instance, else ``known``.
REPRODUCTION_STATUSES: Final[tuple[str, ...]] = ("reproduced", "known")

_FIDELITY_STRENGTH: Final[dict[str, int]] = {
    "stub": 0,
    "proxy": 1,
    "lab": 2,
    "production-derived": 3,
    "production-captured": 4,
}


def fidelity_strength(fidelity: str) -> int:
    """Evidence strength of a fidelity class (higher = more faithful).

    Unknown values sort weakest (``-1``) so a malformed instance never masquerades
    as stronger evidence in the coverage matrix.
    """
    return _FIDELITY_STRENGTH.get(fidelity, -1)
