#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import yaml

from id_utils import promote_id
from sync_utils import merge_unique

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RM_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'sources' / 'rm_researchers.jsonl'
SLIDES_BASE = 'https://o-morikawa.github.io/slides/'
SLIDES_REPO_BASE = 'https://github.com/o-morikawa/o-morikawa.github.io/blob/main/slides/'
RM_PROFILE = 'https://researchmap.jp/o-morikawa'


def load_yaml(name):
    path = DATA / name
    return yaml.safe_load(path.read_text(encoding='utf-8')) or []


def save_yaml(name, data):
    (DATA / name).write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000),
        encoding='utf-8',
    )


def bi(v, lang):
    return v.get(lang) if isinstance(v, dict) else None


def names(v, lang):
    a = (v or {}).get(lang) if isinstance(v, dict) else None
    return [x.get('name') for x in (a or []) if isinstance(x, dict) and x.get('name')]


def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).lower()
    for a, b in {'–':'-','—':'-','−':'-','’':"'",'“':'','”':'','⋆':'star','ℤ':'z','𝒩':'n','θ':'theta','π':'pi','×':'x','ˆ':'^'}.items():
        s = s.replace(a, b)
    s = re.sub(r'\\mathcal\{([^}]+)\}', r'\1', s)
    s = re.sub(r'\\mathbb\{([^}]+)\}', r'\1', s)
    s = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', s)
    s = re.sub(r'\\text\{([^}]+)\}', r'\1', s)
    s = re.sub(r'\\[a-zA-Z]+', ' ', s)
    s = s.replace('$', '').replace('{', '').replace('}', '').replace('~', ' ')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return ' '.join(s.split())


def sim(a, b):
    aa, bb = norm(a), norm(b)
    if not aa or not bb:
        return 0.0
    if aa == bb:
        return 1.0
    return SequenceMatcher(None, aa, bb).ratio()


def month(s):
    return str(s or '')[:7]


def year(s):
    return str(s or '')[:4]


def set_if(rec, key, value, overwrite=False):
    if value is not None and value != '' and (overwrite or not rec.get(key)):
        rec[key] = value


def rm_record_url(typ, rid):
    if typ == 'researchers':
        return RM_PROFILE
    return f'{RM_PROFILE}/{typ}/{rid}'


def add_rm_ref(rec, ins, typ, primary=True):
    rid = str(ins.get('id'))
    url = rm_record_url(typ, rid)
    refs = rec.setdefault('researchmap_refs', [])
    if not any(str(x.get('id')) == rid and x.get('type') == typ for x in refs if isinstance(x, dict)):
        refs.append({'type': typ, 'id': rid, 'url': url})
    # Backward-compatible primary fields.  Correct a stale/wrong primary when the
    # same ResearchMap source type is matched again; do not let a secondary source
    # category erase an already useful primary identity.
    if primary or not rec.get('researchmap_id') or rec.get('researchmap_type') == typ:
        rec['researchmap_id'] = rid
        rec['researchmap_type'] = typ
        rec['researchmap_url'] = url
    rec['researchmap_profile_url'] = RM_PROFILE


def set_bilingual(rec, base, value, canonical_en_key=None, overwrite_ja=True):
    if not isinstance(value, dict):
        return
    ja = bi(value, 'ja')
    en = bi(value, 'en')
    ja_key = f'{base}_ja'
    en_key = canonical_en_key or f'{base}_en'
    if ja and (overwrite_ja or not rec.get(ja_key)):
        rec[ja_key] = ja
    if en:
        if not rec.get(en_key):
            rec[en_key] = en
        elif norm(rec.get(en_key)) != norm(en):
            rec[f'researchmap_{base}_en'] = en


def set_title(rec, value, canonical='title_en'):
    if not isinstance(value, dict):
        return
    ja, en = bi(value, 'ja'), bi(value, 'en')
    if ja:
        rec['title_ja'] = ja
    if en:
        if not rec.get(canonical):
            rec[canonical] = en
        elif norm(rec.get(canonical)) != norm(en):
            rec['researchmap_title_en'] = en


def set_source_date(rec, d, field='start_date'):
    if not d:
        return
    if rec.get('source') == 'researchmap' or not rec.get(field):
        rec[field] = d
        # A source-native record cannot simultaneously have a local/RM date conflict.
        rec.pop('researchmap_date', None)
        rec.pop('date_conflict', None)
        return
    if str(rec.get(field)) != str(d):
        rec['researchmap_date'] = d
        rec['date_conflict'] = True
    else:
        # Clear stale conflict metadata left by an older incorrect match.  Genuine
        # conflicts (for example the author-corrected presentation date) still take
        # the branch above and are preserved.
        rec.pop('researchmap_date', None)
        rec.pop('date_conflict', None)


def see_also(m):
    return [x for x in (m.get('see_also') or []) if isinstance(x, dict) and x.get('@id')]


def first_url(m, label=None, prefix=None):
    for x in see_also(m):
        u = x.get('@id', '')
        if label and x.get('label') != label:
            continue
        if prefix and not u.startswith(prefix):
            continue
        return u
    return None


def arxiv_from_merge(m):
    ids = m.get('identifiers') or {}
    for x in ids.get('arxiv_id') or []:
        mm = re.search(r'(\d{4}\.\d{4,5})', str(x))
        if mm:
            return mm.group(1)
    for x in see_also(m):
        mm = re.search(r'arxiv\.org/(?:abs|pdf)/(?:arXiv:)?(\d{4}\.\d{4,5})', x.get('@id',''), re.I)
        if mm:
            return mm.group(1)
    return None


