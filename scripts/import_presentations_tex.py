#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from import_bib import infer_topics, tex_to_text
from sync_utils import load_yaml, merge_unique, norm, save_yaml, section_text, similarity, slug, split_top_level_items

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEX = ROOT / 'sources' / 'presentation.tex'
DEFAULT_YAML = ROOT / 'data' / 'presentations.yaml'
MONTHS = {m: i for i, m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], 1)}


def clean_tex(s: str) -> str:
    s = s.replace('\\OM\\', 'O. Morikawa ').replace('\\OM', 'O. Morikawa')
    s = re.sub(r'\\href\{[^{}]*\}\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\url\{([^{}]*)\}', r'\1', s)
    for _ in range(5):
        s = re.sub(r'\\(?:textbf|textit|emph)\{([^{}]*)\}', r'\1', s)
    s = s.replace(r'\&', '&').replace(r'\textasciicircum', '^')
    s = s.replace('\\\\', ' ')
    return tex_to_text(s)


def extract_titles(raw: str):
    return [clean_tex(m.group(1)).strip(' ,\n') for m in re.finditer(r"``(.*?)''", raw, re.S)]


def parse_date(text: str):
    pat = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:--(\d{1,2}))?,\s*(\d{4})\b'
    ms = list(re.finditer(pat, text))
    if not ms:
        return None, None, None
    m = ms[-1]
    mon = MONTHS[m.group(1)]
    d1 = int(m.group(2)); d2 = int(m.group(3)) if m.group(3) else d1; y = int(m.group(4))
    start = f'{y:04d}-{mon:02d}-{d1:02d}'
    end = f'{y:04d}-{mon:02d}-{d2:02d}' if d2 != d1 else None
    return start, end, m.span()


def affiliation(date):
    if not date: return None
    ym = int(date[:7].replace('-', ''))
    if ym <= 202103: return 'Kyushu University'
    if ym <= 202403: return 'Osaka University'
    return 'RIKEN (iTHEMS)'


def local_id(start, title):
    return f'presentation-{start or "undated"}-{slug(title, 60)}'


def parse_main_item(raw: str):
    tm = re.search(r"``(.*?)''", raw, re.S)
    if not tm: return None
    title = clean_tex(tm.group(1)).strip(' ,\n')
    start, end, dspan = parse_date(raw)
    presenter = 'Okuto Morikawa'; role = 'self'
    pm = re.search(r'\\textit\{talk by\s+([^{}]+)\}', raw, re.I)
    if pm:
        presenter = clean_tex(pm.group(1)); role = 'collaborator'
    invited = bool(re.search(r'\\textbf\{Invited (?:Speaker|Seminar)\}', raw))
    kind = 'poster' if r'\textbf{Poster}' in raw else ('seminar' if 'Invited Seminar' in raw else 'talk')

    event_raw = raw[tm.end(): dspan[0] if dspan else len(raw)]
    event_raw = re.sub(r'\\textit\{talk by\s+[^{}]+\}\s*,?', '', event_raw, flags=re.I)
    event_raw = re.sub(r'\\textbf\{(?:Invited Speaker|Invited Seminar|Poster)\}\s*(?:at\s*)?,?', '', event_raw)
    event = clean_tex(event_raw).strip(' ,.;\n')
    rec = {
        'id': local_id(start, title), 'type': 'presentations', 'kind': kind, 'role': role,
        'presenter': presenter, 'invited': invited, 'title_en': title, 'event_en': event,
        'start_date': start, 'end_date': end, 'year': int(start[:4]) if start else None,
        'affiliation_period': affiliation(start), 'topics': infer_topics(title, {}), 'source': 'presentation.tex',
    }
    return rec


