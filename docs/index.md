# nrdax-python

The standard open-source Python interface to **NRDAX** - the NullRabbit
Decentralised Attack indeX. It gives researchers, analysts, tool builders,
operators, and automated systems a reusable library and a practical CLI to
retrieve, search, filter, compare, cite, export, and monitor NRDAX data.

If you have used MITRE's `mitreattack-python`, the shape will be familiar; the
schema and semantics are NRDAX's own.

## Install

```bash
pip install nrdax
```

## First run

```bash
nrdax update                       # optional: fetch the latest into the cache
nrdax search "rpc resource exhaustion"
nrdax get NRDAX-T0006
nrdax cite NRDAX-T0006 --format bibtex
```

```python
from nrdax import NRDAX
registry = NRDAX.load()
technique = registry.get("NRDAX-T0006")
```

## Where to go next

- **[CLI reference](cli.md)** - every command, option, format, and exit code.
- **[Python API reference](api.md)** - the public classes and methods.
- **[Data model](data-model.md)** - identifiers, techniques, instances, families,
  relationships, reproduction status, STIX, and the versioning policy.
- **Guides** - task-oriented walkthroughs for common workflows.

## Design principles

- **Fidelity to NRDAX.** Models mirror the canonical schema. The tool never invents
  fields or silently discards data; where the source lacks a capability, the
  limitation is isolated and documented.
- **Determinism.** Search, exports, and STIX output are byte-stable. The STIX export
  is byte-identical to the canonical NRDAX emitter.
- **Offline-first.** A bundled snapshot means everything works with no network; the
  cache lets you pin data for reproducible research.
- **Zero required dependencies.** The core library and CLI use only the standard
  library.
