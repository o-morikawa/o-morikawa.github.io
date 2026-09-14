# O. Morikawa research database (v4)

Static, machine-readable research/CV database with a single-file searchable viewer.

## Data

- `data/publications.yaml` - INSPIRE-backed papers/proceedings/thesis/erratum; INSPIRE BibTeX key is the record ID.
- `data/other_publications.yaml` - editorial/preface and JPS meeting abstracts not covered by the INSPIRE BibTeX import.
- `data/presentations.yaml` - conference talks, seminars, collaborator talks, posters, local/informal talks, journal clubs.
- `data/cv.yaml` - career, education, awards, grants, memberships, service, teaching, mentorship, visits, skills and activities.
- `data/books.yaml` - online books/monographs.
- `data/software.yaml` - public repositories/software.

Every title/event-like field is bilingual-ready using `*_en` and `*_ja`. The supplied English LaTeX/CV sources populate English fields. Japanese fields are left `null` rather than guessed when no Japanese source is available.

## ResearchMap

The supplied ResearchMap ZIP is encrypted. See `RESEARCHMAP_IMPORT_STATUS.md`. Once its password is available, the Japanese originals can be merged into the matching records while retaining the English translations.

## Build

```bash
python -m pip install -r requirements.txt
python scripts/build.py
```

The output `site/index.html` is self-contained: CSS, JavaScript and all database records are embedded. It can be opened directly or placed as-is on GitHub Pages.

Filters: `type`, `kind`, and display language (`EN + JA`, `English`, `Japanese`). The search box recursively searches every field in every record.
