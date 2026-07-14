# Create a citation

```bash
nrdax cite NRDAX-T0006                    # plain text
nrdax cite NRDAX-T0006 --format markdown
nrdax cite NRDAX-T0006 --format bibtex
nrdax cite NRDAX-T0006 --format json      # CSL-JSON
```

## What goes into a citation

- **Author**: NullRabbit Labs
- **Title**: the technique's display name
- **Container**: NRDAX - NullRabbit Decentralised Attack indeX
- **Version**: the dataset version you loaded
- **Number**: the NRDAX id
- **URL**: the canonical permanent URL (`https://nrdax.com/techniques/<id>`)
- **Access date**: today by default (`--accessed YYYY-MM-DD` to fix it)
- **DOI**: included only if one is minted. None is minted yet, so it is omitted -
  never fabricated.

## Reproducible access date

For a paper, fix the access date so the citation is stable:

```bash
nrdax cite NRDAX-T0006 --format bibtex --accessed 2026-07-13
```

## In Python

```python
from nrdax import NRDAX, cite

reg = NRDAX.from_api()
print(cite(reg, "NRDAX-T0006", style="markdown", accessed="2026-07-13"))
```

## When a DOI arrives

Once NullRabbit mints a DOI for a release, load that release (its `index.json`
carries the `doi`) and citations will include it automatically. Loading current data
without a DOI simply omits it.