def doi_from_merge(m):
    ids = m.get('identifiers') or {}
    vals = ids.get('doi') or []
    return vals[0] if vals else None


def record_text(r):
    vals = [r.get('title_en'), r.get('title'), r.get('event_en'), r.get('organization_en'), r.get('description_en'), r.get('work_title_en')]
    return ' '.join(str(x) for x in vals if x)


def best_match(records, title=None, date=None, org=None, kinds=None, min_score=.72, used=None):
    used = used or set()
    candidates = []
    for r in records:
        if id(r) in used:
            continue
        if kinds and r.get('kind') not in kinds:
            continue
        score = max(sim(r.get('title_en') or r.get('title'), title), sim(record_text(r), title)) if title else 0.0
        if title and norm(title) and norm(title) in norm(record_text(r)):
            score = max(score, .93)
        if date:
            if str(r.get('start_date') or '') == str(date):
                score += .28
            elif month(r.get('start_date')) and month(r.get('start_date')) == month(date):
                score += .20
            elif year(r.get('start_date')) and year(r.get('start_date')) == year(date):
                score += .08
        if org:
            os = max(sim(r.get('organization_en'), org), sim(record_text(r), org))
            score += .15 * os
            if norm(org) and norm(org) in norm(record_text(r)):
                score += .08
        candidates.append((score, r))
    if not candidates:
        return None
    sc, r = max(candidates, key=lambda z: z[0])
    return r if sc >= min_score else None


def match_by_rm_id(records, ins, typ):
    rid = str(ins.get('id'))
    for r in records:
        if str(r.get('researchmap_id') or '') == rid and r.get('researchmap_type') == typ:
            return r
        for ref in r.get('researchmap_refs') or []:
            if isinstance(ref, dict) and str(ref.get('id')) == rid and ref.get('type') == typ:
                return r
    return None


def apply_author_corrections(pres):
    old_id = 'presentation-2026-09-14-gradient-flow-actions-integerness-and-gluonic-fermionic-topo'
    for r in pres:
        if r.get('id') == old_id:
            r['legacy_ids'] = merge_unique(r.get('legacy_ids') or [], [old_id])
            r['id'] = 'presentation-2026-09-16-gradient-flow-actions-integerness-and-gluonic-fermionic-topo'
            r['start_date'] = '2026-09-16'
            r['date_note'] = 'Corrected by author on 2026-09-15.'


# ---------- Load ResearchMap JSONL ----------
rms = defaultdict(list)
researcher = None
for line in RM_PATH.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    o = json.loads(line)
    ins, m = o.get('insert', {}), o.get('merge', {})
    typ = ins.get('type')
    if not typ:
        continue
    e = {'insert': ins, 'merge': m}
    rms[typ].append(e)
    if typ == 'researchers':
        researcher = e

stats = defaultdict(lambda: {'matched': 0, 'added': 0})


# ---------- profile ----------
profile = load_yaml('profile.yaml')
if researcher and profile:
    ins, m = researcher['insert'], researcher['merge']
    r = profile[0]
    fnja, gnja = bi(m.get('family_name'), 'ja'), bi(m.get('given_name'), 'ja')
    fnen, gnen = bi(m.get('family_name'), 'en'), bi(m.get('given_name'), 'en')
    if fnja or gnja:
        r['title_ja'] = (fnja or '') + (gnja or '')
    if fnen or gnen:
        rm_name = ' '.join(x for x in [gnen, fnen] if x)
        if not r.get('title_en'):
            r['title_en'] = rm_name
        elif norm(r['title_en']) != norm(rm_name):
            r['researchmap_title_en'] = rm_name
    r['name_kana'] = (bi(m.get('family_name'), 'ja-Kana') or '') + (bi(m.get('given_name'), 'ja-Kana') or '')
    r.setdefault('identifiers', {})['researchmap_internal'] = ins.get('id')
    ids = m.get('identifiers') or {}
    if ids.get('erad_id'):
        r['identifiers']['erad'] = ids['erad_id'][0]
    for x in see_also(m):
        if x.get('label') == 'orcid':
            r['urls']['orcid'] = x['@id']
    # Current affiliation stays locally controlled; preserve ResearchMap's current value separately.
    affs = m.get('affiliations') or []
    if affs:
        a = affs[0]
        r['researchmap_affiliation_en'] = ' '.join(x for x in [bi(a.get('section'),'en'), bi(a.get('affiliation'),'en')] if x)
        r['researchmap_affiliation_ja'] = ' '.join(x for x in [bi(a.get('affiliation'),'ja'), bi(a.get('section'),'ja')] if x)
    r['researchmap_profile_url'] = RM_PROFILE
    save_yaml('profile.yaml', profile)


