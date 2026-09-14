#!/usr/bin/env python3
from __future__ import annotations
import json, re, unicodedata, sys
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict
import yaml
from id_utils import promote_id

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RM_PATH = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'sources'/'rm_researchers20260828.jsonl'
SLIDES_BASE = 'https://o-morikawa.github.io/slides/'
SLIDES_REPO_BASE = 'https://github.com/o-morikawa/o-morikawa.github.io/blob/main/slides/'
RM_PROFILE = 'https://researchmap.jp/o-morikawa'


def load_yaml(name):
    return yaml.safe_load((DATA/name).read_text(encoding='utf-8')) or []

def save_yaml(name, data):
    (DATA/name).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120), encoding='utf-8')

def bi(v, lang):
    return v.get(lang) if isinstance(v, dict) else None

def names(v, lang):
    a = (v or {}).get(lang) if isinstance(v, dict) else None
    return [x.get('name') for x in (a or []) if isinstance(x, dict) and x.get('name')]

def norm(s):
    s = unicodedata.normalize('NFKD', s or '').lower()
    for a,b in {'–':'-','—':'-','−':'-','’':"'",'“':'','”':'','⋆':'star','ℤ':'z','𝒩':'n','θ':'theta','π':'pi','×':'x','ˆ':'^'}.items():
        s=s.replace(a,b)
    s=re.sub(r'\\mathcal\{([^}]+)\}', r'\1', s)
    s=re.sub(r'\\mathbb\{([^}]+)\}', r'\1', s)
    s=re.sub(r'\\mathrm\{([^}]+)\}', r'\1', s)
    s=re.sub(r'\\text\{([^}]+)\}', r'\1', s)
    s=re.sub(r'\\[a-zA-Z]+', ' ', s)
    s=s.replace('$','').replace('{','').replace('}','').replace('~',' ')
    s=re.sub(r'[^a-z0-9]+',' ',s)
    return ' '.join(s.split())

def sim(a,b): return SequenceMatcher(None,norm(a),norm(b)).ratio()

def month(s):
    if not s: return ''
    return str(s)[:7]

def set_if(rec, key, value, overwrite=False):
    if value is not None and value != '' and (overwrite or not rec.get(key)):
        rec[key]=value

def add_rm_meta(rec, ins, typ):
    rec['researchmap_id']=str(ins.get('id'))
    rec['researchmap_type']=typ
    rec['researchmap_profile_url']=RM_PROFILE

def rm_url_presentations(rid): return f'{RM_PROFILE}/presentations/{rid}'

# Parse ResearchMap JSONL
rms=defaultdict(list)
researcher=None
for line in RM_PATH.read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    o=json.loads(line); ins=o.get('insert',{}); m=o.get('merge',{}); typ=ins.get('type')
    entry={'insert':ins,'merge':m}
    rms[typ].append(entry)
    if typ=='researchers': researcher=entry

# ---------- presentations ----------
pres=load_yaml('presentations.yaml')
# explicit correction from user
old_id='presentation-2026-09-14-gradient-flow-actions-integerness-and-gluonic-fermionic-topo'
for r in pres:
    if r.get('id')==old_id:
        r['legacy_ids']=[old_id]
        r['id']='presentation-2026-09-16-gradient-flow-actions-integerness-and-gluonic-fermionic-topo'
        r['start_date']='2026-09-16'
        r['date_note']='Corrected by author on 2026-09-15.'

rm_pres=[]
for e in rms['presentations']:
    ins,m=e['insert'],e['merge']
    rm_pres.append({'entry':e,'id':str(ins['id']),'date':m.get('publication_date'),
                    'title_en':bi(m.get('presentation_title'),'en'), 'title_ja':bi(m.get('presentation_title'),'ja')})
