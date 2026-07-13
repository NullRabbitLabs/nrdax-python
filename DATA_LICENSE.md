# NRDAX data licensing

**Short version:** the *code* in this repository is Apache-2.0 (see `LICENSE`). The
*NRDAX dataset* is a separate NullRabbit product with its own terms, which this
repository does not set and does not grant.

## Why this file exists

`nrdax-python` is open-source tooling that reads the public NRDAX dataset. Two
different things are licensed differently:

| Thing | License | Set by |
| --- | --- | --- |
| This library and CLI (the Python source) | Apache-2.0 | this repository (`LICENSE`) |
| The NRDAX dataset (technique records, the bundled snapshot, API responses) | Determined by NullRabbit, separately | NullRabbit Labs |

The bundled snapshot in `src/nrdax/data/snapshot/` is included purely as a
convenience for offline and reproducible use. Its presence in an Apache-2.0 code
repository does **not** place the NRDAX data under Apache-2.0.

## Known limitation (please read)

At the time of writing, NullRabbit has **not published an explicit public license
for the NRDAX dataset**, and the sibling NullRabbit source repositories are marked
`UNLICENSED`. This tool therefore makes no claim about how you may redistribute or
reuse the *data*. If you intend to redistribute NRDAX records, build a derived
dataset, or use the data commercially, confirm the dataset terms with NullRabbit
first.

Maintainers: this ambiguity should be resolved by publishing a clear dataset
license (for example CC-BY-4.0 for attribution-required reuse) before the dataset
is widely redistributed. Until then, treat the data as "all rights reserved by
NullRabbit unless stated otherwise."

## Citation

Whatever the eventual data license, please cite NRDAX records you rely on. The CLI
generates citations (`nrdax cite <id> --format bibtex|markdown|json`) using the
canonical URL and the dataset version. No DOI is minted yet, so citations omit it
rather than inventing one.

## Contact

Questions about dataset licensing: opensource@nullrabbit.ai / https://nullrabbit.ai.