def parse_other_item(raw: str):
    titles = extract_titles(raw)
    if not titles: return None
    title = titles[0]
    start, end, dspan = parse_date(raw)
    prefix = raw[:dspan[0] if dspan else raw.find('``')]
    event = clean_tex(prefix).strip(' ,:;\n')
    if 'Journal Club' in event:
        kind = 'journal_club'
    elif 'Coffee Meeting' in event:
        kind = 'informal_talk'
    else:
        kind = 'seminar'
    rec = {
        'id': local_id(start, title), 'type': 'presentations', 'kind': kind, 'role': 'self',
        'presenter': 'Okuto Morikawa', 'invited': False, 'title_en': title, 'event_en': event,
        'start_date': start, 'end_date': end, 'year': int(start[:4]) if start else None,
        'affiliation_period': affiliation(start), 'topics': infer_topics(title, {}), 'source': 'presentation.tex',
    }
    if len(titles) > 1:
        rec['references_discussed_en'] = titles[1:]
    hm = re.search(r'\\href\{([^{}]+)\}\{[^{}]+\}', raw)
    if hm: rec['url'] = hm.group(1)
    return rec


def parse(tex_path: Path):
    text = tex_path.read_text(encoding='utf-8')
    main = [parse_main_item(x) for x in split_top_level_items(section_text(text, 'Conference activities, talks, and seminars'))]
    other = [parse_other_item(x) for x in split_top_level_items(section_text(text, 'Other talks'))]
    records = [x for x in main + other if x]
    # Guard against parser-induced local-ID collisions without changing existing IDs on merge.
    seen = {}
    for r in records:
        base = r['id']; seen[base] = seen.get(base, 0) + 1
        if seen[base] > 1: r['id'] = f'{base}-{seen[base]}'
    return records


def find_match(records, inc):
    iid = inc['id']
    for r in records:
        if r.get('id') == iid or iid in (r.get('legacy_ids') or []):
            return r
    exact = [r for r in records if norm(r.get('title_en')) == norm(inc.get('title_en')) and r.get('start_date') == inc.get('start_date')]
    if len(exact) == 1: return exact[0]
    same_title = [r for r in records if norm(r.get('title_en')) == norm(inc.get('title_en'))]
    if len(same_title) == 1: return same_title[0]
    scored = []
    for r in records:
        sc = similarity(r.get('title_en'), inc.get('title_en'))
        if r.get('start_date') == inc.get('start_date'): sc += .15
        if norm(r.get('event_en')) == norm(inc.get('event_en')): sc += .10
        scored.append((sc, r))
    if scored:
        sc, r = max(scored, key=lambda x: x[0])
        if sc >= 1.05: return r
    return None


def sync(tex_path: Path, yaml_path: Path):
    incoming = parse(tex_path)
    records = load_yaml(yaml_path)
    added = updated = 0
    for inc in incoming:
        r = find_match(records, inc)
        if r is None:
            records.append(inc); added += 1; continue
        updated += 1
        old_topics = r.get('topics') or []
        protected_date = bool(r.get('date_note'))
        date_disagrees = protected_date and r.get('start_date') != inc.get('start_date')
        if date_disagrees:
            r['latex_start_date'] = inc.get('start_date')
            r['latex_end_date'] = inc.get('end_date')
        elif protected_date:
            # The author-maintained TeX has caught up with the explicit correction.
            # Keep the historical note, but remove stale literal-date provenance and
            # allow the current TeX end date/affiliation to become canonical again.
            r.pop('latex_start_date', None)
            r.pop('latex_end_date', None)
        for k, v in inc.items():
            if k in {'id', 'topics'}: continue
            if date_disagrees and k in {'start_date', 'end_date', 'year', 'affiliation_period'}:
                continue
            if k in {'url', 'references_discussed_en'} and v is None:
                continue
            r[k] = v
        r['topics'] = merge_unique(old_topics, inc.get('topics') or [])
    records.sort(key=lambda r: (str(r.get('start_date') or ''), str(r.get('id') or '')), reverse=True)
    save_yaml(yaml_path, records)
    return len(incoming), added, updated, len(records)


def main():
    ap = argparse.ArgumentParser(description='Non-destructively upsert presentation.tex into presentations.yaml.')
    ap.add_argument('tex', nargs='?', type=Path, default=DEFAULT_TEX)
    ap.add_argument('-o', '--output', type=Path, default=DEFAULT_YAML)
    args = ap.parse_args()
    parsed, added, updated, total = sync(args.tex, args.output)
    print(f'Parsed {parsed} TeX presentation records; +{added}, updated {updated}, total {total}')


if __name__ == '__main__':
    main()