bydate_rm=defaultdict(list); bydate_pr=defaultdict(list)
for x in rm_pres: bydate_rm[x['date']].append(x)
for r in pres: bydate_pr[r.get('start_date')].append(r)
matched=[]; used_rm=set(); used_pr=set()
# one-to-one within exact date
for d,rs in bydate_pr.items():
    xs=bydate_rm.get(d,[]); pairs=[]
    for i,r in enumerate(rs):
        for j,x in enumerate(xs): pairs.append((sim(r.get('title_en'),x['title_en']),i,j))
    ui=set();uj=set()
    for sc,i,j in sorted(pairs, reverse=True):
        if sc < .70 or i in ui or j in uj: continue
        ui.add(i);uj.add(j); matched.append((rs[i],xs[j],sc));used_pr.add(id(rs[i]));used_rm.add(xs[j]['id'])
# high-confidence title match across a date discrepancy (notably TQFT 2025)
for r in pres:
    if id(r) in used_pr: continue
    candidates=[]
    for x in rm_pres:
        if x['id'] in used_rm: continue
        sc=sim(r.get('title_en'),x['title_en'])
        if sc>=.985: candidates.append((sc,x))
    if candidates:
        sc,x=max(candidates,key=lambda z:z[0]); matched.append((r,x,sc));used_pr.add(id(r));used_rm.add(x['id'])

for r,x,sc in matched:
    e=x['entry'];ins,m=e['insert'],e['merge']; rid=str(ins['id'])
    add_rm_meta(r,ins,'presentations')
    r['researchmap_url']=rm_url_presentations(rid)
    promote_id(r, f'researchmap:presentations:{rid}')
    rm_title=m.get('presentation_title') or {}; rm_event=m.get('event') or {}
    set_if(r,'title_ja',bi(rm_title,'ja'))
    # preserve exact source values when they differ from canonical display fields
    if bi(rm_title,'en') and bi(rm_title,'en') != r.get('title_en'): r['researchmap_title_en']=bi(rm_title,'en')
    set_if(r,'event_ja',bi(rm_event,'ja'))
    if bi(rm_event,'en') and bi(rm_event,'en') != r.get('event_en'): r['researchmap_event_en']=bi(rm_event,'en')
    pe=m.get('presenters')
    if names(pe,'en'): r['presenters_en']=names(pe,'en')
    if names(pe,'ja'): r['presenters_ja']=names(pe,'ja')
    if m.get('languages'): r['languages']=m['languages']
    if m.get('presentation_type'): r['researchmap_presentation_type']=m['presentation_type']
    if m.get('publication_date') and m.get('publication_date') != r.get('start_date'):
        r['researchmap_date']=m.get('publication_date'); r['date_conflict']=True
    ds=m.get('dataset') or {}
    if ds.get('dataset_name'):
        fn=ds['dataset_name']; r['slides_file']=fn
        r['slides_url']=SLIDES_BASE+fn
        r['slides_repo_url']=SLIDES_REPO_BASE+fn
        if ds.get('access_url'): r['researchmap_attachment_url']=ds['access_url']

save_yaml('presentations.yaml',pres)

# ---------- publications: enrich by DOI/arXiv/title ----------
pubs=load_yaml('publications.yaml')
# indexes
bydoi={str(r.get('doi')).lower():r for r in pubs if r.get('doi')}
byarxiv={str(r.get('arxiv')).lower():r for r in pubs if r.get('arxiv')}
for e in rms['published_papers']:
    ins,m=e['insert'],e['merge']; ids=m.get('identifiers') or {}; target=None
    for doi in ids.get('doi') or []:
        if doi.lower() in bydoi: target=bydoi[doi.lower()]; break
    if not target:
        ar=None
        for sa in m.get('see_also') or []:
            u=sa.get('@id',''); mm=re.search(r'arxiv\.org/(?:abs|pdf)/(?:arXiv:)?([0-9]{4}\.[0-9]{4,5})',u,re.I)
            if mm: ar=mm.group(1);break
        if ar and ar.lower() in byarxiv: target=byarxiv[ar.lower()]
    if not target:
        ten=bi(m.get('paper_title'),'en')
        best=max(((sim(r.get('title'),ten),r) for r in pubs),default=(0,None),key=lambda z:z[0])
        if best[0]>=.985: target=best[1]
    if target:
        add_rm_meta(target,ins,'published_papers')
        tj=bi(m.get('paper_title'),'ja'); te=bi(m.get('paper_title'),'en')
        if tj: target['title_ja']=tj
        if te and te != target.get('title'): target['researchmap_title_en']=te