# ---------- presentations: match then add unmatched ----------
pres = load_yaml('presentations.yaml')
apply_author_corrections(pres)
used = set()
for e in rms['presentations']:
    ins, m = e['insert'], e['merge']
    rid = str(ins['id'])
    te = bi(m.get('presentation_title'),'en') or bi(m.get('presentation_title'),'ja')
    d = m.get('publication_date')
    target = match_by_rm_id(pres, ins, 'presentations')
    if target is None:
        # exact-date + title first; then very-high-confidence title across a date conflict
        target = best_match(pres, te, d, bi(m.get('event'),'en'), min_score=.80, used=used)
        if target is None:
            cands = [(sim(r.get('title_en'), te), r) for r in pres if id(r) not in used]
            if cands:
                sc, cand = max(cands, key=lambda z:z[0])
                if sc >= .985:
                    target = cand
    if target is None:
        ptype = m.get('presentation_type') or ''
        kind = 'poster' if 'poster' in ptype else 'talk'
        target = {
            'id': f'researchmap:presentations:{rid}', 'type':'presentations', 'kind':kind,
            'role':'self', 'presenter':'Okuto Morikawa', 'invited':False,
            'title_en': bi(m.get('presentation_title'),'en') or bi(m.get('presentation_title'),'ja'),
            'title_ja': bi(m.get('presentation_title'),'ja'),
            'event_en': bi(m.get('event'),'en'), 'event_ja':bi(m.get('event'),'ja'),
            'start_date': d, 'year': int(d[:4]) if d and d[:4].isdigit() else None,
            'source':'researchmap',
        }
        pres.append(target); stats['presentations']['added'] += 1
    else:
        stats['presentations']['matched'] += 1
    used.add(id(target))
    add_rm_ref(target, ins, 'presentations', primary=True)
    promote_id(target, f'researchmap:presentations:{rid}')
    set_title(target, m.get('presentation_title'))
    set_bilingual(target, 'event', m.get('event'))
    pe = m.get('presenters')
    if names(pe,'en'): target['presenters_en'] = names(pe,'en')
    if names(pe,'ja'): target['presenters_ja'] = names(pe,'ja')
    if m.get('languages'): target['languages'] = m['languages']
    if m.get('presentation_type'): target['researchmap_presentation_type'] = m['presentation_type']
    set_source_date(target, d)
    ds = m.get('dataset') or {}
    if ds.get('dataset_name'):
        fn = ds['dataset_name']
        target['slides_file'] = fn
        target['slides_url'] = SLIDES_BASE + fn
        target['slides_repo_url'] = SLIDES_REPO_BASE + fn
        if ds.get('access_url'): target['researchmap_attachment_url'] = ds['access_url']

pres.sort(key=lambda r:(str(r.get('start_date') or ''),str(r.get('id') or '')), reverse=True)
save_yaml('presentations.yaml', pres)


# ---------- publications: ResearchMap published_papers ----------
# `other_publications.yaml` is part of the same publication namespace.  A
# ResearchMap published_papers record may therefore enrich an editorial/preface
# already classified locally instead of creating a second paper record.
pubs = load_yaml('publications.yaml')
other = load_yaml('other_publications.yaml')
used_pubs = set()
used_other_published = set()
for e in rms['published_papers']:
    ins, m = e['insert'], e['merge']
    te = bi(m.get('paper_title'),'en') or bi(m.get('paper_title'),'ja')
    d = m.get('publication_date')
    doi = doi_from_merge(m); arxiv = arxiv_from_merge(m)
    target = match_by_rm_id(pubs, ins, 'published_papers')
    target_collection = 'pubs' if target is not None else None
    if target is None:
        target = match_by_rm_id(other, ins, 'published_papers')
        if target is not None:
            target_collection = 'other'
    if target is None and doi:
        target = next((r for r in pubs if str(r.get('doi') or '').lower() == doi.lower()), None)
        if target is not None:
            target_collection = 'pubs'
    if target is None and doi:
        target = next((r for r in other if str(r.get('doi') or '').lower() == doi.lower()), None)
        if target is not None:
            target_collection = 'other'
    if target is None and arxiv:
        target = next((r for r in pubs if str(r.get('arxiv') or '').lower() == arxiv.lower()), None)
        if target is not None:
            target_collection = 'pubs'
    if target is None:
        target = best_match(pubs, te, d, bi(m.get('publication_name'),'en'), min_score=.91, used=used_pubs)
        if target is not None:
            target_collection = 'pubs'
    if target is None:
        target = best_match(other, te, d, bi(m.get('publication_name'),'en'), min_score=.91, used=used_other_published)
        if target is not None:
            target_collection = 'other'
    if target is None:
        target = {
            'id': f'researchmap:published_papers:{ins["id"]}', 'type':'publications', 'kind':'paper',
            'status':'published', 'title':te, 'title_ja':bi(m.get('paper_title'),'ja'),
            'authors':names(m.get('authors'),'en') or names(m.get('authors'),'ja'),
            'year':int(d[:4]) if d and d[:4].isdigit() else None,
            'source':'researchmap',
        }
        pubs.append(target); target_collection = 'pubs'; stats['published_papers']['added'] += 1
    else:
        stats['published_papers']['matched'] += 1
    if target_collection == 'pubs':
        used_pubs.add(id(target))
    else:
        used_other_published.add(id(target))
    add_rm_ref(target, ins, 'published_papers', primary=not bool(target.get('inspire_bibkey')))
    # Publications generated by INSPIRE use `title`; locally classified editorials
    # use `title_en`.  Keep the local English wording canonical in either case.
    rm_en = bi(m.get('paper_title'),'en')
    rm_ja = bi(m.get('paper_title'),'ja')
    canonical_title = target.get('title') or target.get('title_en')
    if rm_ja:
        target['title_ja'] = rm_ja
    if rm_en and canonical_title and norm(canonical_title) != norm(rm_en):
        target['researchmap_title_en'] = rm_en
    elif rm_en and not canonical_title:
        if target_collection == 'pubs': target['title'] = rm_en
        else: target['title_en'] = rm_en
    if not target.get('authors') and names(m.get('authors'),'en'):
        target['authors'] = names(m.get('authors'),'en')
    if doi:
        set_if(target,'doi',doi); set_if(target,'doi_url',f'https://doi.org/{doi}')
    if arxiv:
        set_if(target,'arxiv',arxiv); set_if(target,'arxiv_url',f'https://arxiv.org/abs/{arxiv}')
    pn = m.get('publication_name') or {}
    if bi(pn,'en') and not target.get('journal'): target['journal'] = bi(pn,'en')
    if bi(pn,'ja'): target['publication_name_ja'] = bi(pn,'ja')
    if m.get('volume'): set_if(target,'volume',m.get('volume'))
    if m.get('number'): set_if(target,'number',m.get('number'))
    if m.get('starting_page'): set_if(target,'pages',m.get('starting_page'))
    if d and not target.get('year') and d[:4].isdigit(): target['year'] = int(d[:4])
    if m.get('referee') is not None: target['researchmap_referee'] = m.get('referee')


