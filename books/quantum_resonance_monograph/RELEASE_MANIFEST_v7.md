# Version 7 source manifest

Release date: 10 August 2026

## Distribution policy

This is a source-only release. The root-level verification PDF and all
auxiliary LaTeX build products are excluded from the ZIP. The 58 PDF files
below `source_compendium/figures/` are required source figures and are
retained.

## Principal v7 additions

- `chapters/frontmatter/prologue_scattering.tex`: scattering as the dynamical
  core of quantum mechanics and the finite-dimensional truncation contract;
- `chapters/core/sec_scattering_direct_integral.tex`: spectral intertwining,
  decomposability, on-shell fibers, multiplicity, thresholds, and channel
  truncation;
- `chapters/core/sec_gauge_aqft.tex`: BRST, observable algebras, GNS
  representations, central and superselection decompositions, lattice Gauss
  law, regional centers, and AQFT locality;
- expanded foundational definitions in
  `chapters/core/sec_quantum_foundations.tex` and
  `chapters/core/sec_functional_operator_algebra.tex`;
- strengthened ABC, Berggren, and Regge--Wheeler derivations in
  `chapters/core/app_abc_sketch.tex`,
  `chapters/core/sec_rigged_hilbert.tex`, and
  `chapters/core/sec_black_hole_qnm.tex`; and
- a connection-first synthesis in
  `chapters/core/sec_program_development.tex`;
- `chapters/appendices/app_resummation_instantons.tex` and
  `notebooks/resummation_workflow.wl`: a worked comparison of resummation,
  optimized/variational reorganization, ODM, and instanton large order,
  translated into exact-WKB connection data;
- `chapters/backmatter/bibliographical_notes.tex`: Stage-organized reading
  routes which cite selected literature without forcing every database record
  into print; and
- `tools/rebuild_subject_index.py`: curated subject locators on substantive
  pages, independent of the glossary; and
- `solutions_ja.tex` and `solutions_ja/`: complete Japanese solutions to all
  106 problems, with redistributable embedded Japanese fonts.

## Minor notation revision

- `omphys.sty` is the single source of the book's principal notation,
  including `\Resolvent`, `\resolventset`, `\spectrum`, `\essspectrum`,
  `\acspectrum`, `\pseudospectrum`, `\Banach`, `\VorosPeriod`,
  `\VorosExp`, `\Cincoming`, `\resonantE`, `\vsub`, `\vsup`, and `\vsupb`.
- Raw angle-bracket state notation in the TeX body was converted to the
  declared bra--ket or dual-pairing commands.
- `\Cincoming` denotes the scalar incoming coefficient in one channel and
  the incoming connection block in a multichannel problem.
- `\vN` and `\tH` were added for personal names; visible von Neumann
  occurrences now use `\vN`.
- `\dd` is the canonical explicitly spaced differential and replaces every
  literal `\,\rmd` pair.
- Proof labels are opt-in through `\showdraftlabelstrue` and are off in the
  ordinary build.

## Verification record

The distributed sources were built from a clean state with

```sh
latexmk -C main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The verification build produced 442 physical pages. The bibliography printed
219 cited works from 316 database
records.  The subject index accepted 1,610 page locators under 229 printed
headwords.  BibTeX and MakeIndex completed successfully. The final log
contained no undefined citations, undefined references, duplicate labels,
LaTeX errors, overfull boxes, hyperref warnings, or MakeIndex warnings.
Poppler parsed the complete PDF, and representative pages from the new
resummation appendix, Wolfram Language listing, bibliographical notes, and
multi-page subject index were raster-inspected in addition to the earlier
prologue, direct-integral, gauge/AQFT, ABC, Berggren, and Regge--Wheeler
checks.

The companion Japanese solutions clean-built with XeLaTeX to 77 physical
pages. All fonts are embedded; the final log contains no LaTeX errors,
undefined references, hyperref warnings, or overfull boxes. Representative
pages from the cover, contents, every Stage, the resummation appendix, and the
final conventions page were raster-inspected.

The notation audit

```sh
python3 tools/normalize_tex_notation.py .
python3 tools/normalize_semantic_scripts.py .
```

reported `changed_files=0`. No body occurrence of `\revone`, `\revtwo`,
`\revthr`, `\revthree`, `\magenta`, `\emph`, `\exp`, or `\,\rmd` remains.