save_yaml('publications.yaml',pubs)

# ---------- other publications: ResearchMap misc meeting abstracts ----------
other=load_yaml('other_publications.yaml')
for e in rms['misc']:
    ins,m=e['insert'],e['merge']; te=bi(m.get('paper_title'),'en'); tj=bi(m.get('paper_title'),'ja')
    if not te: continue
    # first try existing other publication with title similarity and year/month
    candidates=[]
    for r in other:
        sc=sim(r.get('title_en') or r.get('title'),te)
        if sc>=.88: candidates.append((sc,r))
    if candidates:
        _,r=max(candidates,key=lambda z:z[0]); add_rm_meta(r,ins,'misc'); set_if(r,'title_ja',tj)
        if te and te != r.get('title_en'): r['researchmap_title_en']=te
        pn=m.get('publication_name') or {}; set_if(r,'publication_name_ja',bi(pn,'ja')); set_if(r,'publication_name_en',bi(pn,'en'))
        if m.get('starting_page'): r['starting_page']=m['starting_page']
        continue
    # misc preprints are already in publications.yaml; do not duplicate here
save_yaml('other_publications.yaml',other)

# ---------- software ----------
soft=load_yaml('software.yaml')
for e in rms['works']:
    ins,m=e['insert'],e['merge']; te=bi(m.get('work_title'),'en');tj=bi(m.get('work_title'),'ja')
    if m.get('work_type')!='software' or not te: continue
    rm_name=te.split(':',1)[0].strip()
    candidates=[]
    for rr in soft:
        score=max(sim(rr.get('title_en'),te), sim(rr.get('title_en'),rm_name))
        if norm(rr.get('title_en'))==norm(rm_name): score=1.0
        candidates.append((score,rr))
    best=max(candidates,default=(0,None),key=lambda z:z[0])
    if best[0]>=.70:
        r=best[1]; add_rm_meta(r,ins,'works'); set_if(r,'title_ja',tj)
        if te != r.get('title_en'): r['researchmap_title_en']=te
        dj=bi(m.get('description'),'ja');de=bi(m.get('description'),'en');set_if(r,'description_ja',dj);set_if(r,'description_en',de)
        loc=m.get('location') or {};set_if(r,'location_ja',bi(loc,'ja'));set_if(r,'location_en',bi(loc,'en'))
        for sa in m.get('see_also') or []:
            if sa.get('@id','').startswith('https://github.com/') and not r.get('url'): r['url']=sa['@id']
save_yaml('software.yaml',soft)

# ---------- CV ----------
cv=load_yaml('cv.yaml')
bykind=defaultdict(list)
for r in cv: bykind[r.get('kind')].append(r)
# profile
if researcher:
    m=researcher['merge']; profile=next((r for r in cv if r.get('id')=='cv-profile'),None)
    if profile:
        profile['title_ja']=(bi(m.get('family_name'),'ja') or '')+(bi(m.get('given_name'),'ja') or '')
        profile['name_kana']=(bi(m.get('family_name'),'ja-Kana') or '')+(bi(m.get('given_name'),'ja-Kana') or '')
        profile['researchmap_id']=researcher['insert'].get('id')
