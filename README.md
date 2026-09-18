# O. Morikawa research database

Static, machine-readable research/CV database with a single-file searchable viewer.

## Source model

The database uses a **non-destructive layered upsert** model. The YAML files are the canonical merged state; the TeX/BibTeX/ResearchMap files are provenance-bearing inputs with different responsibilities.

1. `sources/cv_om.tex` is the shared author preamble/driver. Its zero-argument semantic macros (journal names, affiliations, `\OM`, etc.) are loaded by the TeX importers, so the database follows the same macro definitions used to compile the CV.
2. `sources/cv.tex`, `sources/publication.tex`, and `sources/presentation.tex` are the author's day-to-day content sources. New records can therefore appear in the database before ResearchMap, INSPIRE, or slide metadata are complete.
3. The TeX importers update fields owned by the corresponding TeX source and add genuinely new records. They do **not** delete records, Japanese text, URLs, external IDs, manual corrections, manual topics, or other enrichment merely because the current TeX omits them.
4. `sources/ref_om.bib` enriches scholarly publications with INSPIRE/BibTeX identity and bibliographic metadata. A provisional local publication ID is promoted to the INSPIRE BibTeX key when a matching entry later appears; the old ID is retained in `legacy_ids`.
5. `sources/rm_researchers.jsonl` is a second non-destructive upsert layer. A matching ResearchMap item enriches the existing record; an unmatched supported ResearchMap item is added as a source-native record. Local-only records, including collaborator talks, are retained.
6. `scripts/build.py` renders the merged YAML state into the self-contained viewer.

In short:

```text
cv_om.tex (shared preamble/macros)
          |
          +--------+----------------+
          v        v                v
cv.tex  publication.tex  presentation.tex
   \          |          /
    \---------+---------/----> canonical YAML --> searchable index.html
              ^       ^
              |       |
          BibTeX   ResearchMap / slides
```

The normal authoring workflow is therefore still LaTeX-first; external services can catch up later.

## Data and sources

- `data/profile.yaml` - root person entity and canonical public links.
- `data/publications.yaml` - scholarly papers/proceedings/theses/errata.
- `data/other_publications.yaml` - editorials/prefaces and meeting abstracts.
- `data/presentations.yaml` - conference talks, seminars, collaborator talks, posters, informal talks, journal clubs.
- `data/cv.yaml` - career, education, awards, grants, memberships, service, teaching, mentorship, visits, skills, activities, and ResearchMap-only CV records.
- `data/books.yaml` - online books/monographs.
- `data/software.yaml` - public repositories/software.
- `sources/cv_om.tex` - shared CV preamble/driver; zero-argument semantic macros are synchronized and reused by all TeX importers.
- `sources/cv.tex` - author-maintained CV source.
- `sources/publication.tex` - author-maintained publication/repository list.
- `sources/presentation.tex` - author-maintained presentation list, including collaborator talks.
- `sources/ref_om.bib` - INSPIRE-style BibTeX enrichment source.
- `sources/rm_researchers.jsonl` - ResearchMap export for bilingual/structured enrichment.

The canonical display fields use `*_en` and `*_ja`. English wording supplied by the author's TeX remains canonical where available. ResearchMap Japanese values populate `*_ja`; materially different ResearchMap English values are retained separately in `researchmap_*_en` rather than silently replacing the TeX wording.

## Normal workflow

Edit the usual TeX files, then run:

```bash
./build.sh
```

The build performs:

```text
cv_om.tex        -> shared zero-argument macro definitions
cv.tex           -> non-destructive CV/profile upsert
publication.tex  -> non-destructive publication/book/software upsert
presentation.tex -> non-destructive presentation upsert
ref_om.bib       -> bibliographic enrichment / INSPIRE-ID promotion
ResearchMap      -> match: enrich; no match: add; never prune local-only data
YAML             -> site/index.html -> index.html
```

`build.sh` optionally refreshes the bundled author sources from `${AUTHOR_CV_DIR}` (default: `~/Dropbox/riken_2026/template`) when those files exist, including `cv_om.tex` itself. Thus a change such as `\newcommand{\SciPostCore}{...}` is picked up on the next build without editing the Python importer. If that directory is absent, the repository remains buildable from the bundled `sources/` files.

To run individual layers:

```bash
python scripts/import_cv_tex.py sources/cv.tex --preamble sources/cv_om.tex
python scripts/import_publications_tex.py sources/publication.tex --preamble sources/cv_om.tex
python scripts/import_presentations_tex.py sources/presentation.tex --preamble sources/cv_om.tex
python scripts/import_bib.py sources/ref_om.bib -o data/publications.yaml --merge
python scripts/merge_researchmap.py sources/rm_researchers.jsonl
python scripts/build.py
```

