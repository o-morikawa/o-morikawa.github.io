#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import quote

import yaml

from id_utils import promote_id
from sync_utils import merge_unique, norm, same_author_list, similarity


def split_entries(text: str):
    i = 0
    n = len(text)
    while i < n:
        at = text.find('@', i)
        if at < 0:
            return
        m = re.match(r'@(\w+)\s*\{', text[at:])
        if not m:
            i = at + 1
            continue
        entry_type = m.group(1).lower()
        body_start = at + m.end()
        depth = 1
        j = body_start
        in_quote = False
        escaped = False
        while j < n and depth:
            c = text[j]
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                in_quote = not in_quote
            elif not in_quote:
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
            j += 1
        if depth != 0:
            raise ValueError(f'Unbalanced BibTeX entry near byte {at}')
        body = text[body_start:j-1].strip()
        yield entry_type, body
        i = j


def split_top_level_comma(text: str):
    depth = 0
    in_quote = False
    escaped = False
    for i, c in enumerate(text):
        if escaped:
            escaped = False
            continue
        if c == '\\':
            escaped = True
            continue
        if c == '"':
            in_quote = not in_quote
            continue
        if not in_quote:
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            elif c == ',' and depth == 0:
                return text[:i], text[i+1:]
    return text, ''


def parse_fields(text: str):
    fields = {}
    i = 0
    n = len(text)
    while i < n:
        while i < n and (text[i].isspace() or text[i] == ','):
            i += 1
        if i >= n:
            break
        m = re.match(r'([A-Za-z][A-Za-z0-9_-]*)\s*=\s*', text[i:])
        if not m:
            # Skip unexpected material rather than silently looping forever.
            next_comma = text.find(',', i)
            if next_comma < 0:
                break
            i = next_comma + 1
            continue
        key = m.group(1)
        i += m.end()
        if i >= n:
            fields[key] = ''
            break
        if text[i] == '{':
            start = i + 1
            depth = 1
            i += 1
            escaped = False
            while i < n and depth:
                c = text[i]
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                i += 1
            value = text[start:i-1]
        elif text[i] == '"':
            i += 1
            start = i
            escaped = False
            while i < n:
                c = text[i]
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == '"':
                    break
                i += 1
            value = text[start:i]
            i += 1
        else:
            start = i
            while i < n and text[i] != ',':
                i += 1
            value = text[start:i].strip()
        fields[key] = value.strip()
    return fields


def parse_bibtex(path: Path):
    text = path.read_text(encoding='utf-8')
    entries = []
    for entry_type, body in split_entries(text):
        key_part, rest = split_top_level_comma(body)
        key = key_part.strip()
        if not key:
            raise ValueError('BibTeX entry without citation key')
        fields = parse_fields(rest)
        entries.append((entry_type, key, fields))
    return entries


def strip_balanced_outer_braces(s: str) -> str:
    s = s.strip()
    changed = True
    while changed and len(s) >= 2 and s[0] == '{' and s[-1] == '}':
        changed = False
        depth = 0
        escaped = False
        balanced_to_end = False
        for i, c in enumerate(s):
            if escaped:
                escaped = False
                continue
            if c == '\\':
                escaped = True
                continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    balanced_to_end = (i == len(s) - 1)
                    break
        if balanced_to_end:
            s = s[1:-1].strip()
            changed = True
    return s


