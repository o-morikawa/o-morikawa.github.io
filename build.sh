#!/bin/bash
cp ~/Dropbox/riken_2026/template/cv_om.pdf cv/
cp ~/Dropbox/riken_2026/template/publication.tex sources/
cp ~/Dropbox/riken_2026/template/presentation.tex sources/
cp ~/Dropbox/riken_2026/template/ref_om.bib cv/
cp ~/Dropbox/riken_2026/template/ref_om.bib sources/

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PYTHON=python3
if [ -x .venv/bin/python ] && .venv/bin/python -c "import yaml" >/dev/null 2>&1; then
  PYTHON=.venv/bin/python
elif ! python3 -c "import yaml" >/dev/null 2>&1; then
  python3 -m pip install -r requirements.txt
fi

# Fast-moving author-maintained layer: non-destructive upsert from LaTeX.
"$PYTHON" scripts/import_publications_tex.py sources/publication.tex
"$PYTHON" scripts/import_presentations_tex.py sources/presentation.tex

# External enrichment layers. These preserve TeX/manual fields and add stable IDs,
# bibliographic metadata, bilingual ResearchMap fields, and slide links.
"$PYTHON" scripts/import_bib.py sources/ref_om.bib -o data/publications.yaml --merge
"$PYTHON" scripts/merge_researchmap.py sources/rm_researchers.jsonl

"$PYTHON" scripts/build.py
cp site/index.html index.html
