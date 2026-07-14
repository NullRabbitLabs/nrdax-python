# nrdax-python

**Programmatic and command-line access to NRDAX - the NullRabbit Decentralised
Attack indeX.**

[![CI](https://github.com/NullRabbitLabs/nrdax-python/actions/workflows/ci.yml/badge.svg)](https://github.com/NullRabbitLabs/nrdax-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/nrdax.svg)](https://pypi.org/project/nrdax/)
[![Python](https://img.shields.io/pypi/pyversions/nrdax.svg)](https://pypi.org/project/nrdax/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

`nrdax` is the standard open-source Python interface to NRDAX. If you have used
MITRE's `mitreattack-python`, this will feel familiar - but it is designed for the
NRDAX schema and semantics, not forced into an ATT&CK model.

- **Reusable library** with typed models and a small, predictable API.
- **Practical CLI** (`nrdax`) for search, retrieval, filtering, relationships,
  export, citation, change inspection, and offline use.
- **Zero required runtime dependencies** - the core library and CLI use only the
  Python standard library, so it installs cleanly and starts fast.
- **Offline once fetched** - run `nrdax update` (or load `--source api`) to pull the
  dataset into a local cache; subsequent commands work with no network. No data is
  bundled in the package.

## What is NRDAX?

NRDAX is NullRabbit's canonical, chain-agnostic registry of **techniques for attacks
on decentralised infrastructure** - validators, nodes, RPC services, networking and
gossip layers, consensus implementations, and related systems. Each technique has a
permanent id (`NRDAX-Tnnnn`), a mechanism description, a family, and evidence in the
form of chain-specific *instances*, plus links to advisories, CVEs, and research.

The public website (https://nrdax.com) is for human exploration. This package is for
**machines and researchers**: retrieve, search, filter, compare, cite, export, and
monitor NRDAX data programmatically.

## Install

```bash
pip install nrdax
```

Development version:

```bash
git clone https://github.com/NullRabbitLabs/nrdax-python
cd nrdax-python
pip install -e ".[dev]"
```

Python 3.10+ is supported.

## Quick start (CLI)

```bash
pip install nrdax
nrdax update                                  # fetch the latest dataset into the cache
nrdax search "rpc resource exhaustion"
nrdax get NRDAX-T0006
nrdax related NRDAX-T0006
nrdax cite NRDAX-T0006 --format bibtex
nrdax export --implementation agave --format json --output agave-attacks.json
```

Run `nrdax update` once to cache the dataset locally; after that every command works
offline. Before the first fetch, pass `--source api` to read the live registry.

## Quick start (Python)

```python
from nrdax import NRDAX

registry = NRDAX.from_api()                # live registry (or NRDAX.load() after `nrdax update`)
technique = registry.get("NRDAX-T0006")
print(technique.display, technique.family, technique.chains)

results = registry.search("rpc exhaustion")
for r in results[:5]:
    print(r.score, r.technique.id, r.technique.display)

related = registry.related("NRDAX-T0006")  # derived: family, chain, shared refs
coverage = registry.coverage               # technique x chain matrix
```

## Core CLI commands

| Command | Purpose |
| --- | --- |
| `nrdax search <query>` | Deterministic, explainable search across id/name/mechanism/chain/family/reference. |
| `nrdax get <id>` | One technique with instances, references, provenance (table / JSON / STIX). |
| `nrdax list [filters]` | Filter and list techniques (composable filters). |
| `nrdax related <id>` | Derived relationships (family siblings, shared chains, shared references). |
| `nrdax export [filters]` | Export a subset as JSON, CSV, or STIX 2.1. |
| `nrdax cite <id>` | Citation in text, Markdown, BibTeX, or CSL-JSON. |
| `nrdax changes` | Techniques since a date, or a diff between two dataset snapshots. |
| `nrdax info` | Dataset, source, and cache information. |
| `nrdax version` | CLI, library, and schema versions. |
| `nrdax update` | Fetch the latest dataset into the local cache. |
| `nrdax cache info|clear` | Inspect or clear the offline cache. |
| `nrdax schema` | The NRDAX vocabularies and field set. |

Full reference: [`docs/cli.md`](docs/cli.md).

## Supported data sources

Domain operations are independent of where the data came from. Select a source with
`--source` (CLI) or a classmethod (library):

| Source | CLI | Library | Notes |
| --- | --- | --- | --- |
| Local cache | `--source cache` | `NRDAX.from_cache()` | Written by `nrdax update`; the offline default. |
| Live API | `--source api[:URL]` | `NRDAX.from_api()` | `https://api.nrdax.com`. |
| Static feed | `--source feed:LOC` | `NRDAX.from_feed(loc)` | A directory or base URL of feed files. |
| Local file | `--source file:PATH` | `NRDAX.from_file(path)` | `registry.jsonl`, a bundle, or one technique. |
| STIX bundle | `--source stix:PATH` | `NRDAX.from_stix(path=...)` | Parses NRDAX STIX (lossy; see data-model). |
| In-memory | - | `NRDAX.from_memory([...])` | For tests and scripting. |

With no `--source`, the CLI uses the cached snapshot from a prior `nrdax update`; if
the cache is empty it errors and tells you to fetch first (no data is bundled).
`nrdax info` always shows which source and version you are using.

## Output formats

- **Terminal** tables and detail views (default).
- **JSON** (`--format json`) with stable field names.
- **CSV** (`--format csv`) where tabular output is meaningful.
- **STIX 2.1** (`--format stix`) for supported exports - byte-identical to the
  canonical NRDAX emitter, so identities round-trip.

## Versioning

Four versions are tracked independently:

- **Package version** (this repo, e.g. `0.1.0`).
- **CLI version** (equals the package version).
- **Dataset version** (from the loaded data, e.g. `v0.1-import`).
- **Schema version** (the NRDAX contract this client targets, e.g. `1.4`).

A package release does not imply the dataset changed, and vice versa. Pin an exact
dataset for reproducible research by keeping a feed snapshot and loading it with
`--source feed:/path`. See [`docs/data-model.md`](docs/data-model.md).

## Honest limitations

This client never invents fields or fabricates data. Where NRDAX lacks a capability,
the limitation is isolated and documented:

- No `implementation` or `surface` field exists in NRDAX; `--implementation` and
  surface search are **derived text heuristics**, clearly labelled as such.
- No asserted technique-to-technique relationships exist; `related` returns
  **derived** links (shared family / chain / reference).
- No DOI is minted yet; citations omit it rather than inventing one.
- No historical versioned releases are published; cross-version `changes` needs two
  snapshots you supply (`--from`/`--to`). `--since` works from `first_seen`.
- The static feed is not yet hosted at a stable public URL, so `nrdax update` pulls
  from the live API by default.

You can validate any dataset yourself: loading reports schema and integrity issues
(`nrdax info` shows the count, `--strict` fails on the first), so problems in the
underlying data can be found and corrected separately - the client never fabricates
or silently normalises data.

## Documentation

- [CLI reference](docs/cli.md)
- [Python API reference](docs/api.md)
- [Data-model guide](docs/data-model.md)
- Task guides: [`docs/guides/`](docs/guides/) - map a finding, retrieve by
  implementation, build a research dataset, export for a paper, cite, compare
  changes, import into another tool, work offline.
- Runnable [examples](examples/).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and
[GOVERNANCE.md](GOVERNANCE.md). Security issues: [SECURITY.md](SECURITY.md).

## License

The **source code** in this repository is licensed under **Apache-2.0** (see
[LICENSE](LICENSE)).

The **NRDAX dataset** - any data retrieved from NRDAX services (API, feed, cache) -
is a separate NullRabbit product with its own terms; this tool
grants no rights to the data. See [DATA_LICENSE.md](DATA_LICENSE.md) and
[NOTICE](NOTICE). "NRDAX" and "NullRabbit" are trademarks of NullRabbit Labs.

Maintained by [NullRabbit Labs](https://nullrabbit.ai).
