# O. Morikawa research database

Static, machine-readable research/CV database with a single-file searchable viewer.

## Source model

The database uses a **non-destructive layered update** model.

1. `sources/publication.tex` and `sources/presentation.tex` are the author's day-to-day, fast-moving source files. They can describe a new paper/talk before external databases are complete.
2. The TeX importers upsert those records into YAML. Existing ResearchMap IDs, Japanese metadata, slide links, manual corrections, manual topics, and other enrichment fields are preserved.
3. `sources/ref_om.bib` enriches scholarly publications with INSPIRE/BibTeX identity and bibliographic metadata. A provisional local publication ID is promoted to the INSPIRE BibTeX key when a matching BibTeX entry later appears; the old ID is retained in `legacy_ids`.
4. `sources/rm_researchers.jsonl` enriches matching records with bilingual ResearchMap metadata, source-native ResearchMap IDs, and slide attachment metadata. Records that do not exist in ResearchMap, including collaborator talks, remain in the database.
5. `scripts/build.py` renders the merged YAML state into the self-contained viewer.

The YAML files are therefore the **canonical merged state**, while the TeX/BibTeX/ResearchMap files are provenance-bearing inputs with different responsibilities.

## Data

- `data/profile.yaml` - root person entity. Canonical external identifiers/links (Website, ORCID, GitHub, INSPIRE, researchmap) live here.
- `data/publications.yaml` - scholarly papers/proceedings/thesis/errata. INSPIRE-backed records use the INSPIRE BibTeX key as the canonical ID; TeX-only records may temporarily use a local provisional ID.
- `data/other_publications.yaml` - editorial/preface and JPS meeting abstracts.
- `data/presentations.yaml` - conference talks, seminars, collaborator talks, posters, local/informal talks, journal clubs; ResearchMap bilingual metadata and slide links are merged when available.
- `data/cv.yaml` - career, education, awards, grants, memberships, service, teaching, mentorship, visits, skills and activities, enriched with ResearchMap Japanese/English metadata.
- `data/books.yaml` - online books/monographs.
- `data/software.yaml` - public repositories/software.
- `sources/publication.tex` - author-maintained publication/repository list.
- `sources/presentation.tex` - author-maintained presentation list, including collaborator talks.
- `sources/ref_om.bib` - INSPIRE-style BibTeX enrichment source.
- `sources/rm_researchers.jsonl` - ResearchMap export used for bilingual/structured enrichment.

The canonical display fields use `*_en` and `*_ja`. ResearchMap source variants are retained in explicit `researchmap_*` fields when they differ from the existing CV/LaTeX wording rather than silently overwriting the other source.

## Normal workflow

Edit the two TeX files as usual, then run:

```bash
./build.sh
```

The build performs:

```text
publication.tex  -> non-destructive YAML upsert
presentation.tex -> non-destructive YAML upsert
ref_om.bib       -> publication enrichment / INSPIRE-ID promotion
ResearchMap      -> bilingual metadata / ResearchMap IDs / slide metadata
YAML             -> site/index.html -> index.html
```

The TeX importers do **not** delete YAML records merely because a record is absent from the current TeX file. This is deliberate: updates are safe by default, and external/manual enrichment is not destroyed. Explicit deletions should be made deliberately in YAML if needed.

To run only one layer:

```bash
python scripts/import_publications_tex.py sources/publication.tex
python scripts/import_presentations_tex.py sources/presentation.tex
python scripts/import_bib.py sources/ref_om.bib -o data/publications.yaml --merge
python scripts/merge_researchmap.py sources/rm_researchers.jsonl
python scripts/build.py
```

## Slides

ResearchMap presentation records with a `dataset.dataset_name` are linked to the corresponding public file under:

`https://o-morikawa.github.io/slides/<dataset_name>`

The presentation YAML retains the file name (`slides_file`), direct PDF URL (`slides_url`), GitHub repository URL (`slides_repo_url`), and ResearchMap attachment URL when present. The standalone viewer shows a **Slides** link.

Current import: 75 presentation records matched to ResearchMap; 63 have exact slide file names from the ResearchMap export.

## ResearchMap merge

The ResearchMap export can be refreshed only when convenient. A stale export does not prevent new TeX records from appearing in the database.

```bash
python scripts/merge_researchmap.py
python scripts/build.py
```

Or supply another JSONL export explicitly:

```bash
python scripts/merge_researchmap.py /path/to/rm_researchersYYYYMMDD.jsonl
python scripts/build.py
```

## Build/viewer

```bash
python -m pip install -r requirements.txt
python scripts/build.py
```

The output `site/index.html` is self-contained: CSS, JavaScript and all database records are embedded. It can be opened directly or placed as-is on GitHub Pages.

The default view is `?kind=profile`. Opening `index.html` without a query selects the root profile record and rewrites the URL to that state. Selecting `All kinds` writes `?kind=` explicitly, so a reload does not fall back to the profile.

Filters: `type`, `kind`, and display language (`EN + JA`, `English`, `Japanese`). The search box recursively searches every field in every record. Space-separated search terms use AND semantics: every term must occur somewhere in the same record.

`topics` are lightweight discovery tags rather than a controlled ontology. Automatic topic inference is additive: manually added topics in YAML survive later TeX/BibTeX imports.

## Source-native identifiers

The database prefers source-native IDs once they exist.

- Publications: INSPIRE BibTeX key after INSPIRE/BibTeX enrichment. A TeX-only publication can temporarily keep a local ID.
- Presentations with a ResearchMap record: `researchmap:presentations:<ResearchMap numeric id>`.
- Old/generated IDs are preserved in `legacy_ids` when an ID is promoted.

For a newly created ResearchMap presentation that is newer than the latest JSONL export, attach the URL immediately:

```bash
python scripts/attach_researchmap.py data/presentations.yaml \
  --match-id <current-or-legacy-id> \
  --researchmap-url https://researchmap.jp/o-morikawa/presentations/<id> \
  --slides-url https://o-morikawa.github.io/slides/<file>.pdf
python scripts/build.py
```

If `--slides-url` is omitted, only the ResearchMap identity/link is attached; the slide can be added later without changing the record ID.
