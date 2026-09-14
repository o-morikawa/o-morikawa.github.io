# Pending source-dependent items

1. **ResearchMap bilingual merge**: `rm_researchers20260828.zip` is password-protected. Japanese originals from its JSONL payload have not been read. All `*_ja` fields with no independently supplied Japanese source remain `null` rather than being guessed.

2. **Unkeyed paper/preprint**: `publication(1).tex` contains **“A physical connection criterion for reaction-coordinate reduction in quantum-field tunneling”**, but the supplied `ref_om.bib` contains no corresponding INSPIRE BibTeX entry/key. Because the requested rule is to use the INSPIRE BibTeX key as the ID for papers, this record is intentionally not assigned an invented paper ID. It can be added as soon as its INSPIRE key is available (or if a temporary-ID policy is explicitly chosen).
