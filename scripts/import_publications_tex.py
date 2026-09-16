#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from import_bib import arxiv_date, affiliation_from_arxiv, infer_topics, tex_to_text
from sync_utils import load_yaml, merge_unique, norm, same_author_list, save_yaml, section_text, similarity, slug, split_top_level_items

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

JOURNALS = {
    r'\PTEP': 'Prog. Theor. Exp. Phys.',
    r'\PRA': 'Phys. Rev. A',
    r'\PRD': 'Phys. Rev. D',
    r'\PRL': 'Phys. Rev. Lett.',
    r'\PLB': 'Phys. Lett. B',
    r'\JHEP': 'J. High Energy Phys.',
    r'\JPhysA': 'J. Phys. A: Math. Theor.',
    r'\EPJC': 'Eur. Phys. J. C',
    r'\EPJWC': 'EPJ Web Conf.',
    r'\PoS': 'PoS',
    r'\IJMPA': 'Int. J. Mod. Phys. A',
}


def clean_tex(s: str) -> str:
    s = s.replace('\\OM\\', 'O. Morikawa ').replace('\\OM', 'O. Morikawa')
    s = re.sub(r'\\href\{[^{}]*\}\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\url\{([^{}]*)\}', r'\1', s)
    for _ in range(5):
        s = re.sub(r'\\(?:textbf|textit|emph)\{([^{}]*)\}', r'\1', s)
    s = s.replace(r'\&', '&').replace(r'\textasciicircum', '^')
    s = s.replace('\\\\', ' ')
    return tex_to_text(s)


def parse_authors(raw: str):
    text = clean_tex(raw).strip(' ,.;')
    text = re.sub(r'\bet\.\s*al\.?$', 'et. al.', text)
    parts = re.split(r'\s+and\s+|,\s*', text)
    out = []
    for p in parts:
        p = re.sub(r'^and\s+', '', p.strip(), flags=re.I)
        if p: out.append(p)
    return out


def quoted_title(raw: str):
    m = re.search(r"``(.*?)''", raw, re.S)
    if not m:
        return None, None
    return clean_tex(m.group(1)).strip(' ,\n'), m.span()


def italic_title(raw: str):
    m = re.search(r'\\textit\{([^{}]+)\}', raw, re.S)
    if not m:
        return None, None
    return clean_tex(m.group(1)).strip(' ,\n'), m.span()


def parse_jcite(raw: str):
    m = re.search(r'\\Jcite\{([^{}]*)\}\{([^{}]*)\}\{([^{}]*)\}\{([^{}]*)\}', raw, re.S)
    if not m:
        return {}
    doi, journal_macro, volume, detail = [x.strip() for x in m.groups()]
    journal = JOURNALS.get(journal_macro, clean_tex(journal_macro))
    year_m = re.search(r'\((\d{4})\)', detail)
    year = int(year_m.group(1)) if year_m else (int(volume) if volume.isdigit() and len(volume) == 4 else None)
    pages = re.sub(r'\s*\(\d{4}\)\s*$', '', clean_tex(detail)).strip(' ,')
    return {'doi': doi or None, 'journal': journal or None, 'volume': clean_tex(volume) or None, 'pages': pages or None, 'year': year}


def parse_acite(raw: str):
    m = re.search(r'\\Acite\{([^{}]+)\}\{([^{}]+)\}', raw)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip()


def local_id(prefix: str, title: str, year=None):
    return f'{prefix}-{year or "undated"}-{slug(title)}'


def scholarly_record(raw: str, section: str):
    title, span = quoted_title(raw)
    if not title:
        return None
    authors = parse_authors(raw[:span[0]])
    arxiv, primary = parse_acite(raw)
    jc = parse_jcite(raw)
    year = jc.get('year')
    if not year and arxiv:
        d = arxiv_date(arxiv)
        if d:
            year = int(d[:4])
    if not year:
        ym = re.findall(r'\b(19\d{2}|20\d{2})\b', clean_tex(raw))
        if ym:
            year = int(ym[-1])
    if section == 'thesis':
        kind, status = 'thesis', 'thesis'
    elif section == 'proceedings':
        kind, status = 'proceedings', 'published'
    else:
        kind = 'erratum' if title.lower().startswith('erratum') else 'paper'
        status = 'preprint' if section == 'preprint' else 'published'
    rec = {
        'id': local_id('publication', title, year),
        'type': 'publications',
        'kind': kind,
        'status': status,
        'authors': authors,
        'title': title,
        'year': year,
        'source': 'publication.tex',
    }
    for k in ('doi', 'journal', 'volume', 'pages'):
        if jc.get(k):
            rec[k] = jc[k]
    if arxiv:
        rec['arxiv'] = arxiv
        rec['arxiv_url'] = f'https://arxiv.org/abs/{arxiv}'
        d = arxiv_date(arxiv)
        if d:
            rec['arxiv_date'] = d
    if primary:
        rec['arxiv_class'] = primary
    if rec.get('doi'):
        rec['doi_url'] = f'https://doi.org/{rec["doi"]}'
    if section == 'thesis':
        dm = re.search(r'\\DOI\{([^{}]+)\}', raw)
        hm = re.search(r'\\HDL\{([^{}]+)\}', raw)
        if dm:
            rec['doi'] = dm.group(1); rec['doi_url'] = f'https://doi.org/{dm.group(1)}'
        if hm:
            rec['hdl'] = hm.group(1)
        sm = re.search(r'Ph\.D\. Thesis,\s*(.*?)(?:,\s*\d{4}|\\\\)', clean_tex(raw), re.S)
        if sm:
            rec['school'] = sm.group(1).strip(' ,')
    if arxiv:
        aff, basis = affiliation_from_arxiv(arxiv, '', 'article', {})
        rec['affiliation_period'] = aff
        rec['affiliation_basis'] = basis
    rec['topics'] = infer_topics(title, {'primaryClass': primary} if primary else {})
    return rec