# career exact-ish
for e in rms['research_experience']:
    ins,m=e['insert'],e['merge']; st=m.get('from_date'); joben=bi(m.get('job'),'en')
    cands=[r for r in bykind['career'] if r.get('start_date')==st]
    if cands:
        r=max(cands,key=lambda rr: sim(rr.get('title_en'),joben)); add_rm_meta(r,ins,'research_experience')
        set_if(r,'title_ja',bi(m.get('job'),'ja'))
        aj=bi(m.get('affiliation'),'ja'); sj=bi(m.get('section'),'ja')
        if aj: r['affiliation_ja']=aj
        if sj: r['section_ja']=sj
        ae=bi(m.get('affiliation'),'en'); se=bi(m.get('section'),'en')
        if ae: r['affiliation_en']=ae
        if se: r['section_en']=se
        if aj: r['organization_ja']=' '.join(x for x in [aj,sj] if x)
# education periods -> degree records by terminal month
for e in rms['education']:
    ins,m=e['insert'],e['merge']; end=m.get('to_date')
    cands=[r for r in bykind['education'] if month(r.get('start_date'))==month(end) or month(r.get('end_date'))==month(end)]
    if not cands: continue
    r=cands[0]; add_rm_meta(r,ins,'education')
    aj=bi(m.get('affiliation'),'ja'); dj=bi(m.get('department'),'ja'); cj=bi(m.get('course'),'ja')
    if aj: r['affiliation_ja']=aj
    if dj: r['department_ja']=dj
    if cj: r['course_ja']=cj
    if bi(m.get('note'),'ja'): r['stage_ja']=bi(m.get('note'),'ja')
    if bi(m.get('note'),'en'): r['stage_en']=bi(m.get('note'),'en')
    r['education_period_start']=m.get('from_date'); r['education_period_end']=m.get('to_date')
# PhD degree Japanese from researcher profile degree
if researcher:
    for deg in researcher['merge'].get('degrees') or []:
        if deg.get('degree_date')=='2021-03':
            r=next((x for x in bykind['education'] if str(x.get('start_date','')).startswith('2021-03')),None)
            if r: set_if(r,'title_ja',bi(deg.get('degree'),'ja'))
# awards title similarity regardless date
for e in rms['awards']:
    ins,m=e['insert'],e['merge']; te=bi(m.get('award_name'),'en')
    best=max(((sim(r.get('title_en'),te),r) for r in bykind['award']),default=(0,None),key=lambda z:z[0])
    if best[0]>=.55:
        r=best[1];add_rm_meta(r,ins,'awards');set_if(r,'title_ja',bi(m.get('award_name'),'ja'))
        set_if(r,'organization_ja',bi(m.get('association'),'ja'));set_if(r,'organization_en',bi(m.get('association'),'en'))
        set_if(r,'description_ja',bi(m.get('description'),'ja'));set_if(r,'description_en',bi(m.get('description'),'en'))
        if names(m.get('winners'),'ja'):r['winners_ja']=names(m.get('winners'),'ja')
        if names(m.get('winners'),'en'):r['winners_en']=names(m.get('winners'),'en')
        if m.get('award_date') and month(r.get('start_date'))!=month(m['award_date']):r['researchmap_date']=m['award_date']
# teaching exact date+subject, then same-subject translation propagation
subj_ja={}
for e in rms['teaching_experience']:
    ins,m=e['insert'],e['merge']; te=bi(m.get('subject_name'),'en');tj=bi(m.get('subject_name'),'ja')
    if te and tj:subj_ja[norm(te)]=tj
    cands=[r for r in bykind['teaching'] if r.get('start_date')==m.get('from_date') and sim(r.get('title_en'),te)>=.8]
    if cands:
        r=cands[0];add_rm_meta(r,ins,'teaching_experience');set_if(r,'title_ja',tj)
        set_if(r,'organization_ja',bi(m.get('institution_name'),'ja'));set_if(r,'organization_en',bi(m.get('institution_name'),'en'))
for r in bykind['teaching']:
    if not r.get('title_ja') and norm(r.get('title_en')) in subj_ja:r['title_ja']=subj_ja[norm(r.get('title_en'))]
