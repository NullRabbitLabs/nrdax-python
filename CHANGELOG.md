# Changelog

All notable changes to `nrdax-python` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the package version
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Note: the *package* version tracked here is independent of the *NRDAX dataset*
version and the *NRDAX schema* version. See `docs/data-model.md` for the
compatibility policy.

## [Unreleased]

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

[Unreleased]: https://github.com/NullRabbitLabs/nrdax-python/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/NullRabbitLabs/nrdax-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/NullRabbitLabs/nrdax-python/releases/tag/v0.1.0
