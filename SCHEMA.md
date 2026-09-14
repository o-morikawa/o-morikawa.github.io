# Data conventions

All YAML files contain a top-level list of records.

Common fields:

- `id`: stable public identifier. INSPIRE-backed scholarly publications use the INSPIRE BibTeX key verbatim.
- `type`: top-level entity class (`profile`, `publications`, `presentations`, `cv`, `books`, `software`).
- `kind`: subtype within the entity class.
- `title_en`, `title_ja`: English and Japanese title/name.
- `event_en`, `event_ja`: bilingual meeting/seminar/event name.
- `organization_en`, `organization_ja`: bilingual institution/organization name where relevant.
- `source`: provenance of the base record.
- `researchmap_id`, `researchmap_type`: ResearchMap provenance when a record was matched/imported.

Profile/root-entity fields:

- `type: profile`, `kind: profile`: the single root person entity.
- `identifiers`: machine-readable stable identifiers (ORCID, INSPIRE author id, researchmap slug/internal id).
- `urls`: canonical public links (Website, ORCID resolver, GitHub, INSPIRE, researchmap).
- Flat compatibility fields (`website`, `orcid`, `github`, `inspire`, `researchmap`) are retained for simple consumers.

Grant/award link fields:

- `urls.kaken`: KAKEN project page for the corresponding grant number.
- `urls.award`: official award/source page when supplied.
- `urls.jps_hot_topics`, `urls.jps_butsuri`: article coverage associated with the PTEP Editors' Choice record.

Presentation-specific fields:

- `role`: `self` or `collaborator`.
- `presenter`: actual speaker in the CV-derived record.
- `presenters_en`, `presenters_ja`: ResearchMap presenter/author arrays when available.
- `invited`: Boolean.
- `start_date`, `end_date`: ISO-like dates.
- `affiliation_period`: inferred from event date using the requested career periods.
- `researchmap_url`: ResearchMap presentation record.
- `researchmap_date`: retained when the ResearchMap date differs from the CV/LaTeX date; `date_conflict: true` marks this explicitly.
- `slides_file`: exact ResearchMap `dataset.dataset_name`.
- `slides_url`: direct GitHub Pages PDF URL under `https://o-morikawa.github.io/slides/`.
- `slides_repo_url`: corresponding GitHub repository file URL.
- `researchmap_attachment_url`: original ResearchMap attachment URL.

Publication-specific fields:

- INSPIRE-backed records keep `arxiv`, DOI, journal metadata, `inspire_bibkey`, and links when present.
- `topics` are lightweight discovery tags, not a controlled ontology.

Bilingual/provenance policy:

1. Preserve Japanese ResearchMap text in `*_ja`.
2. Preserve supplied English CV/LaTeX wording in `*_en` when already present.
3. If ResearchMap's English text differs materially, retain it in a separate `researchmap_*_en` field.
4. Do not silently resolve disagreements between sources; store the conflicting source value separately.
5. Do not invent Japanese translations when the source does not supply them.

## Source-native ID policy (v7)

IDs are generated from the most stable canonical external record when one exists.

1. **INSPIRE-backed scholarly publications**: use the INSPIRE BibTeX key verbatim, e.g. `Morikawa:2025xjq`.
2. **ResearchMap-backed presentations**: derive the ID from the public ResearchMap record URL:
   `https://researchmap.jp/o-morikawa/presentations/54946770`
   -> `researchmap:presentations:54946770`.
3. The previous locally generated slug is retained in `legacy_ids`, so existing references can be migrated safely.
4. Presentation slide URLs are metadata, not the identity source. They are stored in `slides_url`, `slides_file`, and `slides_repo_url`.
5. Records without a canonical external record keep their local ID until such a record becomes available.

The same ResearchMap convention can later be extended to other record collections (`awards`, `research_projects`, `teaching_experience`, etc.) without changing the basic scheme.
