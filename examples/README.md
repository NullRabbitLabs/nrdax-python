# Examples

Runnable scripts demonstrating the library. Most read the live registry via
`NRDAX.from_api()`; run `nrdax update` first if you'd rather work from the local cache
offline. Example 07 runs fully offline against the repo's feed fixture.

```bash
pip install -e .          # or: pip install nrdax
python examples/01_quickstart.py
```

| Script | Shows |
| --- | --- |
| `01_quickstart.py` | Load the dataset and retrieve a technique. |
| `02_search_and_filter.py` | Deterministic search and composable filters. |
| `03_export_subset.py` | Export a filtered subset as JSON and CSV. |
| `04_citations.py` | Citations in text, Markdown, BibTeX, and CSL-JSON. |
| `05_stix_export.py` | STIX 2.1 export, validation, and identity round-trip. |
| `06_relationships_and_coverage.py` | Derived relationships and the coverage matrix. |
| `07_offline_pinned.py` | Pin a dataset from a feed and diff two snapshots. |

Each script is self-contained and prints its output. Scripts `03` and `05` write a
couple of files into the current directory.
