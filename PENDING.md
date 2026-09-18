# Pending / source-dependent items

1. **Collaborator-talk slide links.** ResearchMap is a personal profile and does not contain the collaborator talks retained from `presentation.tex`. Their records remain complete enough to appear in the database, but an exact slide URL is added only when another trusted source supplies it; filenames are not guessed.

2. **Author-corrected September 2026 date.** `presentation-2026-09-16-gradient-flow-actions-integerness-and-gluonic-fermionic-topo` remains canonically dated **2026-09-16**. The current `presentation.tex` now agrees with that correction; the historical `date_note` is retained while stale earlier range metadata is no longer carried forward.

3. **TQFT 2025 date disagreement.** `presentation.tex` gives 2025-09-03 for “Non-perturbative analysis of resonance physics by exact WKB method,” while ResearchMap gives 2025-09-05 and names the slide `tqft250905.pdf`. The canonical date remains the TeX value; the ResearchMap value is retained as `researchmap_date` with `date_conflict: true`.

4. **TeX-only provisional preprint.** `sources/publication.tex` contains “A physical connection criterion for reaction-coordinate reduction in quantum-field tunneling,” while the bundled `ref_om.bib` has no corresponding INSPIRE BibTeX key. It remains a local provisional publication. When a matching INSPIRE BibTeX entry is later added, the BibTeX merge can promote the record to that source-native key while retaining its local ID in `legacy_ids`.
