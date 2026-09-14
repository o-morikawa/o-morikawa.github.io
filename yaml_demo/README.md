# YAML research database demo

`data/*.yaml` is the canonical public data. `site/index.html` is a generated, self-contained searchable view.

## Current contents

- `data/publications.yaml` — publications imported from the supplied INSPIRE-style BibTeX
- `scripts/import_bib.py` — reusable BibTeX → YAML importer
- `scripts/build.py` — combines all future `data/*.yaml` files into one standalone `site/index.html`

The publication `id` is the INSPIRE BibTeX citation key (for example `Morikawa:2025xjq`).

Affiliation periods are assigned primarily from the arXiv identifier:

- 2016-01 through 2021-03 → `Kyushu University`
- 2021-04 through 2024-03 → `Osaka University`
- 2024-04 onward → `RIKEN (iTHEMS)`

Two source records have no arXiv identifier: the 2021 erratum is tied to its original 2018 arXiv record, and the 2021 PhD thesis is assigned from its thesis institution/year. Each YAML record includes `affiliation_basis` so this is explicit.

## Rebuild the HTML

```bash
python scripts/build.py
```

Then open `site/index.html` directly. It contains the CSS, JavaScript, and generated database in one file.

## Re-import a BibTeX file

```bash
python scripts/import_bib.py /path/to/ref_om.bib -o data/publications.yaml
python scripts/build.py
```

Requires PyYAML.

## Future extension

Drop additional files such as `data/presentations.yaml`, `data/software.yaml`, or `data/books.yaml` into `data/`. Each record needs at least:

```yaml
- id: unique-id
  type: presentations
  title: Example title
```

After rebuilding, `index.html` automatically adds the new `type` to the filter and searches all fields in every record.
