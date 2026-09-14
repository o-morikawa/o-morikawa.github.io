# ResearchMap import status

`rm_researchers20260828.jsonl` is readable and has been imported.

The export contains structured bilingual fields for career history, education, awards, research projects, teaching, memberships, presentations, works/software, academic contributions, social contributions, media coverage, research interests and related records.

Merge policy:

- existing English CV/LaTeX wording remains the canonical English display value when already present;
- ResearchMap Japanese source values populate `*_ja`;
- differing ResearchMap English text is retained separately as `researchmap_*_en` where appropriate;
- ResearchMap IDs and provenance are retained on matched records;
- no Japanese title/event is fabricated when the ResearchMap export has no corresponding record.

Presentation matching result: 75 / 110 database presentation records matched to ResearchMap, and 63 matched records carry a ResearchMap `dataset_name`, which is used as the exact slide filename.
