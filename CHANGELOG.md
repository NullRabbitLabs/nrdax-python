# Changelog

All notable changes to `nrdax-python` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the package version
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Note: the *package* version tracked here is independent of the *NRDAX dataset*
version and the *NRDAX schema* version. See `docs/data-model.md` for the
compatibility policy.

## [Unreleased]

## [0.4.0] - 2026-07-25

### Changed

- **Breaking (tracks the API):** `Technique.family` is now the published *mechanism*
  taxonomy and is `str | None`. It is `None` while the registry has not classified a
  technique, which on the live registry is 323 of 420. The producing pipeline's own
  label moves to the new `producer_family` field. Code doing `t.family == "..."` or
  grouping on `t.family` must handle `None`; `Technique.is_classified` is provided
  for the intent.
- `NRDAX.families()` now returns the five mechanism families (always all five,
  zero counts included). The producer vocabulary moved to `NRDAX.producer_families()`.
  `FamilyCount` gains `axis` (`"mechanism"` or `"producer-class"`), because a name
  such as `memory_amp` occurs on both axes with different counts.
- `by_family()` and `--family` filter the mechanism axis. `by_producer_family()` and
  `--producer-family` filter the producer axis.
- Search matches both axes; STIX export carries `x_nrdax_producer_family`,
  `x_nrdax_surface`, `x_nrdax_bound_failure` and `x_nrdax_classification` alongside
  `x_nrdax_family`, byte-identical to the backend emitter.

### Fixed

- **`techniques_by_family()` and `family_siblings` no longer group unclassified
  techniques together.** Both compared families directly, and since `None == None`
  every pending technique was a "sibling" of every other one - 323 of them against
  the live registry. Grouping now requires a known mechanism.
- A `null` family is no longer reported as a validation issue. A pending technique is
  well-formed, and flagging it made the registry's own honest gap look like a data
  defect.
- The CLI renders `(pending classification)` rather than a bare `None`.

### Added

- `MECHANISM_FAMILIES`, `SURFACES`, `BOUND_FAILURES` and `CLASSIFICATION_STATES`
  vocabularies; `Technique.surface`, `.bound_failure`, `.dual_with`, `.classification`
  and `.is_classified`; `NRDAX.classified()`, `.unclassified()` and
  `.techniques_by_producer_family()`.

## [0.3.0] - 2026-07-16

### Changed

- **Breaking (tracks the API):** the live read API is now versioned under `/v1`;
  `NRDAX_API` is `https://api.nrdax.com/v1` and `ApiSource` requests the versioned
  paths. Unversioned paths on the API host return 404, so `nrdax update` and
  `--source api` in earlier releases (<= 0.2.0) no longer work against the live
  host - upgrade, or pass `--source api:https://api.nrdax.com/v1` explicitly.

## [0.2.0] - 2026-07-14

### Removed

- **The bundled dataset snapshot no longer ships in the package.** The dataset is
  versioned and distributed separately; the wheel now contains code only. Fetch the
  data explicitly with `nrdax update` (cached for offline/pinned use) or load a source
  directly (`--source api` / `NRDAX.from_api()`, `feed:`, `file:`, `stix:`). This
  mirrors how `mitreattack-python` keeps the ATT&CK data out of the library.
- Removed `NRDAX.bundled()` and the `bundled` source spec (`--source bundled`).

### Changed

- **Breaking:** the zero-config default (`NRDAX.load()`, or any CLI command with no
  `--source`) now resolves to the local cache from a prior `nrdax update`, and raises
  `SourceError` with guidance when the cache is empty (previously it silently fell back
  to the in-wheel snapshot). Run `nrdax update` once, or pass an explicit source.

## [0.1.1] - 2026-07-14

### Changed

- Refreshed the bundled dataset snapshot to the current registry: **388 techniques**
  (was 381; 7 added, `NRDAX-T0382`..`NRDAX-T0388`), captured from the live read API.
  The dataset version is unchanged (`v0.1-import`); this is a snapshot refresh, not
  a schema change.
- The snapshot now reflects the upstream canonicalisation of instance-level `cve` /
  `ghsa` reference ids (they carry the identifier, e.g. `CVE-2013-5700`, with the URL
  in `url`), so `by_reference` / `--reference` / citations / STIX `external_id`
  resolve for those references.

## [0.1.0] - 2026-07-13

First public release: the standard open-source Python interface to NRDAX.

### Added

- **Library (`nrdax`)**: the `NRDAX` facade with `load`, `get`, `search`, `filter`,
  `related`, `coverage`, `families`, `instances`, `by_reference`, and serialization
  helpers. Typed dataclass models that mirror the canonical schema, preserve unknown
  fields, and validate leniently (or strictly).
- **Data sources**: bundled snapshot (offline default), static feed (directory or
  URL), live read API (`api.nrdax.com`), local file (`.jsonl` / bundle / single
  technique), STIX 2.1 bundle, and in-memory.
- **CLI (`nrdax`)**: `search`, `get`, `list`, `related`, `export`, `cite`,
  `changes`, `info`, `version`, `update`, `cache`, `schema`. Table / JSON / CSV /
  STIX output where meaningful; stable exit codes and structured JSON errors.
- **Deterministic search**: weighted, explainable field matching (no network, no
  LLM).
- **Exporters**: JSON and CSV (with field projection), and STIX 2.1 that is
  **byte-identical** to the canonical NRDAX emitter (identity round-trips).
- **Citations**: text, Markdown, BibTeX, and CSL-JSON. Never fabricates a DOI.
- **Changes**: `--since` (from `first_seen`) and a real snapshot-diff engine.
- **Offline / cache**: `nrdax update` writes a snapshot; `nrdax cache info|clear`.
- **Bundled dataset snapshot**: NRDAX `v0.1-import` (381 techniques), captured
  2026-07-13, for zero-config offline use.
- Docs, runnable examples, a comprehensive test suite, CI, and release automation.

### Known limitations (documented, not simulated)

- NRDAX has no `implementation` or `surface` field; `--implementation` and related
  search are derived text heuristics.
- NRDAX has no asserted technique-to-technique relationships; `related` is derived
  (shared family / chain / reference).
- No historical versioned releases are published yet, so cross-version `changes`
  requires two snapshots you supply; `--from-version/--to-version` is not available.
- No DOI is minted upstream; citations omit it.
- The static feed is not yet hosted at a stable public URL, so `nrdax update`
  fetches from the live API by default.

[Unreleased]: https://github.com/NullRabbitLabs/nrdax-python/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/NullRabbitLabs/nrdax-python/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/NullRabbitLabs/nrdax-python/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/NullRabbitLabs/nrdax-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/NullRabbitLabs/nrdax-python/releases/tag/v0.1.0
