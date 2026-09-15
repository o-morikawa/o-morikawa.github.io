#!/bin/bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python3 scripts/import_bib.py sources/ref_om.bib -o data/publications.yaml
python3 scripts/build.py
python3 scripts/merge_researchmap.py sources/rm_researchers.jsonl
python3 scripts/build.py
cp site/index.html index.html
