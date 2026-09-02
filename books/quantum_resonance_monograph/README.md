# Quantum Resonance as a Global Connection Problem

Version 7 (10 August 2026) is an English-language, self-contained textbook and
calculational monograph by Okuto Morikawa and Shoya Ogawa. It develops quantum
resonance from standard quantum mechanics, functional analysis, operator
algebras, nuclear physics, and scattering theory, and then reconstructs the
subject through exact WKB. A concept is derived in one canonical place,
calculated there, and subsequently cited rather than reintroduced.

## Learning architecture

The book has eight cumulative numbered Stages, with the mathematical opening
split into I-A and I-B:

1. **I-A:** topology, measure, unbounded operators, domains, self-adjointness,
   resolvents, spectra, and the projection-valued spectral theorem;
2. **I-B:** spectral multiplicity, measurable fields, direct integrals,
   commutants, `\vN` algebras, locally convex test spaces, compact
   kernels, Schatten ideals, and analytic Fredholm theory;
3. **II:** wave packets, Møller operators, the on-shell scattering operator,
   partial waves, Sturm--Liouville expansions, Jost functions, Coulomb and
   three-charge asymptotics, QED dressing, and gauge-theory sector structure;
4. **III:** exact-WKB connection problems and nonperturbative resonance
   quantization;
5. **IV:** continued resolvents, Zel'dovich regularization, Berggren
   completeness, complex scaling, the ABC theorem, rigged Hilbert spaces,
   pole residues, and continuum response;
6. **V:** radial equations, singular endpoints, the Langer correction, and
   monodromy renormalization;
7. **VI:** few-body nuclear reactions, broad and fragmented resonances in
   helium, weakly bound lithium and beryllium systems, CDCC, pseudostates,
   smoothing, and complex-scaled response;
8. **VII:** exceptional points, Jordan chains, geometric phase, and pole
   renormalization; and
9. **VIII:** the Regge--Wheeler reduction and black-hole quasinormal modes in
   Schwarzschild, Reissner--Nordström, and de Sitter geometries.

Nine Calculation Laboratories are embedded at the point where their tools
become available. Each Stage ends with problems. The back of the book gives
hints and selected calculation templates; the companion Japanese volume
`solutions_ja.tex` completely solves all 99 Stage problems and the seven
resummation problems.

## Changes in v7

- Added a prologue that treats scattering as the dynamical core of modern
  quantum mechanics and gives every finite-dimensional truncation an explicit
  parent space, projection, topology, observable, error criterion, and order
  of limits.
- Rebuilt the mathematical opening so that trace class, weak and strong
  operator topologies, projection-valued measures, resolvent sets, spectra,
  commutants, and measurable fields are defined before use.
- Separated energy-fiber decomposition from central decomposition and genuine
  superselection theory. A new derivation proves why operators commuting with
  a multiplicity-one spectral algebra are diagonal and then states the
  higher-multiplicity result.
- Added a self-contained derivation of the decomposable on-shell scattering
  operator, including channel multiplicity, thresholds, partial waves, and a
  finite-channel truncation contract.
- Added an observable-first gauge/AQFT chapter. It distinguishes BRST
  cohomology, GNS representation selection, direct-integral and central
  decompositions, DHR/BF sectors, Gauss-law reduction, edge centers, type-III
  locality, and encoding-dependent nonlocality. A finite Z2 lattice example
  makes the distinction calculable.
- Strengthened the type-A Aguilar--Balslev--Combes theorem and its resolvent
  proof, including analytic-vector matrix elements, relative compactness,
  essential-spectrum rotation, pole multiplicity, and angle independence.
- Replaced an informal Berggren discussion by a finite-range weak expansion
  with explicit endpoint, analyticity, contour, threshold, simplicity, and
  test-space hypotheses.
- Expanded the Regge--Wheeler calculation from tensor-harmonic identities
  through the odd-parity Einstein equations, constraint elimination, master
  variable, potential, and reconstruction formulae.
- Recast the concluding programme around the connection-first exact-WKB
  strategy and removed residual review-style chronology and duplicated
  expository blocks from the source-paper Laboratories.
- Unified the body notation with `omphys.sty`: resolvents use `\Resolvent`,
  state and dual pairings use the bra--ket and `\dualpair` commands, spectra
  use the declared spectrum macros, resonance energies use `\resonantE`, and
  Voros periods and exponentials use `\VorosPeriod` and `\VorosExp`.
- Standardized upright semantic scripts with `\vsub`, `\vsup`, and the new
  three-argument `\vsupb`; a conservative audit tool applies these commands
  only to complete TeX atoms and explicitly excludes structural commands.
