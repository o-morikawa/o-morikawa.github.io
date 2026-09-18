# ResearchMap import status

`sources/rm_researchers.jsonl` is readable and is merged using complete non-destructive upsert semantics.

Bundled ResearchMap source counts:

- research experience: 7
- education: 4
- awards: 7
- research projects: 9
- teaching experience: 6
- association memberships: 2
- committee memberships: 3
- academic contributions: 14
- social contributions: 3
- media coverage: 3
- research interests: 6
- research areas: 1
- presentations: 76
- published papers: 43
- misc: 20
- software/works: 9
- others: 5

Current merged state:

- presentations: 113 total; 76 ResearchMap-linked; 64 exact slide links from `dataset.dataset_name`
- scholarly publications: 53 total; 48 have ResearchMap provenance (`published_papers` and/or `misc`)
- other publications: 17 total; 15 have ResearchMap provenance
- software: 10 total; 9 have ResearchMap provenance
- CV: 101 total; 69 have at least one ResearchMap reference

Merge policy:

- match -> enrich/update ResearchMap-owned metadata;
- no match -> add a source-native ResearchMap record;
- local/TeX-only records are retained;
- author-supplied English wording remains canonical where present;
- ResearchMap Japanese values populate `*_ja`;
- materially different ResearchMap English is stored separately;
- multiple ResearchMap source categories can coexist through `researchmap_refs`;
- no source omission triggers deletion.

Notable v0.1.2 additions from the current ResearchMap export include the high-school education record, the 2025 University of Tsukuba multidisciplinary cooperative research project, and two dated MathSciNet review activities. The 2026 and 2021 Particle Physics Medal records are date-disambiguated and linked to their correct distinct ResearchMap award IDs.
