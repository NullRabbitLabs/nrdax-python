"""Generate citations in every supported style.

Run:  python examples/04_citations.py
"""

from __future__ import annotations

from nrdax import NRDAX, cite


def main() -> None:
    registry = NRDAX.from_api()
    tid = "NRDAX-T0006"

    for style in ("text", "markdown", "bibtex", "json"):
        print(f"----- {style} -----")
        print(cite(registry, tid, style=style, accessed="2026-07-13"))
        print()

    print("Note: no DOI is minted for this dataset, so it is omitted, not invented.")


if __name__ == "__main__":
    main()
