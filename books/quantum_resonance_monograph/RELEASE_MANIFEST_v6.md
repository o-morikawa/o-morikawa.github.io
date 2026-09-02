# Release manifest: Quantum Resonance v6

Release date: 2026-07-22  
Authors: Okuto Morikawa and Shoya Ogawa  
Title: *Quantum Resonance as a Global Connection Problem*

## Release identity

This release is derived from the authors' corrected v5 source archive.  It is
distributed as a new v6 artifact; the supplied v5 archive is not modified.
All legacy revision markup has been unwrapped in the body text, and the book
is presented as a monograph before any formal revision cycle.

## Book inventory

| Item | Count or value |
|---|---:|
| Physical PDF pages | 389 |
| Trim size | 6.5 x 9.5 in (468 x 684 pt) |
| Extracted prose/math words | approximately 111,000 |
| Learning Stages | 8 |
| Embedded calculation Laboratories | 9 |
| End-of-Stage problems | 99 |
| Fully worked selected solutions | 16 |
| TeX source files | 67 |
| Source figure files | 59 |
| Bibliography database entries | 303 |
| Bibliography items cited in this build | 173 |

## Canonical learning route

1. operator domains, topology, direct integrals, and compact/Fredholm theory;
2. Sturm--Liouville and Jost scattering data, including long-range failures;
3. exact-WKB construction of the global incoming connection coefficient;
4. Zel'dovich, complex-scaled, rigged-space, and response realizations of one
   invariant pole and residue;
5. radial endpoint monodromy and renormalization;
6. few-body nuclei, $^6$He pole projectors, CDCC, CSLS, lithium, and beryllium;
7. exceptional points and geometric phase; and
8. Regge--Wheeler theory and black-hole quasinormal modes.

## v6 source transformations

- 168 balanced revision wrappers were removed from the source-paper
  compendium: 94 `\revone`, 30 `\revtwo`, 12 `\revthr`, no `\revthree`, and
  32 `\magenta` invocations.  No body invocation remains.
- Mathematical notation was normalized only inside recognized TeX math
  regions; a repeat run of the checker makes zero changes.
- New chapters and the $^6$He Laboratory were inserted at their prerequisite
  points in the Stage route rather than collected as appendices.
- Added bibliography records retain the literal keys `arXiv:2003.05123`,
  `arXiv:2103.16865`, and `arXiv:2111.04285`.

## Verification record

- pdfLaTeX, BibTeX, and MakeIndex passes: success;
- hard TeX errors: none;
- undefined citations or cross-references: none;
- duplicate labels or bibliography keys: none;
- revision-wrapper invocations in `.tex` body files: none;
- repeat notation-normalizer changes: none;
- Ghostscript full-document parse: success;
- Poppler metadata and text extraction: success;
- PDF structural check: success;
- all 389 pages rasterized and inspected in contact sheets; and
- residual overfull boxes are at most 5.08 pt and occur only in retained
  source-compendium equations/tables.

## Distributed deliverables

- `quantum_resonance_monograph_v6.pdf`: reading copy;
- `quantum_resonance_monograph_v6_20260722.zip`: self-contained source release;
- `quantum_resonance_monograph_v6_main.tex` and
  `quantum_resonance_monograph_v6_ref.bib`: principal editable files;
- `quantum_resonance_monograph_v6_README.md`; and
- this manifest.

The source-archive hash is reported beside the downloadable ZIP because an
archive cannot contain its own stable digest.  Hashes of the principal
payload follow.

<!-- FINAL_HASHES_BEGIN -->
```text
1d723d736b6f2ae789c7197771d485c80fc2c301bb7a9f78e021c817b75db2ea  main.tex
5f04be777e13322d7dac5c105bf39e67652c835affa5cc09c3bd1c69803d518c  ref.bib
b2d78ac7511eb56dc64a6ef694a88816ae76c2d94451b90730e999f41108c365  main.pdf
```
<!-- FINAL_HASHES_END -->