# memberships
for e in rms['association_memberships']:
    ins,m=e['insert'],e['merge']; te=bi(m.get('academic_society_name'),'en')
    best=max(((sim(r.get('title_en'),te),r) for r in bykind['membership']),default=(0,None),key=lambda z:z[0])
    if best[0]>=.7:
        r=best[1];add_rm_meta(r,ins,'association_memberships');set_if(r,'title_ja',bi(m.get('academic_society_name'),'ja'))
# grants: grant number first, else start date + system/title clues
for e in rms['research_projects']:
    ins,m=e['insert'],e['merge']; ids=m.get('identifiers') or {}; nums=(ids.get('national_grant_number') or [])+(ids.get('grant_number') or [])
    r=None
    for rr in bykind['grant']:
        gn=str(rr.get('grant_number') or '')
        if any(n and n in gn for n in nums): r=rr;break
    if not r:
        st=m.get('from_date'); sysen=bi(m.get('system_name'),'en') or ''; cands=[rr for rr in bykind['grant'] if rr.get('start_date')==st]
        if cands:
            r=max(cands,key=lambda rr:max(sim(rr.get('title_en'),sysen),sim(rr.get('title_en'),bi(m.get('research_project_title'),'en'))))
            # avoid weak accidental mapping of the Tsukuba project to another 2025 grant
            if max(sim(r.get('title_en'),sysen),sim(r.get('title_en'),bi(m.get('research_project_title'),'en'))) < .35:r=None
    if r:
        add_rm_meta(r,ins,'research_projects')
        set_if(r,'project_title_ja',bi(m.get('research_project_title'),'ja'));set_if(r,'project_title_en',bi(m.get('research_project_title'),'en'))
        set_if(r,'funding_organization_ja',bi(m.get('offer_organization'),'ja'));set_if(r,'funding_organization_en',bi(m.get('offer_organization'),'en'))
        set_if(r,'system_name_ja',bi(m.get('system_name'),'ja'));set_if(r,'system_name_en',bi(m.get('system_name'),'en'))
        if m.get('research_project_owner_role'):r['role']=m['research_project_owner_role']
        if m.get('overall_grant_amount'):r['amount']=m['overall_grant_amount']
    else:
        # preserve ResearchMap-only research project
        nr={'id':f"cv-research-project-{ins['id']}",'type':'cv','kind':'grant',
            'title_en':bi(m.get('system_name'),'en') or bi(m.get('research_project_title'),'en'),
            'title_ja':bi(m.get('system_name'),'ja') or bi(m.get('research_project_title'),'ja'),
            'project_title_en':bi(m.get('research_project_title'),'en'),'project_title_ja':bi(m.get('research_project_title'),'ja'),
            'start_date':m.get('from_date'),'end_date':m.get('to_date'),'researchmap_id':str(ins['id']),'researchmap_type':'research_projects',
            'researchmap_profile_url':RM_PROFILE,'source':'researchmap'}
        set_if(nr,'funding_organization_en',bi(m.get('offer_organization'),'en'));set_if(nr,'funding_organization_ja',bi(m.get('offer_organization'),'ja'))
        if m.get('research_project_owner_role'):nr['role']=m['research_project_owner_role']
        cv.append(nr);bykind['grant'].append(nr)
# scholarships and graduate representatives from others: title-match existing award/grant
for e in rms['others']:
    ins,m=e['insert'],e['merge']; te=bi(m.get('other_title'),'en');tj=bi(m.get('other_title'),'ja'); best=(0,None)
    for k in ['award','grant']:
        for r in bykind[k]:
            sc=sim(r.get('title_en'),te)
            if sc>best[0]:best=(sc,r)
    if best[0]>=.45:
        r=best[1];add_rm_meta(r,ins,'others');set_if(r,'title_ja',tj);set_if(r,'description_ja',bi(m.get('description'),'ja'));set_if(r,'description_en',bi(m.get('description'),'en'))
