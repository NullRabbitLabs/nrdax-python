# Support

## Getting help

- **Documentation:** start with the [README](README.md) and the [`docs/`](docs/)
  folder (CLI reference, Python API reference, data-model guide, and task-oriented
  guides).
- **Examples:** runnable scripts live in [`examples/`](examples/).
- **Questions and ideas:** open a [GitHub Discussion] or a `question`-labelled
  issue.
- **Bugs and feature requests:** use the issue templates.

## Before filing an issue

1. Run `nrdax version` and `nrdax info` and include the output.
2. Note whether the problem is with the *tool* or with the *data* it returned.
   Data-quality problems (a broken reference, an odd record) should be reported so
   the underlying dataset can be corrected; `nrdax`'s validation output
   (`nrdax --source <src> info`, or `--strict` to fail on the first issue) helps
   pinpoint them.
3. Provide a minimal reproduction: the exact command or a short Python snippet.

## What is in scope

`nrdax-python` is a read/query/export/citation interface for public NRDAX data.
Requests to change the NRDAX dataset itself, or to add producer/write features, are
out of scope here - raise those with NullRabbit directly.

## Commercial / dataset questions

For questions about the NRDAX dataset, its licensing, or commercial use, contact
**opensource@nullrabbit.ai** or see https://nullrabbit.ai.

[GitHub Discussions]: https://github.com/NullRabbitLabs/nrdax-python/discussions
