# nrdax-python — implementation plan

The standard open-source Python library and CLI for the canonical **NRDAX**
registry (NullRabbit Decentralised Attack indeX). Structurally familiar to users
of MITRE's `mitreattack-python`, but designed for the NRDAX schema and semantics —
not forced into an ATT&CK model.

## 1. Inspection findings (canonical source)

Inspected the NRDAX backend (`nrdax/api`, Rust), its pinned `openapi.yaml`, the
golden feed artifacts, and the live surfaces. Findings:

- **Two machine interfaces exist:**
  - **Static feed** — files emitted by `nrdax-emit`: `index.json` (version, doi,
    technique ids), `registry.jsonl` (one technique per line), `families.json`,
    `coverage-matrix.json`, `stix.json`, per-technique JSON, `feed.xml` (Atom),
    `knowledge-pack.jsonld`. Deterministic, golden-tested, version-pinnable.
  - **Read API** — live at `https://api.nrdax.com` (`/techniques`,
    `/techniques/{id}`, `/families`, `/instances`, `/cve/{ref}`, `/coverage`,
    `/search`). Confirmed live (returns real JSON).
- **Canonical dataset source chosen: the static feed.** It is the version-pinnable,
  offline, deterministic snapshot format (the NRDAX analogue of MITRE's
  `attack-stix-data` static JSON). The read API is the live-query source.
- **Current dataset:** version `v0.1-import`, **381 techniques**, **no DOI**.
  291/381 techniques have **zero instances** (known-but-not-reproduced); 90 are
  reproduced. 19/29 families used, 24 instance chains (64 incl. known coverage),
  all 5 reference kinds present.

### Schema (exact fields — no invention)
- **Technique**: `id` (`NRDAX-Tnnnn`, opaque/stable), `name` (stable slug),
  `display_name?`, `mechanism`, `family`, `status` (active|deprecated|superseded),
  `first_seen` (date), `instances[]`, `external_references[]`, `provenance_note?`.
- **Instance**: `chain`, `primitive_id`, `bundle_ref`, `fidelity`
  (stub|proxy|lab|production-derived|production-captured), `discovery_origin`
  (original-research|reverse-engineered-cve|disclosed-advisory),
  `external_references[]`.
- **ExternalReference**: `kind` (cve|ghsa|vendor-advisory|nr-advisory|nr-brief),
  `id`, `url?`.
- **Coverage matrix** (derived): `chains[]`, `cells[]` (reproduced,
  `strongest_fidelity`+`instance_count`), `known[]` (known-but-not-reproduced).
- **Families**: fixed 29-name taxonomy with per-family counts.
- **STIX 2.1**: `attack-pattern` SDOs; NRDAX id anchored in `external_references`
  (`source_name:"nrdax"`); custom props `x_nrdax_family|status|chains`; ids are
  UUIDv5 under namespace `6e727669-615f-5f5f-8000-000000000001`.

### Confirmed schema gaps / limitations (isolated, documented — never fabricated)
1. **No `implementation` field** and **no `surface` field**. CLI `--implementation`
   / search on "surface" are therefore **documented derived text filters** over
   `primitive_id` + `mechanism` + reference text, not schema-backed.
2. **No asserted technique↔technique relationships** (no parent/child/related
   field). `related` surfaces **derived** links: shared family, shared chain,
   shared reference. Documented as derived.
3. **Reproduction status is derived**, not a stored field: `reproduced` (≥1
   instance) vs `known` (0). NRDAX `status` is the lifecycle enum
   (active/deprecated/superseded), a distinct axis.
4. **No `schema_version` in the feed.** We pin `NRDAX_SCHEMA_VERSION = "1.4"` (the
   contract version from the backend) and mark it tool-tracked.
5. **No DOI minted** (`v0.1-import`). Citations never fabricate a DOI; they omit it
   and note absence.
6. **No published historical versions.** Cross-version `changes` requires two
   snapshots the user supplies/caches; `--since` works from `first_seen`.
   Documented as a source limitation, with a real diff engine (not simulated).
7. **Feed vs OpenAPI drift**: feed `coverage-matrix.json` carries `known`; OpenAPI
   `/coverage` documents `gaps`. We model the feed (`known`) and note the drift.
8. **The static feed is not yet published at a stable public URL**
   (`nrdax.com/index.json` → 404). So `update`'s working remote is the live API;
   the feed URL becomes the preferred canonical remote once published.

## 2. Repository identity
- Repo `nrdax-python`, package `nrdax`, CLI `nrdax`. PyPI `nrdax` is **available**.
- GitHub home `NullRabbitLabs/nrdax-python` (siblings: `nrdax-api`, `nrdax-web`).

## 3. Licensing (ambiguity flagged)
Existing NullRabbit code repos are `UNLICENSED`; the dataset has no explicit
license. Resolution: **code is Apache-2.0** (MITRE-tooling norm, patent grant);
the **NRDAX dataset licensing stays separate and undetermined** (`DATA_LICENSE.md`
+ `NOTICE`). This tool grants no rights to the data. Flagged in the final report —
NullRabbit should publish an explicit data license before wide distribution.

## 4. Design
- **Zero required runtime dependencies** (stdlib `json`, `urllib`, `uuid`,
  `argparse`, `csv`, `dataclasses`) → fast CLI startup, trivial install. Optional
  extra `[stix]` adds the `stix2` validator; `[dev]` adds pytest/mypy/ruff/build.
- **Source-independent domain ops.** `Source` protocol → `BundledSource`,
  `FeedSource` (dir or URL), `ApiSource`, `FileSource`, `StixSource`,
  `MemorySource`. `NRDAX.load()` uses the bundled snapshot (offline, zero-config).
- **Typed dataclass models** with `from_dict`/`to_dict`, preserved unknown fields
  (`extra`), missing≠empty (Optional vs `[]`). Lenient parse + collected
  `ValidationIssue`s (`strict=True` to raise); never discards data.
- **Deterministic search** (weighted field matches, stable tie-break), **composable
  filters**, **derived relationships**, **coverage**, **JSON/CSV/STIX exporters**
  (STIX byte-parity with the Rust emitter), **citations** (text/md/bibtex/json),
  **snapshot-diff changes**, **cache** (`~/.cache/nrdax`, `meta.json`).
- **CLI** (argparse): `search get list related export cite changes info version
  update cache schema`. Structured errors + stable exit codes (0 ok, 2 usage,
  3 not-found, 4 invalid-arg, 5 source/data).

## 5. Layout
```
src/nrdax/{__init__,_version,vocab,models,errors,registry,cache,relationships,coverage,citations,changes}.py
src/nrdax/sources/{bundled,feed,api,file,stix,memory}.py
src/nrdax/queries/{search,filters}.py
src/nrdax/exporters/{json_exporter,csv_exporter,stix_exporter}.py
src/nrdax/cli/{main,formatting}.py
src/nrdax/data/snapshot/{index.json,registry.jsonl,families.json,coverage-matrix.json}  # real v0.1-import
tests/… examples/… docs/… .github/…
```

## 6. Validation & release
Run the library over the full real dataset to confirm every record loads and
round-trips (a local validation script generates a report that is kept out of the
repo). Then tests + mypy + ruff, build wheel+sdist, clean-install smoke test.
GitHub + PyPI steps documented (no credentials committed).