def editorial_record(raw: str):
    title, span = italic_title(raw)
    if not title:
        return None
    authors = parse_authors(raw[:span[0]])
    jc = parse_jcite(raw)
    sm = re.search(r'Special Issue:\s*\\textit\{([^{}]+)\}', raw)
    um = re.search(r'\\url\{([^{}]+)\}', raw)
    rec = {
        'id': local_id('editorial', title + '-' + (sm.group(1) if sm else ''), jc.get('year')),
        'type': 'publications', 'kind': 'editorial', 'status': 'published',
        'authors': authors, 'title_en': title, 'title_ja': None, 'year': jc.get('year'),
        'source': 'publication.tex', 'topics': infer_topics((sm.group(1) if sm else title), {}),
    }
    for k in ('doi', 'journal', 'volume', 'pages'):
        if jc.get(k): rec[k] = jc[k]
    if rec.get('doi'): rec['doi_url'] = f'https://doi.org/{rec["doi"]}'
    if sm: rec['special_issue_en'] = clean_tex(sm.group(1))
    if um: rec['url'] = um.group(1)
    return rec


def jps_record(raw: str):
    title, span = quoted_title(raw)
    if not title:
        return None
    authors = parse_authors(raw[:span[0]])
    m = re.search(r'\\JPScite\{([^{}]+)\}\{([^{}]+)\}', raw)
    if not m:
        return None
    volume, detail = m.groups()
    ym = re.search(r'\((\d{4})\)', detail)
    year = int(ym.group(1)) if ym else None
    article = re.sub(r'\s*\(\d{4}\)\s*$', '', clean_tex(detail)).strip(' ,')
    rec = {
        'id': local_id('jps-abstract', title, year), 'type': 'publications', 'kind': 'meeting_abstract',
        'status': 'published', 'authors': authors, 'title_en': title, 'title_ja': None, 'year': year,
        'journal': 'Meeting Abstracts of the Physical Society of Japan', 'volume': clean_tex(volume),
        'article_number': article, 'topics': infer_topics(title, {}), 'source': 'publication.tex',
    }
    gm = re.search(r'\\GLB\{([^{}]+)\}', raw)
    if gm: rec['j_global'] = gm.group(1)
    dm = re.search(r'https://doi\.org/([^}\s]+)', raw)
    if dm:
        rec['doi'] = dm.group(1).replace(r'\_', '_')
        rec['doi_url'] = f'https://doi.org/{rec["doi"]}'
    return rec


def book_record(raw: str):
    title, span = italic_title(raw)
    if not title:
        return None
    authors = parse_authors(raw[:span[0]])
    years = re.findall(r'\b(20\d{2})\b', clean_tex(raw))
    year = int(years[0]) if years else None
    rec = {
        'id': local_id('book', title, year), 'type': 'books', 'kind': 'online_textbook', 'status': 'public',
        'authors': authors, 'title_en': title, 'title_ja': None, 'year': year,
        'topics': infer_topics(title, {}), 'source': 'publication.tex',
    }
    return rec


def software_record(raw: str):
    title, span = quoted_title(raw)
    if not title:
        return None
    authors = parse_authors(raw[:span[0]])
    um = re.search(r'\\url\{([^{}]+)\}', raw)
    years = re.findall(r'\b(20\d{2})\b', clean_tex(raw))
    year = int(years[-1]) if years else None
    desc = None
    if um:
        before = raw[span[1]:um.start()]
        before = re.sub(r'^.*?GitHub:\s*', '', before, flags=re.S)
        desc = clean_tex(before).strip(' ,.;')
    rec = {
        'id': local_id('software', title, year), 'type': 'software', 'kind': 'repository',
        'authors': authors, 'title_en': title, 'title_ja': None, 'year': year,
        'source': 'publication.tex', 'topics': infer_topics(title + ' ' + (desc or ''), {}),
    }
    if desc: rec['description_en'] = desc
    if um: rec['url'] = um.group(1)
    return rec


