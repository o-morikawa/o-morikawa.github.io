# ResearchMap import status

`sources/rm_researchers.jsonl` is readable and has been imported. The bundled export was produced before the September 2026 JPS records.

The export contains structured bilingual fields for career history, education, awards, research projects, teaching, memberships, presentations, works/software, academic contributions, social contributions, media coverage, research interests and related records.

Merge policy:

- existing English CV/LaTeX wording remains the canonical English display value when already present;
- ResearchMap Japanese source values populate `*_ja`;
- differing ResearchMap English text is retained separately as `researchmap_*_en` where appropriate;
- ResearchMap IDs and provenance are retained on matched records;
- records absent from ResearchMap, notably collaborator talks, remain untouched;
- no Japanese title/event is fabricated when the ResearchMap export has no corresponding record.

Presentation matching result: 75 / 110 database presentation records matched to ResearchMap, and 63 matched records carry a ResearchMap `dataset_name`, which is used as the exact slide filename.

Current publication matching after the TeX-first sync: 42 / 49 scholarly publication records have ResearchMap `published_papers` provenance. TeX-only/provisional records do not require a ResearchMap match.