def tex_to_text(s: str) -> str:
    s = strip_balanced_outer_braces(s)
    replacements = {
        r'{\"o}': 'ö', r'\"o': 'ö',
        r'{\"O}': 'Ö', r'\"O': 'Ö',
        r'\theta': 'θ', r'\pi': 'π', r'\times': '×',
        r'\mathbb{Z}': 'ℤ', r'\mathbb{R}': 'ℝ', r'\mathbb{C}': 'ℂ',
        r'\mathcal{N}': '𝒩', r'\star': '⋆',
        r'\,': ' ', r'\!': '',
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    # Common TeX typography used in the imported titles.
    s = s.replace('---', '—').replace('--', '–').replace('~', ' ')
    s = s.replace('$', '')
    s = re.sub(r'\^\{([^{{}}]+)\}', lambda m: '^(' + m.group(1).replace('-', '−') + ')', s)
    s = s.replace('×', ' × ')
    # Drop grouping braces after macro conversion. The source BibTeX is still the provenance.
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'\\([A-Za-z]+)', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def parse_authors(s: str):
    authors = []
    for person in re.split(r'\s+and\s+', s.strip()):
        person = tex_to_text(person.strip())
        if ',' in person:
            family, given = [p.strip() for p in person.split(',', 1)]
            authors.append(f'{given} {family}'.strip())
        elif person:
            authors.append(person)
    return authors


def arxiv_date(eprint: str | None):
    if not eprint:
        return None
    m = re.match(r'^(\d{2})(\d{2})\.', eprint)
    if not m:
        return None
    yy, mm = map(int, m.groups())
    year = 2000 + yy if yy < 90 else 1900 + yy
    return f'{year:04d}-{mm:02d}'


def affiliation_from_arxiv(eprint: str | None, key: str, entry_type: str, fields: dict):
    d = arxiv_date(eprint)
    if d:
        ym = int(d.replace('-', ''))
        if 201601 <= ym <= 202103:
            return 'Kyushu University', f'arXiv:{eprint}'
        if 202104 <= ym <= 202403:
            return 'Osaka University', f'arXiv:{eprint}'
        if ym >= 202404:
            return 'RIKEN (iTHEMS)', f'arXiv:{eprint}'
        return 'Kyushu University', f'arXiv:{eprint}'

    # Two records in the supplied INSPIRE BibTeX have no arXiv identifier.
    if key == 'Makino:2021edc':
        return 'Kyushu University', 'erratum of arXiv:1802.07897'
    if entry_type == 'phdthesis' or key == 'Morikawa:2021lmb':
        return 'Kyushu University', 'thesis institution/year'
    return 'Unknown', 'no arXiv identifier'


def infer_kind(entry_type: str, fields: dict, key: str):
    if entry_type == 'phdthesis':
        return 'thesis'
    if key == 'Makino:2021edc':
        return 'erratum'
    journal = fields.get('journal', '')
    if journal in {'PoS', 'EPJ Web Conf.'}:
        return 'proceedings'
    return 'paper'


def infer_topics(title: str, fields: dict):
    t = title.lower()
    topics = []

    def add(*xs):
        for x in xs:
            if x not in topics:
                topics.append(x)

    if any(x in t for x in ['black-hole', 'black hole', 'quasinormal', 'ringdown']):
        add('black holes', 'quasinormal modes')
    if 'nuclear' in t:
        add('nuclear reactions')
    if 'resonance' in t or 'resonant' in t:
        add('quantum resonance')
    if 'exceptional point' in t:
        add('exceptional points')
    if 'complex scaling' in t:
        add('complex scaling method')
    if 'scattering' in t:
        add('scattering theory')
    if 'exact wkb' in t:
        add('exact WKB', 'quantum resonance')
    if 'quantum mechanics' in t:
        add('quantum mechanics')
    if 'rigged hilbert' in t:
        add('rigged Hilbert space', 'spectral theory')

    if 'eigenstate thermalization' in t:
        add('eigenstate thermalization hypothesis', 'quantum many-body theory')
    if 'projective representation' in t:
        add('projective symmetry')

    if any(x in t for x in ['lattice', 'yang–mills', 'yang-mills', 'gauge theory', 'gauge theories']):
        add('lattice gauge theory')
    if any(x in t for x in ['generalized symmetr', 'higher-form', 'higher-group', 'noninvertible', '2-form gauge', 'magnetic operators']):
        add('generalized symmetry')
    if any(x in t for x in ["'t hooft", "'t~hooft", 'dyon condensation', 'confining phase', 'partition function']):
        add('confinement')
    if 'topological charge' in t or 'topology' in t or 'winding number' in t:
        add('topology')
    if 'anomaly' in t:
        add('anomalies')
    if 'chiral gauge' in t or 'chiral overlap' in t:
        add('chiral gauge theory')
    if 'bosonization' in t:
        add('bosonization')

    if 'gradient flow' in t:
        add('gradient flow')
    if 'renormalization group' in t or 'rg fixed point' in t:
        add('renormalization group')
    if 'renormalon' in t:
        add('renormalons', 'resurgence')
    if 'bion' in t:
        add('resurgence', 'semiclassical field theory')
    if 's^1' in t or 'compactified' in t:
        add('compactified field theory')

    if 'landau–ginzburg' in t or 'landau-ginzburg' in t:
        add('Landau–Ginzburg model', 'supersymmetry', 'conformal field theory')
    if 'super yang–mills' in t or 'supercurrent' in t or 'supersymmetric' in t:
        add('supersymmetry')
    if 'linear quiver' in t:
        add('gauge theory', 'anomaly matching')
    if 'wilsonian' in t:
        add('Wilsonian renormalization group')

    primary = fields.get('primaryClass')
    if primary == 'hep-lat':
        add('lattice field theory')
    elif primary == 'quant-ph':
        add('quantum mechanics')
    elif primary == 'gr-qc' and 'black holes' not in topics:
        add('gravitation')
    if len(topics) < 2:
        if primary == 'hep-th':
            add('quantum field theory')
        elif not primary:
            add('theoretical physics')
    return topics


def make_record(entry_type: str, key: str, f: dict):
    eprint = f.get('eprint') or None
    title_tex = strip_balanced_outer_braces(f.get('title', ''))
    title = tex_to_text(title_tex)
    affiliation, affiliation_basis = affiliation_from_arxiv(eprint, key, entry_type, f)
    kind = infer_kind(entry_type, f, key)
    status = 'preprint' if entry_type == 'article' and not f.get('journal') else 'published'
    if entry_type == 'phdthesis':
        status = 'thesis'
    if kind == 'erratum':
        status = 'published'

    record = {
        'id': key,
        'type': 'publications',
        'kind': kind,
        'status': status,
        'authors': parse_authors(f.get('author', '')),
        'title': title,
        'year': int(f['year']) if f.get('year', '').isdigit() else f.get('year'),
        'affiliation_period': affiliation,
        'affiliation_basis': affiliation_basis,
    }
    if title_tex and title_tex != title:
        record['title_bibtex'] = title_tex
    if eprint:
        record['arxiv'] = eprint
        record['arxiv_url'] = f'https://arxiv.org/abs/{eprint}'
        d = arxiv_date(eprint)
        if d:
            record['arxiv_date'] = d
    if f.get('primaryClass'):
        record['arxiv_class'] = f['primaryClass']
    if f.get('doi'):
        record['doi'] = f['doi']
        record['doi_url'] = f'https://doi.org/{f["doi"]}'
    for src, dst in [
        ('journal', 'journal'), ('volume', 'volume'), ('number', 'number'),
        ('pages', 'pages'), ('school', 'school'), ('reportNumber', 'report_number'),
        ('note', 'note'),
    ]:
        if f.get(src):
            record[dst] = tex_to_text(f[src])
    record['inspire_bibkey'] = key
    record['inspire_url'] = 'https://inspirehep.net/literature?q=' + quote('texkeys:' + key, safe='')
    record['topics'] = infer_topics(title, f)
    return record


def sort_key(r):
    # The user requested affiliation periods to follow arXiv numbering, so arXiv date
    # is also the natural primary chronology when available.
    return (str(r.get('arxiv_date') or f"{r.get('year', 0)}-00"), str(r['id']))


def find_existing(records, incoming):
    key = incoming.get('id')
    for r in records:
        if r.get('id') == key or key in (r.get('legacy_ids') or []):
            return r
    arxiv = incoming.get('arxiv')
    if arxiv:
        for r in records:
            if str(r.get('arxiv') or '').lower() == str(arxiv).lower():
                return r
    doi = incoming.get('doi')
    if doi:
        for r in records:
            if str(r.get('doi') or '').lower() == str(doi).lower():
                return r
    title = incoming.get('title')
    exact = [r for r in records if norm(r.get('title') or r.get('title_en')) == norm(title)]
    if len(exact) == 1:
        return exact[0]
    scored = [(similarity(r.get('title') or r.get('title_en'), title), r) for r in records]
    if scored:
        sc, r = max(scored, key=lambda x: x[0])
        if sc >= .985:
            return r
    return None


def merge_records(existing, incoming):
    old_topics = existing.get('topics') or []
    tex_backed = existing.get('source') == 'publication.tex'
    if tex_backed:
        # Keep the TeX title/current status as the fast-moving canonical layer.
        # INSPIRE/BibTeX enriches identity and bibliographic metadata.
        if incoming.get('authors'):
            if existing.get('authors') and not same_author_list(existing.get('authors'), incoming.get('authors')):
                existing['authors_latex'] = existing.get('authors_latex') or existing['authors']
            existing['authors'] = incoming['authors']
        if incoming.get('title_bibtex'):
            existing['title_bibtex'] = incoming['title_bibtex']
        elif incoming.get('title') and incoming.get('title') != existing.get('title'):
            existing['title_bibtex'] = incoming['title']
        for k, v in incoming.items():
            if k in {'id', 'title', 'authors', 'kind', 'status', 'year', 'topics', 'title_bibtex'}:
                continue
            if v is not None and v != '':
                existing[k] = v
        if not existing.get('year') and incoming.get('year'):
            existing['year'] = incoming['year']
    else:
        for k, v in incoming.items():
            if k in {'id', 'topics'} or v is None:
                continue
            existing[k] = v
    existing['topics'] = merge_unique(old_topics, incoming.get('topics') or [])
    existing['bibtex_source'] = 'sources/ref_om.bib'
    promote_id(existing, incoming['id'])
    return existing


def main():
    ap = argparse.ArgumentParser(description='Convert or merge an INSPIRE-style BibTeX file into publications.yaml.')
    ap.add_argument('bib', type=Path)
    ap.add_argument('-o', '--output', type=Path, default=Path('data/publications.yaml'))
    ap.add_argument('--merge', action='store_true', help='Non-destructively enrich an existing YAML file instead of replacing it.')
    args = ap.parse_args()

    parsed = parse_bibtex(args.bib)
    incoming = [make_record(*entry) for entry in parsed]
    ids = [r['id'] for r in incoming]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate citation keys in BibTeX')

    if args.merge and args.output.exists():
        records = yaml.safe_load(args.output.read_text(encoding='utf-8')) or []
        added = updated = 0
        for inc in incoming:
            target = find_existing(records, inc)
            if target is None:
                inc['bibtex_source'] = 'sources/ref_om.bib'
                records.append(inc); added += 1
            else:
                merge_records(target, inc); updated += 1
        records.sort(key=sort_key, reverse=True)
        args.output.write_text(yaml.safe_dump(records, allow_unicode=True, sort_keys=False, width=1000), encoding='utf-8')
        print(f'BibTeX merge: +{added}, updated {updated}, total {len(records)} in {args.output}')
    else:
        records = incoming
        for r in records:
            r['bibtex_source'] = 'sources/ref_om.bib'
        records.sort(key=sort_key, reverse=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(yaml.safe_dump(records, allow_unicode=True, sort_keys=False, width=1000), encoding='utf-8')
        print(f'Wrote {len(records)} records to {args.output}')


if __name__ == '__main__':
    main()