# ---------- ResearchMap misc: preprints -> publications; abstracts/etc -> other_publications ----------
used_pubs=set(); used_other=set()
for e in rms['misc']:
    ins, m = e['insert'], e['merge']
    te = bi(m.get('paper_title'),'en') or bi(m.get('paper_title'),'ja')
    d = m.get('publication_date')
    arxiv = arxiv_from_merge(m)
    if arxiv:
        target = match_by_rm_id(pubs, ins, 'misc')
        if target is None:
            target = next((r for r in pubs if str(r.get('arxiv') or '').lower()==arxiv.lower()),None)
        if target is None:
            target = best_match(pubs, te, d, None, min_score=.93, used=used_pubs)
        if target is None:
            target={'id':f'researchmap:misc:{ins["id"]}','type':'publications','kind':'paper','status':'preprint',
                    'title':te,'title_ja':bi(m.get('paper_title'),'ja'),'authors':names(m.get('authors'),'en') or names(m.get('authors'),'ja'),
                    'arxiv':arxiv,'arxiv_url':f'https://arxiv.org/abs/{arxiv}','year':int(d[:4]) if d and d[:4].isdigit() else None,
                    'source':'researchmap'}
            pubs.append(target);stats['misc_preprints']['added']+=1
        else:stats['misc_preprints']['matched']+=1
        used_pubs.add(id(target)); add_rm_ref(target,ins,'misc',primary=not bool(target.get('researchmap_id')))
        if bi(m.get('paper_title'),'ja'):target['title_ja']=bi(m.get('paper_title'),'ja')
        if bi(m.get('paper_title'),'en') and norm(target.get('title'))!=norm(bi(m.get('paper_title'),'en')):target['researchmap_title_en']=bi(m.get('paper_title'),'en')
        if not target.get('authors') and names(m.get('authors'),'en'):target['authors']=names(m.get('authors'),'en')
        continue
    target = match_by_rm_id(other,ins,'misc')
    if target is None:
        target=best_match(other,te,d,bi(m.get('publication_name'),'en'),min_score=.83,used=used_other)
    if target is None:
        pn=bi(m.get('publication_name'),'en') or bi(m.get('publication_name'),'ja')
        target={'id':f'researchmap:misc:{ins["id"]}','type':'publications','kind':'meeting_abstract','status':'published',
                'title_en':te,'title_ja':bi(m.get('paper_title'),'ja'),'authors':names(m.get('authors'),'en') or names(m.get('authors'),'ja'),
                'year':int(d[:4]) if d and d[:4].isdigit() else None,'journal':pn,'source':'researchmap'}
        other.append(target);stats['misc_other']['added']+=1
    else:stats['misc_other']['matched']+=1
    used_other.add(id(target)); add_rm_ref(target,ins,'misc',primary=True)
    set_title(target,m.get('paper_title'))
    set_bilingual(target,'publication_name',m.get('publication_name'))
    if m.get('starting_page'): target['starting_page']=m['starting_page']
    doi=doi_from_merge(m)
    if doi:
        set_if(target,'doi',doi);set_if(target,'doi_url',f'https://doi.org/{doi}')

pubs.sort(key=lambda r:(str(r.get('arxiv_date') or f"{r.get('year',0)}-00"),str(r.get('id') or '')),reverse=True)
other.sort(key=lambda r:(str(r.get('year') or ''),str(r.get('id') or '')),reverse=True)
save_yaml('publications.yaml',pubs);save_yaml('other_publications.yaml',other)


