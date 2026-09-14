python3 scripts/import_bib.py sources/ref_om.bib -o data/publications.yaml
python3 scripts/build.py
python3 scripts/merge_researchmap.py sources/rm_researchers.jsonl
python3 scripts/build.py
