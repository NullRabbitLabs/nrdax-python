# Python API reference

Import the public surface from the top-level package:

```python
from nrdax import NRDAX, Technique, Instance, ExternalReference
```

Everything below is importable from `nrdax` unless noted. The package is typed
(ships `py.typed`).

## `NRDAX` - the facade

The one object you load and query.

### Constructors

| Method | Description |
| --- | --- |
| `NRDAX.load(source=None, *, strict=False)` | Load from `source`, or the zero-config default (the cache from a prior `nrdax update`; raises `SourceError` if empty). |
| `NRDAX.from_cache(*, strict=False)` | The local cache. |
| `NRDAX.from_feed(location, *, strict=False)` | A static-feed directory or base URL. |
| `NRDAX.from_api(base_url=None, *, strict=False)` | The live read API. |
| `NRDAX.from_file(path, *, strict=False)` | A local `.jsonl`, bundle, or single technique. |
| `NRDAX.from_stix(path=None, *, bundle=None, strict=False)` | A STIX 2.1 bundle (lossy). |
| `NRDAX.from_memory(techniques, *, strict=False, version=..., doi=..., known_coverage=..., families=...)` | In-memory dicts or `Technique`s. |
| `NRDAX.from_source(source, *, strict=False)` | Any object implementing the `Source` protocol. |

`strict=True` raises `ValidationError` on the first error; the default collects
issues (see `.validate()`).

### Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `.version` | `str` | Dataset version. |
| `.doi` | `str \| None` | Dataset DOI, if minted. |
| `.schema_version` | `str` | The NRDAX schema/contract version this client targets. |
| `.techniques` | `list[Technique]` | All techniques, sorted by id. |
| `.known_coverage` | `list[KnownCoverage]` | Known-but-not-reproduced coverage. |
| `.families_vocab` | `list[str]` | The family vocabulary (fixed taxonomy plus any seen). |
| `.source_meta` | `SourceMeta \| None` | Where the data came from. |

### Methods

| Method | Returns | Description |
| --- | --- | --- |
| `get(id)` | `Technique` | By id (case-insensitive); raises `NotFoundError`. |
| `find(id)` | `Technique \| None` | Like `get` but returns `None`. |
| `search(query, *, limit=None, fields=None)` | `list[SearchResult]` | Ranked search. |
| `filter(**criteria)` | `list[Technique]` | Composable filters (see below). |
| `related(id)` | `RelatedResult` | Derived relationships. |
| `coverage` | `CoverageMatrix` | Cached derived matrix (property). |
| `families()` | `list[FamilyCount]` | Vocabulary with counts (incl. zero). |
| `chains()` | `list[str]` | Chains with a reproduced instance. |
| `instances(*, chain=None, discovery_origin=None)` | `list[tuple[str, Instance]]` | All instances, annotated with technique id. |
| `by_reference(ref_id)` | `list[Technique]` | Techniques carrying a reference id. |
| `validate()` | `list[ValidationIssue]` | Issues found while loading. |
| `to_records()` | `list[dict]` | Canonical dicts (round-trips the feed layout). |
| `to_release_dict()` | `dict` | The whole registry as one object. |

`len(registry)`, `iter(registry)`, and `"NRDAX-T0006" in registry` all work.

### `filter` criteria

`family`, `status`, `chain`, `fidelity`, `discovery_origin`, `reproduction_status`,
`reference` (+ `reference_contains=True`), `implementation` (derived heuristic),
`text`. Closed vocabularies (status, fidelity, discovery origin, reproduction status)
are validated and raise `InvalidArgumentError` on bad values.

```python
reg.filter(chain="solana", family="compute_amp", reproduction_status="reproduced")
```

## Models

### `Technique`

| Field | Type |
| --- | --- |
| `id` | `str` (`NRDAX-Tnnnn`) |
| `name` | `str` (stable slug) |
| `display_name` | `str \| None` |
| `mechanism` | `str` |
| `family` | `str` |
| `status` | `str` |
| `first_seen` | `str` (`YYYY-MM-DD`) |
| `instances` | `list[Instance]` |
| `external_references` | `list[ExternalReference]` |
| `provenance_note` | `str \| None` |
| `extra` | `dict` (preserved unknown fields) |

Derived (computed) properties: `display`, `url`, `chains`, `is_reproduced`,
`reproduction_status`, `strongest_fidelity`, `reference_ids`. Methods:
`iter_references()`, `references_of_kind(*kinds)`, `to_dict()`,
`Technique.from_dict(data, issues=None)`.

### `Instance`

`chain`, `primitive_id`, `bundle_ref`, `fidelity`, `discovery_origin`,
`external_references`, `extra`; property `fidelity_strength`.

### `ExternalReference`

`kind`, `id`, `url`, `extra`.

### Coverage

`CoverageMatrix(chains, cells, known)`, `CoverageCell(technique_id, chain,
strongest_fidelity, instance_count)`, `KnownCell(technique_id, chain)`. Call
`.to_dict()` on the matrix for the feed-compatible shape.

### `SearchResult`

`technique`, `score`, `matched_fields`.

### `RelatedResult`

`technique_id`, `family`, `family_siblings`, `chains` (list of `ChainNeighbours`),
`shared_references` (list of `SharedReference`), `instances`, `advisories`, `briefs`;
method `is_empty()`.

## Exporters

```python
from nrdax.exporters import export, export_json, export_csv, stix_bundle, stix_dumps, validate_bundle

export(techniques, "json", version=reg.version, doi=reg.doi)     # -> str
export(techniques, "csv", version=reg.version, fields=["id", "family"])
export(techniques, "stix", version=reg.version)
bundle = stix_bundle(list(reg), reg.version)                     # -> dict
text = stix_dumps(bundle)                                        # canonical string
errors = validate_bundle(bundle)                                 # [] if valid
```

## Citations

```python
from nrdax import cite
cite(registry, "NRDAX-T0006", style="bibtex", accessed="2026-07-13")
```

Styles: `text`, `markdown`, `bibtex`, `json` (CSL-JSON).

## Changes

```python
from nrdax.changes import since, diff
since(registry, "2026-07-01")                # list[Technique]
diff(old_registry, new_registry)             # ChangeSet
```

## Errors

`NrdaxError` (base), `NotFoundError`, `InvalidArgumentError`, `SourceError`,
`DataFormatError`, `SchemaVersionError`, `ValidationError`. Each carries a `.code`
and `.exit_code` (`ExitCode`). `ValidationIssue(locator, message, severity)` is the
non-fatal issue type.

## Custom sources

Implement the `Source` protocol - a `load()` returning a `RawDataset` - and pass it
to `NRDAX.from_source(...)`.

```python
from nrdax.sources import RawDataset, SourceMeta

class MySource:
    def load(self) -> RawDataset:
        return RawDataset(version="mine", doi=None, techniques=[...],
                          meta=SourceMeta(kind="custom", location="..."))
```