# ---------- software ----------
soft=load_yaml('software.yaml');used=set()
for e in rms['works']:
    ins,m=e['insert'],e['merge']
    if m.get('work_type')!='software':
        continue
    te=bi(m.get('work_title'),'en') or bi(m.get('work_title'),'ja')
    name=(te or '').split(':',1)[0].strip()
    target=match_by_rm_id(soft,ins,'works')
    if target is None:
        candidates=[]
        for r in soft:
            if id(r) in used:continue
            sc=max(sim(r.get('title_en'),te),sim(r.get('title_en'),name))
            if norm(r.get('title_en'))==norm(name):sc=1.0
            candidates.append((sc,r))
        if candidates and max(candidates,key=lambda z:z[0])[0]>=.70:target=max(candidates,key=lambda z:z[0])[1]
    if target is None:
        target={'id':f'researchmap:works:{ins["id"]}','type':'software','kind':'repository','title_en':name or te,
                'title_ja':bi(m.get('work_title'),'ja'),'description_en':bi(m.get('description'),'en'),
                'description_ja':bi(m.get('description'),'ja'),'year':int(str(m.get('from_date') or '')[:4]) if str(m.get('from_date') or '')[:4].isdigit() else None,
                'authors':names(m.get('creators'),'en') or names(m.get('creators'),'ja'),'source':'researchmap'}
        soft.append(target);stats['works']['added']+=1
    else:stats['works']['matched']+=1
    used.add(id(target));add_rm_ref(target,ins,'works',primary=True)
    if bi(m.get('work_title'),'ja'):target['title_ja']=bi(m.get('work_title'),'ja')
    if bi(m.get('work_title'),'en') and norm(target.get('title_en'))!=norm(bi(m.get('work_title'),'en')):target['researchmap_title_en']=bi(m.get('work_title'),'en')
    set_bilingual(target,'description',m.get('description'))
    set_bilingual(target,'location',m.get('location'))
    u=first_url(m,prefix='https://github.com/') or first_url(m)
    if u and not target.get('url'):target['url']=u
soft.sort(key=lambda r:(str(r.get('year') or ''),str(r.get('id') or '')),reverse=True)
save_yaml('software.yaml',soft)


# ---------- CV generic non-destructive upsert ----------
cv=load_yaml('cv.yaml')


def add_cv_record(kind, ins, title_en=None, title_ja=None, start=None, end=None, org_en=None, org_ja=None, **extra):
    r={'id':f'researchmap:{ins["type"]}:{ins["id"]}','type':'cv','kind':kind,'title_en':title_en or title_ja,
       'title_ja':title_ja,'start_date':start,'end_date':None if end=='9999' else end,'source':'researchmap'}
    if org_en:r['organization_en']=org_en
    if org_ja:r['organization_ja']=org_ja
    for k,v in extra.items():
        if v is not None and v!='':r[k]=v
    add_rm_ref(r,ins,ins['type'],primary=True)
    cv.append(r)
    return r


def upsert_cv_type(typ, entries, kinds, title_get, date_get=lambda m:None, end_get=lambda m:None, org_get=lambda m:(None,None), enrich=None, new_kind=None, min_score=.72, cross_kinds=None):
    used=set()
    for e in entries:
        ins,m=e['insert'],e['merge'];te,tj=title_get(m);d=date_get(m);oe,oj=org_get(m)
        target=match_by_rm_id(cv,ins,typ)
        search_kinds=cross_kinds or kinds
        if target is None:
            target=best_match(cv,te or tj,d,oe,kinds=search_kinds,min_score=min_score,used=used)
        if target is None:
            target=add_cv_record(new_kind or kinds[0],ins,te,tj,d,end_get(m),oe,oj)
            stats[typ]['added']+=1
        else:
            stats[typ]['matched']+=1
            add_rm_ref(target,ins,typ,primary=(target.get('researchmap_type') in {None,typ}))
            if tj:target['title_ja']=tj
            if te and not target.get('title_en'):target['title_en']=te
            elif te and norm(target.get('title_en'))!=norm(te):target[f'researchmap_title_en']=te
            if oj:target['organization_ja']=oj
            if oe:
                if not target.get('organization_en'):target['organization_en']=oe
                elif norm(target.get('organization_en'))!=norm(oe):target['researchmap_organization_en']=oe
            set_source_date(target,d)
            rend=end_get(m)
            if rend and rend!='9999':
                if target.get('source')=='researchmap' or not target.get('end_date'):target['end_date']=rend
                elif str(target.get('end_date'))!=str(rend):target['researchmap_end_date']=rend
        used.add(id(target))
        if enrich:enrich(target,m,ins)


# career
def enrich_career(r,m,ins):
    set_bilingual(r,'affiliation',m.get('affiliation'));set_bilingual(r,'section',m.get('section'))
    aj,sj=bi(m.get('affiliation'),'ja'),bi(m.get('section'),'ja')
    if aj:r['organization_ja']=' '.join(x for x in [aj,sj] if x)
upsert_cv_type('research_experience',rms['research_experience'],['career'],
               lambda m:(bi(m.get('job'),'en'),bi(m.get('job'),'ja')),
               lambda m:m.get('from_date'),lambda m:m.get('to_date'),
               lambda m:(' '.join(x for x in [bi(m.get('section'),'en'),bi(m.get('affiliation'),'en')] if x),
                         ' '.join(x for x in [bi(m.get('affiliation'),'ja'),bi(m.get('section'),'ja')] if x)),enrich_career,min_score=.66)

