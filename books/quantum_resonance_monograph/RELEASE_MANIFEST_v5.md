# Release manifest: Quantum Resonance v5

Release date: 2026-07-22  
Authors: Okuto Morikawa and Shoya Ogawa  
Title: *Quantum Resonance: A Calculational Monograph*

## Release identity

This is the first monograph-layout release.  It is distinct from the v4
review-paper archive.  The v4 project remains unchanged, and no legacy ZIP or
v4 release manifest is included in the v5 distribution archive.

## Book inventory

| Item | Count or value |
|---|---:|
| Physical PDF pages | 351 |
| Trim size | 6.5 x 9.5 in (468 x 684 pt) |
| Extracted prose/math words | approximately 98,000 |
| Learning Stages | 8 |
| Embedded Laboratories | 8 |
| End-of-Stage problems | 80 |
| Fully worked selected solutions | 16 |
| TeX source files | 63 |
| Source figure files | 59 |
| Bibliography entries | 294 |

## Canonical learning route

1. functional and operator foundations;
2. scattering data and long-range asymptotics;
3. the exact-WKB construction of resonance;
4. equivalent pole realizations and continuum response;
5. radial monodromy and renormalization;
6. weakly bound nuclei and CDCC;
7. exceptional points and geometric phase; and
8. Regge--Wheeler theory and black-hole quasinormal modes.

Each result is developed in one canonical location.  The calculation
laboratories reuse that result by equation or section reference.  Source-paper
material is retained for detailed calculations and figures, but duplicated
article introductions and review-style summaries are suppressed.

## Verification record

- `latexmk -pdf -interaction=nonstopmode -file-line-error main.tex`: success;
- BibTeX and MakeIndex passes: success;
- undefined citations or references: none;
- duplicate labels: none;
- Ghostscript full-document parse: success;
- Poppler metadata and text extraction: success;
- all 351 pages rasterized and contact-sheet inspected;
- raster edge scan: no content crossing the physical page boundary; and
- maximum residual TeX overfull box: 5.31 pt, confined within the designed
  text block.

## Distributed deliverables

- `quantum_resonance_monograph_v5.pdf`: reading copy;
- `quantum_resonance_monograph_v5_20260722.zip`: self-contained source release;
- `main.tex` and `ref.bib`: principal editable files; and
- this manifest and `README.md`.

The archive hash is reported alongside the downloadable ZIP because an
archive cannot contain its own stable digest.  The hashes of its principal
payload are:

<!-- FINAL_HASHES_BEGIN -->
```text
a3edcb8247b9bf8a9524bca48b045550e08b0a79076297543a9b90033c5ab040  main.tex
c00cea7c996d23898f9f644ff8bfa6a27011cc6164cdd3ee372d9ba3e9e03988  ref.bib
3a3f3e5a68401059817ef3feb0bfbad365c1a814e330f1af9f18764082795a18  main.pdf
```
<!-- FINAL_HASHES_END -->
