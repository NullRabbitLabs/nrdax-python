# Compare registry changes

## Source limitation (read first)

NRDAX does not yet publish historical versioned releases addressable by a version
number. So `nrdax changes --from-version X --to-version Y` is **not available** and
exits with a clear message. Instead:

- Use `--since DATE` to find techniques added since a date (derived from `first_seen`,
  which every record has).
- Use `--from <source> --to <source>` to diff two dataset snapshots you supply. This
  is a real diff, not a simulation.

## Techniques added since a date

```bash
nrdax changes --since 2026-07-01
nrdax changes --since 2026-07-01 --implementation agave
```

## Diff two snapshots

Keep a snapshot, fetch a newer one, and diff:

```bash
# Save today's dataset:
nrdax --source api list --format json > /dev/null   # (or export the feed)
nrdax update                                         # cache = current

# Later, after the dataset moves on:
nrdax changes --from cache --to api
```

Or diff two files you control:

```bash
nrdax changes --from file:old.jsonl --to file:new.jsonl --format json
```

## What the diff reports

- `technique_added`, `technique_removed`
- `name_changed`, `family_changed`, `status_changed`, `first_seen_changed`
- `reproduction_status_changed` (known becomes reproduced, or vice versa)
- `instance_added`, `instance_removed`, `chain_added`
- `advisory_added`, `brief_added`, `reference_removed`

## In Python

```python
from nrdax import NRDAX
from nrdax.changes import diff, since

reg = NRDAX.load()
recent = since(reg, "2026-07-01")
print(f"{len(recent)} techniques first seen since 2026-07-01")

old = NRDAX.from_file("old.jsonl")
new = NRDAX.from_file("new.jsonl")
cs = diff(old, new)
print(cs.counts_by_kind())
```

## Pinning for reproducible diffs

Keep dated copies of the feed (or the JSONL export) so you can always reconstruct a
diff between two exact points in time.