- Standardized the incoming connection datum as `\Cincoming`.  It denotes a
  scalar coefficient in one channel and the corresponding incoming block in
  several channels; the distinction is dimensional, not conceptual.
- Added the personal-name macros `\vN` and `\tH`, and standardized visible
  occurrences of von Neumann through `\vN`.  Draft equation-label overlays
  remain available through `\showdraftlabelstrue` but are disabled by default.
- Standardized an explicitly spaced differential `\,\rmd` as the single
  house command `\dd`; the notation normalizer now enforces this convention.
- Added a self-contained computational appendix which carries one quartic
  benchmark through truncation, Borel and lateral summation, Padé and
  Borel--Padé, optimized and variational perturbation theory,
  order-dependent mapping, instanton large order, and the exact-WKB
  dictionary.  A text-readable Wolfram Language implementation is included.
- Added Stage-organized bibliographical notes.  The bibliography contains
  works used in the text and notes; uncited database records are not forced
  into print with `\nocite{*}`.
- Rebuilt the subject index on substantive derivation pages, removed glossary
  page locators, added hierarchy and cross-references, and supplied an
  idempotent curated index-rebuild tool.
- Added a 77-page Japanese companion containing complete solutions to all 106
  problems. Its source and embedded Noto Serif JP fonts are included, while
  the compiled PDF is distributed as a separate deliverable.
- Retained the v6 removal of `\revone`, `\revtwo`, `\revthr`, `\revthree`, and
  `\magenta`. A math-region audit finds no legacy `\mathrm{i}` or
  `\mathrm{d}` forms; the source uses `\rmi`, `\rmd`, and `\rme` conventions.
- Converted the distribution to source-only form. Generated PDFs and LaTeX
  build products are omitted; PDF files under `source_compendium/figures/`
  are source figures and must be retained.

## Contents of this source release

- `main.tex`: book driver and canonical Stage order;
- `chapters/`: foundations, Laboratories, problems, solutions, glossary, and
  synthesis chapters;
- `source_compendium/`: detailed calculations and required figures adapted
  from the authors' seven-paper exact-WKB/complex-scaling programme;
- `notebooks/resummation_workflow.wl`: compact Wolfram Language calculation
  companion for the resummation appendix;
- `ref.bib`: bibliography, retaining literal arXiv identifiers as citation
  keys where they were supplied by the arXiv source;
- `tools/normalize_tex_notation.py`: conservative math-region notation audit;
- `tools/normalize_semantic_scripts.py`: conservative `\vsub`/`\vsup`/`\vsupb`
  audit and normalization;
- `solutions_ja.tex` and `solutions_ja/`: complete Japanese solutions and
  their redistributable embedded fonts;
- `tools/rebuild_subject_index.py`: curated, repeatable subject-index
  reconstruction;
- `tools/unwrap_revision_commands.py`: balanced-brace provenance utility; and
- `tools/build_source_compendium.py`: provenance helper for rebuilding the
  source-paper compendium when original arXiv source trees are present.

The provenance helpers are not needed to typeset the book. All TeX sources
and figures required by `main.tex` are included.

## Building

A current TeX Live installation with pdfLaTeX, BibTeX, MakeIndex, TikZ,
`tcolorbox`, `natbib`, and the standard AMS packages is sufficient. A fully
explicit build is:

```sh
pdflatex -interaction=nonstopmode -file-line-error main.tex
bibtex main
makeindex main.idx
pdflatex -interaction=nonstopmode -file-line-error main.tex
pdflatex -interaction=nonstopmode -file-line-error main.tex
```

Alternatively:

```sh
latexmk -pdf -interaction=nonstopmode -file-line-error main.tex
```

The Japanese solutions use XeLaTeX and the included fonts:

```sh
xelatex -interaction=nonstopmode -halt-on-error solutions_ja.tex
xelatex -interaction=nonstopmode -halt-on-error solutions_ja.tex
```

The supplied `utphys.bst` and `natbib.sty` make the bibliography independent
of a journal template. The legacy PTEP class and styles are retained only as
source provenance and are not loaded by `main.tex`.

## Validation

The revised v7 source was clean-built into a 442-page verification copy at a
6.5 by 9.5 inch trim size. The
compiled bibliography contains 219 cited works from a 316-record database.
The subject index contains 1,610 page locators under 229 printed headwords.
BibTeX and MakeIndex completed, all cited keys were resolved, and the final log
contained no undefined references, undefined citations, duplicate labels,
LaTeX errors, overfull boxes, hyperref warnings, or MakeIndex warnings. The
77-page Japanese solutions PDF was separately clean-built with all fonts
embedded and no errors, unresolved references, hyperref warnings, or
overfull boxes. Verification PDFs are deliberately not included in this
source release.
