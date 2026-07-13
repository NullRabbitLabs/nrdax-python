# Build a research dataset

Assemble a filtered, reproducible subset of NRDAX for analysis.

## 1. Pin a dataset version

For reproducible research, pin the exact data. Either use the bundled snapshot (fixed
at a known version) or keep your own feed copy:

```bash
nrdax info                       # shows the dataset version you are on
nrdax update                     # fetch the current version into the cache
```

To pin precisely, save a feed and load it explicitly:

```bash
# once you have a feed directory or URL:
nrdax --source feed:/data/nrdax-v0.1-import list --format json > snapshot.json
```

## 2. Filter to your scope

```bash
nrdax export --chain solana --family compute_amp --reproduction-status reproduced \
  --format json --output solana-compute.json
```

Filters compose (AND). See `nrdax list --help` for the full set.

## 3. Choose columns

```bash
nrdax export --implementation agave \
  --fields id,name,family,reproduction_status,chains,first_seen \
  --format csv --output agave.csv
```

## In Python

```python
from nrdax import NRDAX
from nrdax.exporters import export_json

reg = NRDAX.load()
subset = reg.filter(reproduction_status="reproduced", chain="solana")

# Provenance is preserved: version and DOI travel with the records.
doc = export_json(subset, version=reg.version, doi=reg.doi,
                  fields=["id", "family", "reproduction_status", "chains"])
open("solana-reproduced.json", "w").write(doc)

print(f"{len(subset)} techniques from dataset {reg.version}")
```

## Record what you used

Always note the dataset version (`reg.version`) in your methods section so the subset
can be reproduced. The JSON export embeds it (`registry_version`).
