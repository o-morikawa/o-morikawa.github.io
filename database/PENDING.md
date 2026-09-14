# Pending / source-dependent items

1. **September 2026 slide filenames.** The ResearchMap export is dated 2026-08-28, so the September 2026 JPS talks are not present in it and therefore have no `dataset_name` from which to derive an exact GitHub slide URL. The database does not guess those filenames. The author-supplied correction has been applied: `presentation-2026-09-16-gradient-flow-actions-integerness-and-gluonic-fermionic-topo` is dated **2026-09-16** (legacy ID with 2026-09-14 retained in `legacy_ids`).

2. **TQFT 2025 date disagreement.** `presentation.tex` gives 2025-09-03 for “Non-perturbative analysis of resonance physics by exact WKB method,” while ResearchMap gives 2025-09-05 and names the slide `tqft250905.pdf`. The database preserves the CV/LaTeX date as `start_date`, the ResearchMap value as `researchmap_date`, and marks `date_conflict: true` instead of choosing silently.

3. **Unkeyed paper/preprint.** `publication(1).tex` contains “A physical connection criterion for reaction-coordinate reduction in quantum-field tunneling,” but the supplied `ref_om.bib` contains no corresponding INSPIRE BibTeX key. Because paper IDs are defined to be INSPIRE BibTeX keys, no invented paper ID is assigned yet.
