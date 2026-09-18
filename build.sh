#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Optional convenience sync for the author's working tree.  A distributed clone
# remains fully buildable from the bundled sources when this directory is absent.
AUTHOR_CV_DIR="${AUTHOR_CV_DIR:-$HOME/Dropbox/riken_2026/template}"
sync_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -f "$src" ]; then
    cp "$src" "$dst"
  fi
}
sync_if_exists "$AUTHOR_CV_DIR/cv_om.tex" sources/cv_om.tex
sync_if_exists "$AUTHOR_CV_DIR/cv.tex" sources/cv.tex
sync_if_exists "$AUTHOR_CV_DIR/cv_om.pdf" cv/cv_om.pdf
sync_if_exists "$AUTHOR_CV_DIR/publication.tex" sources/publication.tex
sync_if_exists "$AUTHOR_CV_DIR/presentation.tex" sources/presentation.tex
sync_if_exists "$AUTHOR_CV_DIR/ref_om.bib" sources/ref_om.bib
sync_if_exists "$AUTHOR_CV_DIR/ref_om.bib" cv/ref_om.bib

PYTHON=python3
if [ -x .venv/bin/python ] && .venv/bin/python -c "import yaml" >/dev/null 2>&1; then
  PYTHON=.venv/bin/python
elif ! python3 -c "import yaml" >/dev/null 2>&1; then
  python3 -m pip install -r requirements.txt
fi

# Fast-moving author-maintained layer.  Every importer performs a non-destructive
# upsert: it updates fields owned by that source, adds genuinely new records, and
# never deletes records or metadata merely because a source omits them.
"$PYTHON" scripts/import_cv_tex.py sources/cv.tex --preamble sources/cv_om.tex
"$PYTHON" scripts/import_publications_tex.py sources/publication.tex --preamble sources/cv_om.tex
"$PYTHON" scripts/import_presentations_tex.py sources/presentation.tex --preamble sources/cv_om.tex

# External enrichment layers.  BibTeX/INSPIRE and ResearchMap may add stable IDs,
# bibliographic data, Japanese/bilingual metadata, and slide links.  ResearchMap
# unmatched records are added source-natively; local-only records are retained.
"$PYTHON" scripts/import_bib.py sources/ref_om.bib -o data/publications.yaml --merge
"$PYTHON" scripts/merge_researchmap.py sources/rm_researchers.jsonl

"$PYTHON" scripts/build.py
cp site/index.html index.html