# education: compare terminal month heavily; generic scorer gets start date wrong because local degree date is completion date.
used=set()
for e in rms['education']:
    ins,m=e['insert'],e['merge'];te=bi(m.get('note'),'en') or bi(m.get('affiliation'),'en');tj=bi(m.get('note'),'ja') or bi(m.get('affiliation'),'ja')
    target=match_by_rm_id(cv,ins,'education')
    if target is None:
        cands=[]
        for r in cv:
            if r.get('kind')!='education' or id(r) in used:continue
            sc=0
            if month(r.get('start_date'))==month(m.get('to_date')) or month(r.get('end_date'))==month(m.get('to_date')):sc+=.75
            sc+=.2*max(sim(r.get('organization_en'),bi(m.get('affiliation'),'en')),sim(r.get('stage_en'),bi(m.get('note'),'en')))
            cands.append((sc,r))
        if cands and max(cands,key=lambda z:z[0])[0]>=.70:target=max(cands,key=lambda z:z[0])[1]
    if target is None:
        target=add_cv_record('education',ins,te,tj,m.get('from_date'),m.get('to_date'),bi(m.get('affiliation'),'en'),bi(m.get('affiliation'),'ja'),
                             department_en=bi(m.get('department'),'en'),department_ja=bi(m.get('department'),'ja'),course_en=bi(m.get('course'),'en'),course_ja=bi(m.get('course'),'ja'),
                             stage_en=bi(m.get('note'),'en'),stage_ja=bi(m.get('note'),'ja'))
        stats['education']['added']+=1
    else:
        stats['education']['matched']+=1;add_rm_ref(target,ins,'education',primary=True)
        set_bilingual(target,'affiliation',m.get('affiliation'));set_bilingual(target,'department',m.get('department'));set_bilingual(target,'course',m.get('course'))
        if bi(m.get('note'),'ja'):target['stage_ja']=bi(m.get('note'),'ja')
        if bi(m.get('note'),'en'):target['stage_en']=bi(m.get('note'),'en')
        target['education_period_start']=m.get('from_date');target['education_period_end']=m.get('to_date')
    used.add(id(target))

# researcher profile degrees -> matching degree Japanese
if researcher:
    for deg in researcher['merge'].get('degrees') or []:
        dd=deg.get('degree_date')
        cands=[r for r in cv if r.get('kind')=='education' and month(r.get('start_date'))==month(dd)]
        if cands and bi(deg.get('degree'),'ja'):cands[0]['title_ja']=bi(deg.get('degree'),'ja')

# awards one-to-one date-aware
def enrich_award(r,m,ins):
    set_bilingual(r,'description',m.get('description'))
    if names(m.get('winners'),'ja'):r['winners_ja']=names(m.get('winners'),'ja')
    if names(m.get('winners'),'en'):r['winners_en']=names(m.get('winners'),'en')
    u=first_url(m)
    if u:r.setdefault('urls',{}).setdefault('award',u)
upsert_cv_type('awards',rms['awards'],['award'],lambda m:(bi(m.get('award_name'),'en'),bi(m.get('award_name'),'ja')),
               lambda m:m.get('award_date'),lambda m:m.get('award_date'),lambda m:(bi(m.get('association'),'en'),bi(m.get('association'),'ja')),
               enrich_award,min_score=.67)

# teaching
def enrich_teaching(r,m,ins):
    if m.get('to_date') and m.get('to_date')!='9999' and (r.get('source')=='researchmap' or not r.get('end_date')):r['end_date']=m.get('to_date')
upsert_cv_type('teaching_experience',rms['teaching_experience'],['teaching'],lambda m:(bi(m.get('subject_name'),'en'),bi(m.get('subject_name'),'ja')),
               lambda m:m.get('from_date'),lambda m:m.get('to_date'),lambda m:(bi(m.get('institution_name'),'en'),bi(m.get('institution_name'),'ja')),
               enrich_teaching,min_score=.76)

# memberships
upsert_cv_type('association_memberships',rms['association_memberships'],['membership'],lambda m:(bi(m.get('academic_society_name'),'en'),bi(m.get('academic_society_name'),'ja')),
               org_get=lambda m:(None,None),min_score=.72)

# grants/projects: grant number before text/date
used=set()
for e in rms['research_projects']:
    ins,m=e['insert'],e['merge'];ids=m.get('identifiers') or {};nums=(ids.get('national_grant_number') or [])+(ids.get('grant_number') or [])
    target=match_by_rm_id(cv,ins,'research_projects')
    if target is None and nums:
        for r in cv:
            if r.get('kind')!='grant' or id(r) in used:continue
            gn=' '.join([str(r.get('grant_number') or '')]+[str(x) for x in (r.get('grant_numbers') or [])])
            if any(n and n in gn for n in nums):target=r;break
    te=bi(m.get('system_name'),'en') or bi(m.get('research_project_title'),'en');tj=bi(m.get('system_name'),'ja') or bi(m.get('research_project_title'),'ja')
    if target is None:
        target=best_match(cv,te,m.get('from_date'),bi(m.get('offer_organization'),'en'),kinds=['grant'],min_score=.68,used=used)
    if target is None:
        target=add_cv_record('grant',ins,te,tj,m.get('from_date'),m.get('to_date'),bi(m.get('offer_organization'),'en'),bi(m.get('offer_organization'),'ja'),
                             project_title_en=bi(m.get('research_project_title'),'en'),project_title_ja=bi(m.get('research_project_title'),'ja'),
                             system_name_en=bi(m.get('system_name'),'en'),system_name_ja=bi(m.get('system_name'),'ja'))
        stats['research_projects']['added']+=1
    else:
        stats['research_projects']['matched']+=1;add_rm_ref(target,ins,'research_projects',primary=True)
        set_bilingual(target,'project_title',m.get('research_project_title'));set_bilingual(target,'funding_organization',m.get('offer_organization'));set_bilingual(target,'system_name',m.get('system_name'))
        set_source_date(target,m.get('from_date'))
    used.add(id(target))
    if nums:
        if not target.get('grant_number'):target['grant_number']=nums[0]
        target['researchmap_grant_numbers']=nums
    if m.get('research_project_owner_role'):target['role']=m['research_project_owner_role']
    if m.get('overall_grant_amount'):target['amount']=m['overall_grant_amount']
    kaken=first_url(m,label='kaken')
    if kaken:target.setdefault('urls',{})['kaken']=kaken

