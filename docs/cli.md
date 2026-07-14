# CLI reference

The `nrdax` command is a thin layer over the library. Every data-loading command
accepts `--source` and `--strict`; output-producing commands accept `--format`.

```
nrdax <command> [options]
```

Run `nrdax <command> --help` for the exact options of any command.

## Global concepts

### `--source SPEC`

Selects where data is loaded from. `SPEC` is one of:

| Spec | Meaning |
| --- | --- |
| *(omitted)* | Cached snapshot from a prior `nrdax update`; errors if the cache is empty (no data is bundled). |
| `cache` | The local cache written by `nrdax update`. |
| `api` or `api:URL` | The live read API (default `https://api.nrdax.com`). |
| `feed:LOCATION` | A static-feed directory or base URL. |
| `file:PATH` | A local `registry.jsonl`, a bundle JSON, or a single technique JSON. |
| `stix:PATH` | A STIX 2.1 bundle (lossy import; see the data model). |
| a bare path/dir/URL | Auto-detected: a directory or URL loads as a feed, a file as a file. |

### `--strict`

Fail on the first data validation issue instead of loading leniently. By default,
issues are collected and surfaced (via `nrdax info`), never silently dropped and
never fatal.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Unexpected error. |
| `2` | Usage error (bad option/argument; argparse). |
| `3` | Not found (unknown technique id or reference). |
| `4` | Invalid argument (bad filter value, unsupported format/style, version mismatch). |
| `5` | Source error (unreachable source, malformed data, missing/stale cache). |

With `--format json`, errors print a structured body: `{"error": {"code", "message"}}`.

---

## `nrdax search <query>`

Deterministic, explainable keyword search across id, name, display name, family,
chain, primitive id, references, mechanism, and bundle ref.

| Option | Description |
| --- | --- |
| `--limit N` | Max results (default 20). |
| `--search-fields F...` | Restrict which fields are searched. |
| `--explain` | Show which fields matched each hit. |
| `--fields F...` | Columns for `--format csv`. |
| `--format table\|json\|csv` | Output format (default `table`). |

```bash
nrdax search "unauthenticated rpc worker exhaustion" --explain
nrdax search NRDAX-T0006            # exact id match ranks first
nrdax search "getblock" --format json
```

The live API additionally offers semantic (pgvector) search; this local search is
deterministic and always available offline.

## `nrdax get <id>`

One technique with instances, references, and provenance.

| Option | Description |
| --- | --- |
| `--format table\|json\|stix` | Output format (default `table`). |

```bash
nrdax get NRDAX-T0006
nrdax get NRDAX-T0006 --format json
nrdax get NRDAX-T0006 --format stix
```

Unknown id exits `3`.

## `nrdax list [filters]`

Filter and list techniques. Filters compose (AND).

| Filter | Description |
| --- | --- |
| `--family F` | Exact family (validated against the vocabulary). |
| `--chain C` | Techniques with a reproduced instance on chain `C`. |
| `--status S` | Lifecycle status (`active`/`deprecated`/`superseded`). |
| `--fidelity F` | Any instance with this fidelity. |
| `--discovery-origin O` | Any instance with this discovery origin. |
| `--reproduction-status R` | `reproduced` (has an instance) or `known`. |
| `--implementation TOKEN` | Derived text heuristic (no first-class field). |
| `--reference ID` | Carries an external reference (advisory/CVE/GHSA) with this id. |
| `--reference-contains` | Treat `--reference` as a substring match. |
| `--text T` | Free-text match across searchable fields. |
| `--limit N` | Max techniques. |
| `--fields F...` | Columns (table/csv). |
| `--format table\|json\|csv` | Output format. |

```bash
nrdax list --chain solana
nrdax list --implementation agave
nrdax list --family compute_amp
nrdax list --reproduction-status reproduced
nrdax list --chain solana --family compute_amp --format csv
```

## `nrdax related <id>`

Derived relationships for a technique: family siblings, techniques on shared chains,
techniques sharing a reference (the strongest link, e.g. the same CVE), the
technique's own instances, advisories, and research briefs.

```bash
nrdax related NRDAX-T0006
nrdax related NRDAX-T0006 --format json
```

