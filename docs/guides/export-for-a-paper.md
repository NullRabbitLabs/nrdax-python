# Export records for a paper

## Pick the records

```bash
nrdax export --family consensus_abuse --format csv \
  --fields id,display,family,reproduction_status,chains,first_seen \
  --output paper-table.csv
```

The CSV is ready for a spreadsheet or a LaTeX table tool. List-valued fields (like
`chains`) are joined with `;`.

## Cite each record

Generate a BibTeX entry per technique:

```bash
for id in NRDAX-T0006 NRDAX-T0099 NRDAX-T0261; do
  nrdax cite "$id" --format bibtex
  echo
done > refs.bib
```

Or CSL-JSON for reference managers (Zotero, Pandoc):

```bash
nrdax cite NRDAX-T0006 --format json
```

Citations use the canonical URL and the dataset version. No DOI is minted yet, so
entries omit it - do not add one by hand.

## Record the dataset version

Put the dataset version in your methods section:

```bash
nrdax info --format json | python -c "import json,sys;print(json.load(sys.stdin)['dataset_version'])"
```

## In Python (build a table + a .bib together)

```python
from nrdax import NRDAX, cite

reg = NRDAX.load()
rows = reg.filter(family="consensus_abuse")

with open("refs.bib", "w") as bib:
    for t in rows:
        bib.write(cite(reg, t.id, style="bibtex") + "\n\n")

print(f"{len(rows)} records from NRDAX {reg.version}")
```