# committee memberships -> professional service
upsert_cv_type('committee_memberships',rms['committee_memberships'],['professional_service'],
               lambda m:(bi(m.get('committee_name'),'en'),bi(m.get('committee_name'),'ja')),
               lambda m:m.get('from_date'),lambda m:m.get('to_date'),lambda m:(bi(m.get('association'),'en'),bi(m.get('association'),'ja')),
               min_score=.62)

# academic contributions use several CV semantic kinds.  Match only within the
# compatible kind(s) before falling back to a new source-native record.  In
# particular, a dated individual peer review is an Activity and must not be
# collapsed into the standing "Reviewer" professional-service appointment.
def academic_new_kind(m):
    roles = m.get('academic_contribution_roles') or []
    title = (bi(m.get('academic_contribution_title'),'en') or '').lower()
    d = m.get('from_event_date')
    individual_review = 'peer_review' in roles and bool(d) and (
        title.startswith('review ') or title.startswith('review(') or
        title.startswith('review (') or title.startswith('referee report')
    )
    if individual_review:
        return 'activity'
    if 'planning_etc' in roles and ('seminar series' in title or 'conference' in title):
        return 'organizer'
    if 'panel_chair_etc' in roles:
        return 'activity'
    if 'peer_review' in roles and not d:
        return 'professional_service'
    return 'activity'


def academic_match_kinds(m):
    roles = m.get('academic_contribution_roles') or []
    title = (bi(m.get('academic_contribution_title'),'en') or '').lower()
    d = m.get('from_event_date')
    individual_review = 'peer_review' in roles and bool(d) and (
        title.startswith('review ') or title.startswith('review(') or
        title.startswith('review (') or title.startswith('referee report')
    )
    if individual_review:
        return ['activity']
    if 'planning_etc' in roles:
        return ['organizer', 'activity']
    if 'panel_chair_etc' in roles:
        return ['activity']
    if 'peer_review' in roles and not d:
        return ['professional_service']
    return ['activity', 'organizer', 'professional_service', 'social_service']


used=set()
for e in rms['academic_contribution']:
    ins,m=e['insert'],e['merge'];te=bi(m.get('academic_contribution_title'),'en');tj=bi(m.get('academic_contribution_title'),'ja');d=m.get('from_event_date')
    target=match_by_rm_id(cv,ins,'academic_contribution')
    if target is None:
        target=best_match(cv,te,d,bi(m.get('promoter'),'en'),kinds=academic_match_kinds(m),min_score=.58,used=used)
    if target is None:
        target=add_cv_record(academic_new_kind(m),ins,te,tj,d,m.get('to_event_date'),bi(m.get('promoter'),'en'),bi(m.get('promoter'),'ja'))
        stats['academic_contribution']['added']+=1
    else:
        stats['academic_contribution']['matched']+=1;add_rm_ref(target,ins,'academic_contribution',primary=(not target.get('researchmap_id') or target.get('researchmap_type')=='academic_contribution'))
        if tj:target['title_ja']=tj
        if te and not target.get('title_en'):target['title_en']=te
        elif te and norm(target.get('title_en'))!=norm(te):target['researchmap_title_en']=te
        if bi(m.get('promoter'),'ja'):target['organization_ja']=bi(m.get('promoter'),'ja')
        if bi(m.get('promoter'),'en') and not target.get('organization_en'):target['organization_en']=bi(m.get('promoter'),'en')
        set_source_date(target,d)
    used.add(id(target))
    if m.get('academic_contribution_roles'):target['researchmap_roles']=m['academic_contribution_roles']
    set_bilingual(target,'description',m.get('description'))
    u=first_url(m)
    if u and not target.get('url'):target['url']=u

# social contribution: local CV title may describe event/role while RM title describes work, so compare all record text.
used=set()
for e in rms['social_contribution']:
    ins,m=e['insert'],e['merge'];te=bi(m.get('social_contribution_title'),'en');tj=bi(m.get('social_contribution_title'),'ja');d=m.get('from_event_date')
    target=match_by_rm_id(cv,ins,'social_contribution')
    if target is None:
        # Date/year plus event/promoter or work_title is stronger than raw title alone.
        candidates=[]
        for r in cv:
            if r.get('kind')!='social_service' or id(r) in used:continue
            sc=max(sim(record_text(r),te),sim(r.get('work_title_en'),te),sim(record_text(r),bi(m.get('event'),'en')))
            if year(r.get('start_date'))==year(d):sc+=.20
            candidates.append((sc,r))
        if candidates and max(candidates,key=lambda z:z[0])[0]>=.55:target=max(candidates,key=lambda z:z[0])[1]
    if target is None:
        target=add_cv_record('social_service',ins,te,tj,d,m.get('to_event_date'),bi(m.get('promoter'),'en'),bi(m.get('promoter'),'ja'),
                             event_en=bi(m.get('event'),'en'),event_ja=bi(m.get('event'),'ja'))
        stats['social_contribution']['added']+=1
    else:
        stats['social_contribution']['matched']+=1;add_rm_ref(target,ins,'social_contribution',primary=(not target.get('researchmap_id') or target.get('researchmap_type')=='social_contribution'))
        if tj:target['work_title_ja']=tj
        if te:target['work_title_en']=te
        set_bilingual(target,'event',m.get('event'));set_source_date(target,d)
        if bi(m.get('promoter'),'ja'):target['organization_ja']=bi(m.get('promoter'),'ja')
        if bi(m.get('promoter'),'en') and not target.get('organization_en'):target['organization_en']=bi(m.get('promoter'),'en')
    used.add(id(target))
    if m.get('social_contribution_roles'):target['researchmap_roles']=m['social_contribution_roles']
    u=first_url(m)
    if u and not target.get('url'):target['url']=u

