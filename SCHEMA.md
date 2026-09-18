# Data conventions

All YAML files contain a top-level list of records.

## Canonical merged-state policy

The database is a canonical **merged state**, not a destructive mirror of any one source.

Author-maintained sources:

- `sources/cv_om.tex` (shared preamble/driver and semantic macro definitions)
- `sources/cv.tex`
- `sources/publication.tex`
- `sources/presentation.tex`

External enrichment sources:

- `sources/ref_om.bib` (INSPIRE-style BibTeX)
- `sources/rm_researchers.jsonl` (ResearchMap)
- slide files/attachment metadata

All importers follow non-destructive upsert semantics:

1. Match an existing canonical record when possible.
2. Update only fields for which that source is responsible.
3. Add a new record when the source contains a genuinely unmatched item.
4. Preserve metadata owned by other sources and preserve records absent from the current source.
5. Never infer deletion from source absence.

English/basic wording supplied in the author's TeX is canonical where present. ResearchMap is authoritative for its own IDs/provenance and is primarily used to supply Japanese/bilingual structured metadata. Conflicting values are retained explicitly rather than silently reconciled.

For an explicit author correction that intentionally differs from a source date, `date_note` protects the canonical date. Literal TeX or ResearchMap values can be retained as `latex_start_date` / `latex_end_date` or `researchmap_date`, with `date_conflict: true` where applicable.


## Shared LaTeX preamble policy

`sources/cv_om.tex` is synchronized alongside the content files and is the source of truth for zero-argument semantic macros used by the author's CV ecosystem. The importers automatically read `\newcommand`, `\renewcommand`, and `\providecommand` definitions that take no arguments, including aliases such as journal names, affiliations, and `\OM`.

Argument-taking macros are not blindly expanded. Commands carrying structure or identifiers (for example `\Jcite`, `\Acite`, `\DOI`, `\HDL`, `\ID`, and `\JPScite`) remain under dedicated parsing rules. This separates semantic alias synchronization from schema-aware extraction. Unknown macros are left to the existing TeX cleanup/parser path rather than treated as data loss.

A change in the author's local `${AUTHOR_CV_DIR}/cv_om.tex` is copied to `sources/cv_om.tex` by `build.sh` when present, then used immediately by the TeX importers.

## Common fields

- `id`: stable public identifier.
- `legacy_ids`: previous IDs retained after identity promotion.
- `type`: top-level entity class (`profile`, `publications`, `presentations`, `cv`, `books`, `software`).
- `kind`: subtype within the entity class.
- `title_en`, `title_ja`: bilingual title/name for entity families using those fields.
- `event_en`, `event_ja`: bilingual event name.
- `organization_en`, `organization_ja`: bilingual institution/organization.
- `source`: provenance of the base/canonical record (`cv.tex`, `publication.tex`, `presentation.tex`, `researchmap`, etc.).
- `researchmap_id`, `researchmap_type`, `researchmap_url`: backward-compatible primary ResearchMap provenance.
- `researchmap_refs`: list of all ResearchMap source records attached to the canonical record. Each entry has `type`, `id`, and `url`. This permits, for example, an award to also carry related `media_coverage` provenance without replacing its award identity.

## Profile/root entity

- `type: profile`, `kind: profile`: the single root person entity.
- `identifiers`: ORCID, INSPIRE author ID, ResearchMap identifiers, and related stable identifiers.
- `urls`: canonical public links.
- `urls.cv_pdf`: public CV PDF.
- `urls.bibtex`: public BibTeX file.
- Flat compatibility fields (`website`, `orcid`, `github`, `inspire`, `researchmap`, `cv_pdf`, `bibtex`) may be retained for simple consumers.

The current affiliation is locally controlled; ResearchMap current-affiliation text is retained separately as `researchmap_affiliation_en` / `researchmap_affiliation_ja` rather than automatically replacing the profile value.

## CV records

Typical `kind` values include:

`career`, `education`, `award`, `grant`, `membership`, `organizer`, `professional_service`, `teaching`, `mentorship`, `visit`, `language`, `skill`, `social_service`, `activity`, `media_coverage`, `research_interest`, and `research_area`.

ResearchMap source categories are mapped semantically. An unmatched ResearchMap item is added with source-native ID `researchmap:<type>:<id>`. A matching local/TeX item retains its canonical local ID and receives ResearchMap provenance/enrichment.

A dated, individually identified peer review is an `activity`; a standing referee/reviewer appointment is `professional_service`. This prevents individual MathSciNet/SciPost reviews from being collapsed into standing reviewer roles.

## Grant/award/media links

- `urls.kaken`: KAKEN project page.
- `urls.award`: official award/source page.
- `urls.jps_hot_topics`, `urls.jps_butsuri`: coverage associated with the PTEP Editors' Choice record.
- `urls.media`: source URL for a related media-coverage record when applicable.

## Presentation-specific fields

- `role`: `self` or `collaborator`.
- `presenter`: actual speaker in the TeX-derived record.
- `presenters_en`, `presenters_ja`: ResearchMap presenter arrays when available.
- `invited`: Boolean.
- `start_date`, `end_date`: canonical ISO-like dates.
- `latex_start_date`, `latex_end_date`: literal TeX date when an explicit author correction protects another canonical date.
- `affiliation_period`: inferred affiliation period.
- `researchmap_date`: ResearchMap date when it differs from the canonical date; `date_conflict: true` marks the disagreement.
- `slides_file`: exact ResearchMap `dataset.dataset_name`.
- `slides_url`: direct GitHub Pages slide URL.
- `slides_repo_url`: corresponding GitHub repository file URL.
- `researchmap_attachment_url`: original ResearchMap attachment URL.

## Publication-specific fields

- `title`: canonical English title for scholarly publications generated/enriched through BibTeX/INSPIRE.
- `title_en`: canonical English title in locally classified publication families such as editorials/meeting abstracts.
- `authors`, `authors_latex`: canonical/enrichment author representations.
- `arxiv`, DOI, journal metadata, `inspire_bibkey`, and links are retained when available.
- `bibtex_source`: BibTeX provenance.
- `topics`: lightweight discovery tags, not a controlled ontology. Automatic inference is additive and does not remove manual topics.

The PhD thesis (`hdl: 2324/4474929`) carries:

- `urls.handle: https://hdl.handle.net/2324/4474929`
- `urls.pdf: https://o-morikawa.github.io/cv/sci1362.pdf`

ResearchMap `published_papers` matching is performed across both `publications.yaml` and `other_publications.yaml`, so a locally classified editorial such as a preface is enriched in place rather than duplicated as a generic paper.

## Bilingual/provenance policy

1. Preserve Japanese ResearchMap text in `*_ja`.
2. Preserve author-supplied English TeX wording as the canonical English value where available.
3. If ResearchMap English differs materially, retain it in `researchmap_*_en`.
4. Retain relevant source-specific dates/values when sources disagree.
5. Do not invent Japanese translations when the source does not supply them.

## Source-native ID policy

1. **INSPIRE-backed scholarly publications**: INSPIRE BibTeX key verbatim, e.g. `Morikawa:2025xjq`.
2. **TeX-only scholarly publications**: local `publication-...` ID until an INSPIRE key becomes available; promotion retains `legacy_ids`.
3. **ResearchMap-backed presentations**: `researchmap:presentations:<numeric id>`.
4. **ResearchMap-only records in other families**: `researchmap:<ResearchMap type>:<numeric id>`.
5. A pre-existing local record enriched by ResearchMap normally retains its local canonical ID.
6. Slide URLs are metadata, not identity sources.