# professional service / organizer / activity / social service: title similarity across relevant kinds
for typ, titlekey, orgkey, datekey in [
    ('committee_memberships','committee_name','association','from_date'),
    ('academic_contribution','academic_contribution_title','promoter','from_event_date'),
    ('social_contribution','social_contribution_title','promoter','from_event_date')]:
    for e in rms[typ]:
        ins,m=e['insert'],e['merge']; te=bi(m.get(titlekey),'en');tj=bi(m.get(titlekey),'ja'); d=m.get(datekey)
        candidates=[]
        for k in ['professional_service','organizer','activity','social_service']:
            for r in bykind[k]:
                sc=sim(r.get('title_en'),te)
                if d and month(r.get('start_date'))==month(d): sc+=.2
                candidates.append((sc,r))
        if candidates and max(candidates,key=lambda z:z[0])[0]>=.65:
            _,r=max(candidates,key=lambda z:z[0]); add_rm_meta(r,ins,typ);set_if(r,'title_ja',tj)
            set_if(r,'organization_ja',bi(m.get(orgkey),'ja'));set_if(r,'organization_en',bi(m.get(orgkey),'en'))
            if bi(m.get('description'),'ja'):r['description_ja']=bi(m.get('description'),'ja')
            if bi(m.get('description'),'en'):r['description_en']=bi(m.get('description'),'en')
# research interests (add; no existing equivalents)
existing_ids={r['id'] for r in cv}
for e in rms['research_interests']:
    ins,m=e['insert'],e['merge']; rid=f"cv-research-interest-{ins['id']}"
    if rid not in existing_ids:
        cv.append({'id':rid,'type':'cv','kind':'research_interest','title_en':bi(m.get('keyword'),'en'),'title_ja':bi(m.get('keyword'),'ja'),
                   'researchmap_id':str(ins['id']),'researchmap_type':'research_interests','researchmap_profile_url':RM_PROFILE,'source':'researchmap'})
        existing_ids.add(rid)
for e in rms['research_areas']:
    ins,m=e['insert'],e['merge'];rid=f"cv-research-area-{ins['id']}"
    if rid not in existing_ids:
        cv.append({'id':rid,'type':'cv','kind':'research_area','title_en':bi(m.get('research_field'),'en'),'title_ja':bi(m.get('research_field'),'ja'),
                   'discipline_en':bi(m.get('discipline'),'en'),'discipline_ja':bi(m.get('discipline'),'ja'),
                   'researchmap_id':str(ins['id']),'researchmap_type':'research_areas','researchmap_profile_url':RM_PROFILE,'source':'researchmap'})
# media coverage: add standalone records except Staff Picks which already exists as an award
for e in rms['media_coverage']:
    ins,m=e['insert'],e['merge']; te=bi(m.get('media_coverage_title'),'en');
    existing=max([sim(r.get('title_en'),te) for r in cv] or [0])
    if existing>=.72: continue
    cv.append({'id':f"cv-media-{ins['id']}",'type':'cv','kind':'media_coverage','title_en':te,'title_ja':bi(m.get('media_coverage_title'),'ja'),
               'start_date':m.get('publication_date'),'organization_en':bi(m.get('publisher'),'en'),'organization_ja':bi(m.get('publisher'),'ja'),
               'event_en':bi(m.get('event'),'en'),'event_ja':bi(m.get('event'),'ja'),
               'researchmap_id':str(ins['id']),'researchmap_type':'media_coverage','researchmap_profile_url':RM_PROFILE,'source':'researchmap'})

save_yaml('cv.yaml',cv)

# summary
print(f'Presentations: {len(pres)} total, {len(matched)} matched to ResearchMap, {sum(bool(r.get("slides_url")) for r in pres)} slide links')
print(f'CV: {len(cv)} records after ResearchMap enrichment/additions')
print(f'Publications: {sum(bool(r.get("researchmap_id")) for r in pubs)}/{len(pubs)} linked to ResearchMap')
print(f'Other publications: {sum(bool(r.get("researchmap_id")) for r in other)}/{len(other)} linked to ResearchMap')
print(f'Software: {sum(bool(r.get("researchmap_id")) for r in soft)}/{len(soft)} linked to ResearchMap')