# Others: match local award/grant by date/title; otherwise keep as explicit `other`.
used=set()
for e in rms['others']:
    ins,m=e['insert'],e['merge'];te=bi(m.get('other_title'),'en');tj=bi(m.get('other_title'),'ja');d=m.get('from_date')
    target=match_by_rm_id(cv,ins,'others')
    if target is None:target=best_match(cv,te,d,None,kinds=['award','grant'],min_score=.52,used=used)
    if target is None:
        target=add_cv_record('other',ins,te,tj,d,m.get('to_date'))
        stats['others']['added']+=1
    else:
        stats['others']['matched']+=1;add_rm_ref(target,ins,'others',primary=(not target.get('researchmap_id') or target.get('researchmap_type')=='others'))
        if tj:target['title_ja']=tj
        if te and not target.get('title_en'):target['title_en']=te
        elif te and norm(target.get('title_en'))!=norm(te):target['researchmap_title_en']=te
    used.add(id(target));set_bilingual(target,'description',m.get('description'))

# Research interests/areas are source-native CV records if there is no local equivalent.
upsert_cv_type('research_interests',rms['research_interests'],['research_interest'],lambda m:(bi(m.get('keyword'),'en'),bi(m.get('keyword'),'ja')),min_score=.80)

def enrich_area(r,m,ins):
    set_bilingual(r,'discipline',m.get('discipline'))
upsert_cv_type('research_areas',rms['research_areas'],['research_area'],lambda m:(bi(m.get('research_field'),'en'),bi(m.get('research_field'),'ja')),enrich=enrich_area,min_score=.80)

# Media coverage may correspond to a locally classified award; match conceptually first.
used=set()
for e in rms['media_coverage']:
    ins,m=e['insert'],e['merge'];te=bi(m.get('media_coverage_title'),'en');tj=bi(m.get('media_coverage_title'),'ja');d=m.get('publication_date')
    target=match_by_rm_id(cv,ins,'media_coverage')
    if target is None:
        target=best_match(cv,te,d,bi(m.get('publisher'),'en'),kinds=['media_coverage','award'],min_score=.64,used=used)
    if target is None:
        target=add_cv_record('media_coverage',ins,te,tj,d,None,bi(m.get('publisher'),'en'),bi(m.get('publisher'),'ja'),event_en=bi(m.get('event'),'en'),event_ja=bi(m.get('event'),'ja'))
        stats['media_coverage']['added']+=1
    else:
        stats['media_coverage']['matched']+=1;add_rm_ref(target,ins,'media_coverage',primary=(target.get('kind')=='media_coverage'))
        if target.get('kind')=='media_coverage':
            if tj:target['title_ja']=tj
            if te and not target.get('title_en'):target['title_en']=te
        else:
            target['researchmap_media_title_en']=te
            if tj:target['researchmap_media_title_ja']=tj
        set_bilingual(target,'event',m.get('event'))
        if bi(m.get('publisher'),'ja') and not target.get('organization_ja'):target['organization_ja']=bi(m.get('publisher'),'ja')
        if bi(m.get('publisher'),'en') and not target.get('organization_en'):target['organization_en']=bi(m.get('publisher'),'en')
    used.add(id(target));u=first_url(m)
    if u:target.setdefault('urls',{}).setdefault('media',u)

cv.sort(key=lambda r:(str(r.get('start_date') or ''),str(r.get('id') or '')),reverse=True)
save_yaml('cv.yaml',cv)


# ---------- summary ----------
print(f'Presentations: {len(pres)} total; ResearchMap matched {stats["presentations"]["matched"]}, added {stats["presentations"]["added"]}; {sum(bool(r.get("slides_url")) for r in pres)} slide links')
print(f'Publications: {len(pubs)} total; published_papers +{stats["published_papers"]["added"]}, misc preprints +{stats["misc_preprints"]["added"]}')
print(f'Other publications: {len(other)} total; ResearchMap misc added {stats["misc_other"]["added"]}')
print(f'Software: {len(soft)} total; ResearchMap works added {stats["works"]["added"]}')
print(f'CV: {len(cv)} total records')
for typ in ['research_experience','education','awards','teaching_experience','association_memberships','research_projects','committee_memberships','academic_contribution','social_contribution','others','research_interests','research_areas','media_coverage']:
    s=stats[typ]
    print(f'  {typ}: matched {s["matched"]}, added {s["added"]}')