def find_match(records, incoming, title_key):
    arxiv = incoming.get('arxiv')
    if arxiv:
        for r in records:
            if str(r.get('arxiv') or '') == str(arxiv): return r
    doi = str(incoming.get('doi') or '').lower()
    if doi:
        for r in records:
            if str(r.get('doi') or '').lower() == doi: return r
    url = incoming.get('url')
    if url:
        for r in records:
            if r.get('url') == url: return r
    title = incoming.get(title_key) or incoming.get('title') or incoming.get('title_en')
    exact = [r for r in records if norm(r.get(title_key) or r.get('title') or r.get('title_en')) == norm(title)]
    if len(exact) == 1:
        return exact[0]
    scored = [(similarity(r.get(title_key) or r.get('title') or r.get('title_en'), title), r) for r in records]
    if scored:
        sc, r = max(scored, key=lambda x: x[0])
        if sc >= .985: return r
    return None


def upsert(path: Path, incoming, title_key: str, scholarly=False):
    records = load_yaml(path)
    added = updated = 0
    for inc in incoming:
        if not inc: continue
        r = find_match(records, inc, title_key)
        if r is None:
            records.append(inc); added += 1; continue
        updated += 1
        # LaTeX defines the current roster/title/status, but enrichment fields survive.
        old_topics = r.get('topics') or []
        if scholarly and r.get('inspire_bibkey') and inc.get('authors'):
            if not same_author_list(r.get('authors'), inc['authors']):
                r['authors_latex'] = inc['authors']
            inc = dict(inc); inc.pop('authors', None)
        base_overwrite = {'source', 'title', 'title_en', 'status', 'kind', 'year'}
        for k, v in inc.items():
            if k == 'id' or v is None: continue
            if k == 'topics': continue
            if scholarly and k == 'kind' and r.get('kind') == 'erratum' and v == 'paper':
                # Some CV entries list an erratum under the original title without the word 'Erratum'.
                # Preserve a source-backed erratum classification already supplied by INSPIRE/BibTeX.
                continue
            if scholarly or k in base_overwrite or k == 'authors' or not r.get(k):
                r[k] = v
        new_topics = [t for t in (inc.get('topics') or []) if not (t == 'theoretical physics' and old_topics)]
        r['topics'] = merge_unique(old_topics, new_topics)
    # Deterministic newest-first ordering without deleting records absent from the TeX source.
    def sk(r):
        return (str(r.get('arxiv_date') or r.get('start_date') or r.get('year') or ''), str(r.get('id') or ''))
    records.sort(key=sk, reverse=True)
    save_yaml(path, records)
    return added, updated, len(records)


def parse(path: Path):
    text = path.read_text(encoding='utf-8')
    pubs = []
    for raw in split_top_level_items(section_text(text, 'Journal Articles (peer-reviewed)')):
        pubs.append(scholarly_record(raw, 'journal'))
    for raw in split_top_level_items(section_text(text, 'Preprints')):
        pubs.append(scholarly_record(raw, 'preprint'))
    for raw in split_top_level_items(section_text(text, 'Thesis')):
        pubs.append(scholarly_record(raw, 'thesis'))

    proc = section_text(text, 'Proceedings')
    lattice = section_text(proc, 'Lattice conference (peer-reviewed)', level='subsubsection')
    for raw in split_top_level_items(lattice):
        pubs.append(scholarly_record(raw, 'proceedings'))

    other = []
    for raw in split_top_level_items(section_text(text, 'Editorials / Prefaces')):
        other.append(editorial_record(raw))
    jps = section_text(proc, r'\JPS', level='subsubsection')
    for raw in split_top_level_items(jps):
        other.append(jps_record(raw))

    books = [book_record(raw) for raw in split_top_level_items(section_text(text, 'Other Publications'))]

    software = []
    for raw in split_top_level_items(section_text(text, 'Public Repositories')):
        software.append(software_record(raw))
        if r'\begin{enumerate}' in raw:
            nested = raw[raw.find(r'\begin{enumerate}'):]
            for nr in split_top_level_items(nested):
                software.append(software_record(nr))
    return [x for x in pubs if x], [x for x in other if x], [x for x in books if x], [x for x in software if x]


def main():
    ap = argparse.ArgumentParser(description='Non-destructively upsert publication.tex into the canonical YAML database.')
    ap.add_argument('tex', nargs='?', type=Path, default=ROOT / 'sources' / 'publication.tex')
    args = ap.parse_args()
    pubs, other, books, software = parse(args.tex)
    results = [
        ('publications', upsert(DATA / 'publications.yaml', pubs, 'title', scholarly=True)),
        ('other_publications', upsert(DATA / 'other_publications.yaml', other, 'title_en')),
        ('books', upsert(DATA / 'books.yaml', books, 'title_en')),
        ('software', upsert(DATA / 'software.yaml', software, 'title_en')),
    ]
    for name, (added, updated, total) in results:
        print(f'{name}: +{added}, updated {updated}, total {total}')


if __name__ == '__main__':
    main()
