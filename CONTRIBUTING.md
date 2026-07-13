# Contributing to nrdax-python

Thanks for your interest. This repository is the open-source Python interface to
NRDAX, maintained by NullRabbit Labs. Contributions of all sizes are welcome:
bug reports, docs, examples, new data-source adapters, exporters, and citation
styles.

## Scope

This project is a **read, query, export, citation, and analysis** interface for the
public NRDAX dataset. It is intentionally **not** a producer: it does not generate
techniques, reproduce CVEs, or write back to NRDAX. Please keep PRs within that
scope (see the non-goals in the README). New capabilities that fit the roadmap
(more source adapters, TAXII consumption, knowledge-graph exports, additional
citation styles) are welcome; speak to us in an issue first for larger changes.

## Development setup

```bash
git clone https://github.com/NullRabbitLabs/nrdax-python
cd nrdax-python
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## The checks we run (and you should too)

```bash
ruff check src tests        # lint
ruff format --check src tests
mypy                        # type-check
pytest                      # unit tests (no network)
pytest -m integration       # optional: hits the live API (skips if unreachable)
```

CI runs the same on Python 3.10-3.13. A PR must be green.

## Ground rules that are easy to miss

1. **Do not invent NRDAX fields.** The models mirror the canonical schema exactly.
   If NRDAX lacks a capability, isolate and document the limitation (as we already
   do for `implementation`, `surface`, relationships, DOI, and schema version).
   Never fabricate or silently normalise data.
2. **Determinism.** Search ranking, exports, and STIX output must be byte-stable:
   same input, same output. No wall-clock or randomness in serialized output.
   The STIX exporter is byte-identical to the canonical NRDAX emitter and has a
   golden test - keep it that way.
3. **Preserve unknown fields.** Parsing keeps unrecognised canonical fields in
   `extra` and round-trips them. Do not drop data.
4. **Zero required runtime dependencies.** The core library and CLI use only the
   standard library. New required dependencies need a strong justification; prefer
   an optional extra.
5. **House style:** hyphens, not em dashes, in user-facing text.

## Tests first for behaviour changes

New behaviour needs a test. Use the small deterministic fixtures in `tests/` and
`MemorySource` for synthetic data; keep the default suite offline.

## Commit and PR

- Keep PRs focused; one logical change each.
- Update `CHANGELOG.md` under "Unreleased".
- Update docs/examples when you change public behaviour.
- Sign-off is not required, but by contributing you agree your contribution is
  licensed under Apache-2.0.

## Reporting security issues

Do not open a public issue for vulnerabilities. See `SECURITY.md`.
