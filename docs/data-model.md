# Data model

This page explains the NRDAX concepts as this client represents them, and the
versioning policy. The models mirror the canonical NRDAX schema exactly; nothing
here is invented.

## Identifiers

A technique's id has the form `NRDAX-Tnnnn` (for example `NRDAX-T0006`). Ids are
**opaque, stable, and never reused**. An id never changes across releases, so it is
safe to cite. Family is an *attribute*, not part of the id - a technique can be
reclassified without breaking its citation.

## Technique

The citable unit.

| Field | Meaning |
| --- | --- |
| `id` | Permanent `NRDAX-Tnnnn` identifier. |
| `name` | Stable slug / alias (opaque, citeable). |
| `display_name` | Human-readable label (presentation only; may improve across releases). |
| `mechanism` | Prose description of how the attack works. |
| `family` | One family from the fixed taxonomy. |
| `status` | Lifecycle: `active`, `deprecated`, or `superseded`. |
| `first_seen` | Date (`YYYY-MM-DD`). |
| `instances` | Chain-specific occurrences (evidence). |
| `external_references` | Links to CVEs, advisories, briefs. |
| `provenance_note` | Set when the technique arrived via an accepted submission. |

The human label to show is `display` (the `display_name` if present, else `name`).

## Instance

A chain-specific occurrence of a technique - the evidence for its cross-chain claim.

| Field | Meaning |
| --- | --- |
| `chain` | The chain the occurrence was observed on. |
| `primitive_id` | The pipeline primitive that reproduces it. |
| `bundle_ref` | Reference to the evidence bundle. |
| `fidelity` | How faithfully it reproduces the real attack on the wire. |
| `discovery_origin` | How the finding was discovered. |
| `external_references` | Instance-level references. |

**Fidelity classes**, weakest to strongest evidence: `stub`, `proxy`, `lab`,
`production-derived`, `production-captured`.

**Discovery origins** (a distinct axis from capture provenance):
`original-research`, `reverse-engineered-cve`, `disclosed-advisory`.

## Reproduction status (derived)

Reproduction status is **derived, not stored**: a technique is `reproduced` if it has
at least one instance, otherwise `known` (a catalogued public disclosure names it,
but no instance reproduces it). This is a different axis from the lifecycle `status`.

In the current dataset most techniques are `known`; a minority are `reproduced`.

## External references

`kind` is one of `cve`, `ghsa`, `vendor-advisory`, `nr-advisory`, `nr-brief`; `id` is
the reference identifier; `url` is optional. Reference ids are preserved exactly as
published and are never rewritten; when an `id` is not a clean short identifier, match
it with `--reference --reference-contains` (or `by_reference(..., contains=True)`).

## Families

Families are a fixed taxonomy with two groups: fine-grained families carried by
reproduced techniques, and a coarser class axis carried by known-but-not-reproduced
techniques. `nrdax schema` lists them all. `families()` returns every family with its
count, including zero-count families.

## Coverage matrix (derived)

The coverage matrix is `technique x chain`, computed from the data (never stored):

- **cells** - reproduced pairs, recording the strongest fidelity and instance count.
- **known** - pairs a disclosure names, with no reproduced instance.
- Anything in neither is a gap (implicit, to keep the payload proportional).

The chain axis is ordered most-covered first (ties by name). This client's derivation
is byte-compatible with the canonical feed's `coverage-matrix.json`.

## Relationships (derived)

NRDAX has **no asserted technique-to-technique relationship field** (no
parent/child/"related" edges). `related()` therefore surfaces only relationships
derivable from canonical fields:

- **family** - sibling techniques in the same family;
- **chain** - techniques with an instance on a shared chain;
- **reference** - techniques sharing a reference id (e.g. the same CVE) - the
  strongest link;
- **instances**, **advisories**, **briefs** - the technique's own evidence and links.

## STIX 2.1 representation

STIX is an *export* format for NRDAX, not its internal model. Each technique becomes
a STIX `attack-pattern` SDO:

- The NRDAX id is anchored in `external_references` under `source_name: "nrdax"`.
- NRDAX-specific fields ride as custom properties: `x_nrdax_family`,
  `x_nrdax_status`, `x_nrdax_chains`.
- Ids are deterministic UUIDv5 under a fixed namespace; timestamps come from
  `first_seen`. The export is byte-identical to the canonical NRDAX emitter, so
  identity round-trips.

**Parsing STIX back is lossy** (see `NRDAX.from_stix`): it recovers identity, name,
mechanism, family, status, `first_seen`, references, and the chain list (preserved in
`extra['x_nrdax_chains']`), but not per-instance detail (primitive id, bundle ref,
fidelity, discovery origin), because STIX flattens instances. Treat STIX as an
interchange format, not a full backup.

## Versioning policy

Four versions are tracked independently:

| Version | Where it lives | Changes when |
| --- | --- | --- |
| Package | `nrdax.__version__` / `pyproject.toml` | The library/CLI code changes. |
| CLI | equals the package version | with the package. |
| Dataset | `index.json` / API `registry_version` (e.g. `v0.1-import`) | NullRabbit publishes new data. |
| Schema | `nrdax.vocab.NRDAX_SCHEMA_VERSION` (e.g. `1.4`) | The field set changes. |

- A **package** release does not imply the dataset changed.
- A **dataset** release does not require a new package unless the schema changed.
- The **schema** version is tool-tracked because the feed carries no
  `schema_version` field.

**Pin an exact dataset** for reproducible research by keeping a copy of a static feed
and loading it with `--source feed:/path` (or `NRDAX.from_feed`). `nrdax update`
fetches the current dataset into the cache; the package bundles no data, so a pinned
feed copy is the way to hold a fixed version.

## Known source limitations

- No `implementation` or `surface` field exists; `--implementation` and surface
  search are derived text heuristics.
- No DOI is minted yet; citations omit it.
- No historical versioned releases are published; cross-version `changes` needs two
  snapshots you supply.
- The static feed is not yet hosted at a stable public URL; `nrdax update` uses the
  live API by default.
- The feed's `coverage-matrix.json` exposes `known`; the API's `/coverage` documents
  `gaps` in its OpenAPI. This client models the feed (`known`).
