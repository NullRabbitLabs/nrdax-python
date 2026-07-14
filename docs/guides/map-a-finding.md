# Map a new finding to an existing technique

You have a finding (a report, a CVE, a mechanism description) and want to know
whether NRDAX already has a technique for it.

## 1. Search by what you know

```bash
nrdax search "unauthenticated rpc worker exhaustion" --explain
```

`--explain` shows which fields matched, so you can judge relevance. Search covers id,
name, mechanism, family, chain, primitive id, and references.

If you have an advisory or CVE id, look it up directly:

```bash
nrdax list --reference CVE-2025-1111
nrdax list --reference GHSA-aaaa-bbbb-cccc
```

## 2. Inspect the candidates

```bash
nrdax get NRDAX-T0006
```

Read the mechanism and the instances. Two techniques with similar names can have
different mechanisms - the mechanism is what defines a technique.

## 3. Check neighbours

```bash
nrdax related NRDAX-T0006
```

Family siblings and techniques sharing a chain or a reference help you confirm you
have the right one, or point you to a closer match.

## In Python

```python
from nrdax import NRDAX

reg = NRDAX.from_api()
for r in reg.search("worker pool exhaustion", limit=5):
    t = r.technique
    print(f"{r.score:6.1f}  {t.id}  {t.display}  (matched: {', '.join(r.matched_fields)})")

# If you have a CVE:
for t in reg.by_reference("CVE-2025-1111"):
    print(t.id, t.display)
```

## If nothing matches

NRDAX may not have your finding yet. This tool is read-only; propose new techniques
through NullRabbit's submission process (the registry's `/submissions` endpoint), not
through this client.
