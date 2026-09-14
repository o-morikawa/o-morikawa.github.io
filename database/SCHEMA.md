# Data conventions

All YAML files contain a top-level list of records.

Common fields:

- `id`: stable public identifier. INSPIRE-backed scholarly publications use the INSPIRE BibTeX key verbatim.
- `type`: top-level entity class (`publications`, `presentations`, `cv`, `books`, `software`).
- `kind`: subtype within the entity class.
- `title_en`, `title_ja`: English and Japanese title/name. A missing source-language value is `null`, never machine-guessed.
- `event_en`, `event_ja`: bilingual meeting/seminar/event name for presentations or CV activities.
- `organization_en`, `organization_ja`: bilingual institution/organization name where relevant.
- `source`: provenance of the current record.

Presentation-specific fields:

- `role`: `self` or `collaborator`.
- `presenter`: actual speaker.
- `invited`: Boolean.
- `start_date`, `end_date`: ISO-like dates.
- `affiliation_period`: inferred from the event date using the requested career periods.

Publication-specific fields:

- INSPIRE-backed records keep `arxiv`, DOI, journal metadata, `inspire_bibkey`, and links when present.
- `topics` are lightweight discovery tags, not a controlled ontology.

Bilingual merge policy:

1. Preserve the Japanese ResearchMap text verbatim in `*_ja`.
2. Preserve the supplied English CV/LaTeX wording in `*_en`.
3. Do not overwrite one language with a translation of the other unless explicitly requested.
4. Matching/normalization metadata should be stored separately if needed; it should not replace the source strings.
