# Data conventions

All YAML files contain a top-level list of records.

## Layered source policy

The database is a canonical **merged state**, not a destructive mirror of one external service.

- `sources/publication.tex` and `sources/presentation.tex` are the fast-moving author-maintained layer. Their importers upsert current English/basic records and add new provisional records immediately.
- TeX import is non-destructive: fields outside the TeX importer's responsibility are retained, and records absent from TeX are not automatically deleted.
- INSPIRE-style BibTeX enriches scholarly publications and can promote a provisional local ID to the INSPIRE BibTeX key.
- ResearchMap enriches matching records with Japanese/bilingual metadata, ResearchMap identity/provenance, and slide attachment metadata. It does not delete collaborator talks or other TeX-only records.
- Manual YAML metadata, especially discovery `topics`, is preserved across later imports.

For an explicit author correction that intentionally differs from the literal TeX date, `date_note` protects the canonical presentation date. The literal parsed value is retained as `latex_start_date` / `latex_end_date` when it differs.

## Common fields

- `id`: stable public identifier. INSPIRE-backed scholarly publications use the INSPIRE BibTeX key verbatim; ResearchMap-backed presentations use the ResearchMap record ID.
- `legacy_ids`: previous local/canonical IDs retained when an external source-native ID is promoted.
- `type`: top-level entity class (`profile`, `publications`, `presentations`, `cv`, `books`, `software`).
- `kind`: subtype within the entity class.
- `title_en`, `title_ja`: English and Japanese title/name where the entity family uses bilingual title fields.
- `event_en`, `event_ja`: bilingual meeting/seminar/event name.
- `organization_en`, `organization_ja`: bilingual institution/organization name where relevant.
- `source`: provenance of the base record, normally `publication.tex` or `presentation.tex` for records maintained in those lists.
- `researchmap_id`, `researchmap_type`: ResearchMap provenance when a record was matched/imported.

## Profile/root entity

- `type: profile`, `kind: profile`: the single root person entity.
- `identifiers`: machine-readable stable identifiers (ORCID, INSPIRE author id, researchmap slug/internal id).
- `urls`: canonical public links (Website, ORCID resolver, GitHub, INSPIRE, researchmap).
- Flat compatibility fields (`website`, `orcid`, `github`, `inspire`, `researchmap`) are retained for simple consumers.

## Grant/award links

- `urls.kaken`: KAKEN project page for the corresponding grant number.
- `urls.award`: official award/source page when supplied.
- `urls.jps_hot_topics`, `urls.jps_butsuri`: article coverage associated with the PTEP Editors' Choice record.

## Presentation-specific fields

- `role`: `self` or `collaborator`.
- `presenter`: actual speaker in the TeX/CV-derived record.
- `presenters_en`, `presenters_ja`: ResearchMap presenter/author arrays when available.
- `invited`: Boolean.
- `start_date`, `end_date`: canonical ISO-like dates.
- `latex_start_date`, `latex_end_date`: literal TeX-parsed date retained only when an explicit author correction protects a different canonical date.
- `affiliation_period`: inferred from event date using the requested career periods.
- `researchmap_url`: ResearchMap presentation record.
- `researchmap_date`: retained when the ResearchMap date differs from the canonical/TeX date; `date_conflict: true` marks this explicitly.
- `slides_file`: exact ResearchMap `dataset.dataset_name`.
- `slides_url`: direct GitHub Pages PDF URL under `https://o-morikawa.github.io/slides/`.
- `slides_repo_url`: corresponding GitHub repository file URL.
- `researchmap_attachment_url`: original ResearchMap attachment URL.

## Publication-specific fields

- `title`: canonical English scholarly-publication title; the LaTeX list is the fast-moving title source.
- `authors`: canonical author list. TeX-only provisional records use the LaTeX author list; BibTeX may later enrich it.
- `authors_latex`: retained when the LaTeX author rendering differs from enriched BibTeX authors.
- `arxiv`, DOI, journal metadata, `inspire_bibkey`, and links are retained when present.
- `bibtex_source`: BibTeX enrichment provenance.
- `topics`: lightweight discovery tags, not a controlled ontology. Automatic inference is additive and never removes manually added YAML topics.

## Bilingual/provenance policy

1. Preserve Japanese ResearchMap text in `*_ja`.
2. Preserve supplied English TeX/CV wording as the base/current English value when appropriate.
3. If ResearchMap's English text differs materially, retain it in a separate `researchmap_*_en` field.
4. Do not silently resolve disagreements between sources; store the conflicting source value separately where the distinction matters.
5. Do not invent Japanese translations when the source does not supply them.

## Source-native ID policy

IDs are promoted to the most stable canonical external record when one exists.

1. **INSPIRE-backed scholarly publications**: use the INSPIRE BibTeX key verbatim, e.g. `Morikawa:2025xjq`.
2. **TeX-only scholarly publications**: use a local `publication-...` ID until an INSPIRE BibTeX key becomes available. Promotion retains the local ID in `legacy_ids`.
3. **ResearchMap-backed presentations**: derive the ID from the public ResearchMap record URL:
   `https://researchmap.jp/o-morikawa/presentations/54946770`
   -> `researchmap:presentations:54946770`.
4. Presentation slide URLs are metadata, not the identity source. They are stored in `slides_url`, `slides_file`, and `slides_repo_url`.
5. Records without a canonical external record keep their local ID until such a record becomes available.
