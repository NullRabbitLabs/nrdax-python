# Governance

## Maintainership

`nrdax-python` is maintained by **NullRabbit Labs**. NullRabbit produces the NRDAX
dataset and stewards this open-source client for it.

- **Maintainers** review and merge pull requests, cut releases, and set the roadmap
  in line with the NRDAX product direction.
- Day-to-day decisions are made by the maintainers by lazy consensus on issues and
  pull requests.
- Significant changes (new required dependencies, breaking API changes, changes to
  the data-model mapping or the STIX byte-compatibility guarantee) require explicit
  maintainer approval and a `CHANGELOG` entry.

## Decision principles

1. **Fidelity to NRDAX.** The client mirrors the canonical schema and semantics. It
   never invents fields or silently normalises data. Where the source lacks a
   capability, we isolate and document the limitation.
2. **Stability of the public surface.** The Python API, CLI commands, machine
   output field names, and exit codes are a compatibility surface. Breaking changes
   are versioned and documented (see the versioning policy in `docs/data-model.md`).
3. **Separation of code and data.** The code is Apache-2.0; the NRDAX dataset is a
   separate NullRabbit product (see `DATA_LICENSE.md`).

## Becoming a maintainer

Contributors with a sustained track record of high-quality, in-scope contributions
may be invited to become maintainers by the existing maintainers.

## Releases

Releases follow semantic versioning for the package. Package, CLI, dataset, and
schema versions are tracked independently (see `docs/data-model.md`). Release
mechanics are in `CONTRIBUTING.md` and automated via GitHub Actions.

## Contact

opensource@nullrabbit.ai
