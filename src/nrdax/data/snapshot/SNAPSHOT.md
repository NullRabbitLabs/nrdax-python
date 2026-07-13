# Bundled dataset snapshot

This directory holds the NRDAX dataset snapshot shipped inside the `nrdax` package
so `NRDAX.load()` works offline with zero configuration.

| field | value |
| --- | --- |
| dataset version | `v0.1-import` |
| techniques | 381 |
| DOI | none minted yet |
| captured | 2026-07-13 |
| source | the NRDAX static feed emitted by `nrdax-emit` (the canonical registry) |

Files: `index.json`, `registry.jsonl`, `families.json`, `coverage-matrix.json`.

This is a point-in-time snapshot for offline/reproducible use, not the live
dataset. Refresh to the current registry with `nrdax update` (writes a newer
snapshot into the local cache), or load the live API with `nrdax --source api ...`.
Pin an exact version for a paper or analysis by keeping a copy of a feed and
loading it with `nrdax --source feed:/path/to/feed ...`.
