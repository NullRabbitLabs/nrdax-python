# Retrieve attacks affecting an implementation

You run a specific client (say Agave, Geth, or a libp2p stack) and want the NRDAX
techniques that touch it.

## Important: implementation is a derived heuristic

NRDAX has **no first-class `implementation` field**. `--implementation` matches a
token across each technique's primitive ids, mechanism text, and references. It is a
best-effort text match, not an authoritative "affected implementations" list. Treat
the result as a starting point and confirm by reading the mechanism.

## CLI

```bash
nrdax list --implementation agave
nrdax list --implementation geth --format json
nrdax export --implementation agave --format json --output agave-attacks.json
```

Combine with real fields to narrow:

```bash
nrdax list --implementation agave --chain solana --reproduction-status reproduced
```

## By chain (a first-class field)

If you care about a chain rather than a client, use the schema-backed filter:

```bash
nrdax list --chain solana
```

## In Python

```python
from nrdax import NRDAX

reg = NRDAX.load()
hits = reg.filter(implementation="agave")
for t in hits:
    print(t.id, t.display, "|", ", ".join(t.chains))
```

## Confirm what actually matched

Because the match is heuristic, verify:

```python
for t in reg.filter(implementation="agave"):
    where = []
    for inst in t.instances:
        if "agave" in inst.primitive_id.lower():
            where.append(f"primitive {inst.primitive_id}")
    if "agave" in t.mechanism.lower():
        where.append("mechanism")
    print(t.id, "->", where or "reference text")
```