There is intentionally no automatic prune step. Absence from a source is not evidence that a record should be deleted. Explicit deletion remains a deliberate edit to the canonical YAML.

## ResearchMap upsert

The ResearchMap merge now follows the same rule for every supported source category:

```text
matching canonical record -> enrich/update ResearchMap-owned metadata
no matching record         -> add source-native record
canonical/local-only record -> retain
```

Supported mappings include:

- `research_experience` -> `cv/career`
- `education` -> `cv/education`
- `awards` -> `cv/award`
- `research_projects` -> `cv/grant`
- `teaching_experience` -> `cv/teaching`
- `association_memberships` -> `cv/membership`
- `committee_memberships` -> `cv/professional_service`
- `academic_contribution` -> `cv/organizer`, `cv/activity`, or `cv/professional_service` according to the ResearchMap role
- `social_contribution` -> `cv/social_service`
- `media_coverage` -> media metadata / `cv/media_coverage`
- `research_interests`, `research_areas`, and `others` -> corresponding CV records
- `presentations`, `published_papers`, `misc`, and `works` -> presentations/publications/software records

A record may be related to more than one ResearchMap category. `researchmap_refs` retains all such source references while the backward-compatible `researchmap_id` / `researchmap_type` fields identify the primary ResearchMap source.

## Profile and thesis resources

The profile exposes the normal identity links plus:

- `CV (PDF)` -> `https://o-morikawa.github.io/cv/cv_om.pdf`
- `BibTeX` -> `https://o-morikawa.github.io/cv/ref_om.bib`

The PhD thesis record exposes its DOI together with:

- `Handle` -> `https://hdl.handle.net/2324/4474929`
- `PDF` -> `https://o-morikawa.github.io/cv/sci1362.pdf`

## Slides

ResearchMap presentation records with a `dataset.dataset_name` are linked to the corresponding public file under:

`https://o-morikawa.github.io/slides/<dataset_name>`

The presentation YAML retains `slides_file`, `slides_url`, `slides_repo_url`, and the original ResearchMap attachment URL when present. The standalone viewer shows a **Slides** link.

Current bundled state: 113 presentation records; 76 linked to ResearchMap; 64 with exact slide file names from ResearchMap.

## Build/viewer

```bash
python -m pip install -r requirements.txt
python scripts/build.py
```

`site/index.html` is self-contained: CSS, JavaScript, and all database records are embedded. It can be opened directly or placed as-is on GitHub Pages. `build.sh` copies it to the repository-root `index.html` as well.

The default view is `?kind=profile`. Filters are `type`, `kind`, and display language (`EN + JA`, `English`, `Japanese`). Search recursively covers every field in every record. Space-separated search terms use AND semantics: every term must occur somewhere in the same record.

`topics` are lightweight discovery tags rather than a controlled ontology. Automatic topic inference is additive; manually added YAML topics survive later TeX/BibTeX imports.

## Source-native identifiers

The database prefers a stable external identity when one exists without treating external services as destructive masters.

- INSPIRE-backed scholarly publications use the INSPIRE BibTeX key. A TeX-only paper may temporarily use a local ID; promotion retains the old ID in `legacy_ids`.
- ResearchMap-backed presentations use `researchmap:presentations:<ResearchMap numeric id>`.
- ResearchMap-only records in other entity families use `researchmap:<ResearchMap type>:<numeric id>`.
- Local records keep their local ID when an external ResearchMap link is merely enrichment rather than the canonical identity.

For a newly created ResearchMap presentation newer than the bundled JSONL export, the identity can still be attached immediately:

```bash
python scripts/attach_researchmap.py data/presentations.yaml \
  --match-id <current-or-legacy-id> \
  --researchmap-url https://researchmap.jp/o-morikawa/presentations/<id> \
  --slides-url https://o-morikawa.github.io/slides/<file>.pdf
python scripts/build.py
```

## v0.1.3

v0.1.3 synchronizes the shared `cv_om.tex` preamble and makes its zero-argument semantic macros a first-class input to all TeX importers. Argument-taking structural macros continue to be handled by dedicated parsers, so macro expansion cannot accidentally reinterpret commands such as `\Jcite`, `\DOI`, or `\ID`. The build remains non-destructive and reproducible from the bundled sources.

## v0.1.2

v0.1.2 makes the source pipeline uniformly non-destructive: `cv.tex` becomes a first-class input and ResearchMap changes from mostly enrichment-only matching to match-or-add upsert across all supported categories. It also adds the public CV/BibTeX links and the PhD thesis Handle/PDF links.
