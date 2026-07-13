# Import NRDAX into another tool

## STIX 2.1 (threat-intel platforms)

Export a STIX bundle and import it into a platform that speaks STIX:

```bash
nrdax export --format stix --output nrdax-stix.json
nrdax export --chain solana --format stix --output solana-stix.json
```

Each technique is a STIX `attack-pattern`. The NRDAX id is anchored in
`external_references` (`source_name: "nrdax"`), and NRDAX-specific fields are custom
properties: `x_nrdax_family`, `x_nrdax_status`, `x_nrdax_chains`. The bundle is
byte-identical to the canonical NRDAX emitter, and identities round-trip.

Validate before importing:

```python
import json
from nrdax.exporters import validate_bundle
errors = validate_bundle(json.load(open("nrdax-stix.json")))
assert errors == [], errors
```

If you have the optional `stix2` library installed (`pip install "nrdax[stix]"`), you
can additionally parse the bundle with the reference implementation.

## JSON / CSV (spreadsheets, databases, notebooks)

```bash
nrdax export --format json --output nrdax.json
nrdax export --format csv  --output nrdax.csv
nrdax export --format csv --csv-rows instances --output instances.csv
```

JSON preserves the full records and provenance; CSV flattens to a table (one row per
technique, or per instance with `--csv-rows instances`).

## Reading NRDAX STIX back

If another tool hands you an NRDAX STIX bundle, load it:

```python
from nrdax import NRDAX
reg = NRDAX.from_stix(path="incoming-stix.json")
```

Note this is **lossy**: STIX flattens instances, so identity and coarse fields are
recovered but per-instance detail is not. Use the feed/API/JSON for a full import.

## Custom pipelines

The library exposes the raw records (`registry.to_records()`) and a `Source` protocol
so you can plug NRDAX into your own ingestion without shelling out to the CLI. See the
[API reference](../api.md).
