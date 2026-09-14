# O. Morikawa research database (v5)

Static, machine-readable research/CV database with a single-file searchable viewer.

## Data

- `data/publications.yaml` - INSPIRE-backed papers/proceedings/thesis/erratum; INSPIRE BibTeX key is the record ID.
- `data/other_publications.yaml` - editorial/preface and JPS meeting abstracts not covered by the INSPIRE BibTeX import.
- `data/presentations.yaml` - conference talks, seminars, collaborator talks, posters, local/informal talks, journal clubs; ResearchMap bilingual metadata and slide links are merged when available.
- `data/cv.yaml` - career, education, awards, grants, memberships, service, teaching, mentorship, visits, skills and activities, enriched with ResearchMap Japanese/English metadata.
- `data/books.yaml` - online books/monographs.
- `data/software.yaml` - public repositories/software.
- `sources/rm_researchers20260828.jsonl` - supplied ResearchMap export used for the bilingual merge.

The canonical display fields use `*_en` and `*_ja`. ResearchMap source variants are retained in explicit `researchmap_*` fields when they differ from the existing CV/LaTeX wording rather than silently overwriting the other source.

## Slides

ResearchMap presentation records with a `dataset.dataset_name` are linked to the corresponding public file under:

`https://o-morikawa.github.io/slides/<dataset_name>`

The presentation YAML retains the file name (`slides_file`), direct PDF URL (`slides_url`), GitHub repository URL (`slides_repo_url`), and ResearchMap attachment URL when present. The standalone viewer shows a **Slides** link.

Current import: 75 presentation records matched to ResearchMap; 63 have exact slide file names from the ResearchMap export.

## ResearchMap merge

```bash
python scripts/merge_researchmap.py
python scripts/build.py
```

Or supply another JSONL export explicitly:

```bash
python scripts/merge_researchmap.py /path/to/rm_researchersYYYYMMDD.jsonl
python scripts/build.py
```

## Build

```bash
python -m pip install -r requirements.txt
python scripts/build.py
```

The output `site/index.html` is self-contained: CSS, JavaScript and all database records are embedded. It can be opened directly or placed as-is on GitHub Pages.

Filters: `type`, `kind`, and display language (`EN + JA`, `English`, `Japanese`). The search box recursively searches every field in every record.
