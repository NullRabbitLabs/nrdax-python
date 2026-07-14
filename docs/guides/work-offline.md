# Work offline with a pinned dataset

## Fetch once, then work offline

`nrdax` bundles no dataset - fetch it once into a local cache, and from then on every
command works with no network:

```bash
pip install nrdax
nrdax update                   # fetches the live dataset into the local cache
nrdax get NRDAX-T0006          # now offline, served from the cache
```

`NRDAX.load()` uses that cache by default. Before the first `nrdax update`, read the
live registry directly with `--source api` (`NRDAX.from_api()`).

## Acquire the current dataset once, then go offline

```bash
nrdax update                   # fetches the live dataset into the local cache
# ... later, with no network:
nrdax search "rpc exhaustion"  # uses the cache
nrdax info                     # shows the cached version and fetch time
```

After `nrdax update`, the CLI uses the cache by default. Stale data
is never hidden - `nrdax info` and `nrdax cache info` always show the version and when
it was fetched.

## Pin an exact version for reproducible research

Keep a copy of a static feed (a directory of `index.json`, `registry.jsonl`,
`coverage-matrix.json`, `families.json`) and load it explicitly:

```bash
nrdax --source feed:/data/nrdax-v0.1-import get NRDAX-T0006
```

In Python:

```python
from nrdax import NRDAX
reg = NRDAX.from_feed("/data/nrdax-v0.1-import")
assert reg.version == "v0.1-import"
```

This guarantees the same records every run, regardless of what the live dataset does.

## Cache location and management

The cache lives under `$NRDAX_CACHE_DIR`, else `$XDG_CACHE_HOME/nrdax`, else
`~/.cache/nrdax`.

```bash
nrdax cache info
nrdax cache clear
```

## Air-gapped setup

On a networked machine:

```bash
nrdax export --format json --output nrdax.json     # or copy a feed directory
```

On the air-gapped machine:

```bash
nrdax --source file:nrdax.json get NRDAX-T0006
```