NRDAX has no asserted technique-to-technique relationships, so every relationship is
derived from canonical fields. The output says so.

## `nrdax export [filters]`

Export a filtered subset. Accepts all `list` filters, plus:

| Option | Description |
| --- | --- |
| `--format json\|csv\|stix` | Export format (default `json`). |
| `--fields F...` | Field projection (json/csv). |
| `--csv-rows techniques\|instances` | CSV granularity (default `techniques`). |
| `--output FILE`, `-o` | Write to a file instead of stdout. |

```bash
nrdax export --format json --output nrdax.json
nrdax export --format csv --output nrdax.csv
nrdax export --format stix --output nrdax-stix.json
nrdax export --chain solana --format json
nrdax export --implementation agave --fields id,name,family,reproduction_status
```

Exports preserve identifiers and provenance (the JSON wrapper carries the dataset
version and DOI). CSV flattens nested collections deterministically (lists joined
with `;`, plus `instance_count`); no field is silently dropped.

## `nrdax cite <id>`

Generate a citation.

| Option | Description |
| --- | --- |
| `--format text\|markdown\|bibtex\|json` | Citation style (default `text`; `json` is CSL-JSON). |
| `--accessed DATE` | Access date `YYYY-MM-DD` (default: today). |

```bash
nrdax cite NRDAX-T0006
nrdax cite NRDAX-T0006 --format markdown
nrdax cite NRDAX-T0006 --format bibtex
nrdax cite NRDAX-T0006 --format json
```

Uses the canonical URL and the dataset version. No DOI is minted yet, so citations
omit it rather than inventing one.

## `nrdax changes`

Inspect changes.

| Option | Description |
| --- | --- |
| `--since DATE` | Techniques first seen on or after `DATE`. |
| `--from SOURCE` / `--to SOURCE` | Diff two dataset sources (source specs). |
| `--from-version` / `--to-version` | Not available (see below); exits `4` with guidance. |
| all `list` filters | Restrict the change set. |
| `--format table\|json` | Output format. |

```bash
nrdax changes --since 2026-07-01
nrdax changes --since 2026-07-01 --implementation agave
nrdax changes --from cache --to api
nrdax changes --from file:old.jsonl --to file:new.jsonl
```

NRDAX does not yet publish historical versioned releases addressable by version
number, so `--from-version/--to-version` are unavailable and exit `4` with a message
pointing you at `--from/--to`. The diff engine is real, not simulated: give it two
snapshots and it reports added/removed techniques, status and family changes,
reproduction-status changes, added instances and chains, and newly linked advisories.

## `nrdax info`

Dataset, source, and cache information.

```bash
nrdax info
nrdax info --format json
```

Shows dataset version, DOI (or "not minted"), technique count (reproduced vs
known-only), family and chain counts, the active source and fetch time, validation
issue count, and cache state.

## `nrdax version`

CLI, library, and schema versions. Does not load data.

```bash
nrdax version
nrdax version --format json
```

## `nrdax update`

Fetch the latest dataset into the local cache for offline use.

| Option | Description |
| --- | --- |
| `--source SPEC` | Where to fetch from (default `api`). |
| `--version V` | Require this dataset version, else exit `4`. |

```bash
nrdax update
nrdax update --source feed:https://example.com/nrdax-feed
```

The live API serves only the current version, so pin a specific version by pointing
`--source feed:...` at that release's static feed.

## `nrdax cache {info|clear}`

Inspect or clear the offline cache.

```bash
nrdax cache info
nrdax cache clear
```

The cache location honours `$NRDAX_CACHE_DIR`, then `$XDG_CACHE_HOME/nrdax`, then
`~/.cache/nrdax`. `nrdax info` and `nrdax cache info` always show the cached version
and fetch time, so stale data is never hidden.

## `nrdax schema`

The NRDAX vocabularies (families, statuses, fidelity classes, discovery origins,
reference kinds) and the technique/instance field set.

```bash
nrdax schema
nrdax schema --format json
```

## Machine-output compatibility

JSON and CSV field names are stable within a major package version. The STIX export
follows STIX 2.1 and is byte-compatible with the canonical NRDAX emitter. Breaking
changes to these are versioned and noted in the changelog.
