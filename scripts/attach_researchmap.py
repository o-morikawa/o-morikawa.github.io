#!/usr/bin/env python3
"""Attach a ResearchMap record URL (and optional slide URL) to an existing YAML record.

This is meant for newly-added talks that are newer than the latest ResearchMap JSONL export.
It does not scrape ResearchMap; it only derives the stable source-native id from the URL
and attaches the canonical links to an existing record.

Examples:
  python scripts/attach_researchmap.py data/presentations.yaml \
    --match-id presentation-2026-09-14-complex-scaling-approach-to-quasinormal-modes-of-schwarzschi \
    --researchmap-url https://researchmap.jp/o-morikawa/presentations/54946770

  python scripts/attach_researchmap.py data/presentations.yaml \
    --match-id researchmap:presentations:54946770 \
    --researchmap-url https://researchmap.jp/o-morikawa/presentations/54946770 \
    --slides-url https://o-morikawa.github.io/slides/EXAMPLE.pdf
"""
from __future__ import annotations
import argparse
from pathlib import Path
from urllib.parse import urlparse
import yaml
from id_utils import id_from_researchmap_url, researchmap_parts, promote_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('yaml_file')
    ap.add_argument('--match-id', required=True, help='Current id or one of legacy_ids')
    ap.add_argument('--researchmap-url', required=True)
    ap.add_argument('--slides-url')
    ap.add_argument('--slides-repo-url')
    args = ap.parse_args()

    path = Path(args.yaml_file)
    rows = yaml.safe_load(path.read_text(encoding='utf-8')) or []
    target = None
    for r in rows:
        if r.get('id') == args.match_id or args.match_id in (r.get('legacy_ids') or []):
            target = r
            break
    if target is None:
        raise SystemExit(f'No record matched id/legacy_id: {args.match_id}')

    collection, rid = researchmap_parts(args.researchmap_url) or (None, None)
    if not collection:
        raise SystemExit('Invalid ResearchMap record URL')
    target['researchmap_id'] = rid
    target['researchmap_type'] = collection
    target['researchmap_url'] = args.researchmap_url
    promote_id(target, id_from_researchmap_url(args.researchmap_url))

    if args.slides_url:
        target['slides_url'] = args.slides_url
        name = Path(urlparse(args.slides_url).path).name
        if name:
            target['slides_file'] = name
        if args.slides_repo_url:
            target['slides_repo_url'] = args.slides_repo_url
        elif name:
            target['slides_repo_url'] = f'https://github.com/o-morikawa/o-morikawa.github.io/blob/main/slides/{name}'

    path.write_text(yaml.safe_dump(rows, allow_unicode=True, sort_keys=False, width=120), encoding='utf-8')
    print(target['id'])


if __name__ == '__main__':
    main()
