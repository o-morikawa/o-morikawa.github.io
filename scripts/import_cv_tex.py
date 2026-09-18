#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from sync_utils import load_yaml, save_yaml, norm, similarity, slug, merge_unique

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEX = ROOT / 'sources' / 'cv.tex'
DEFAULT_YAML = ROOT / 'data' / 'cv.yaml'
DEFAULT_PROFILE = ROOT / 'data' / 'profile.yaml'

# Sections actually used in the author's CV.  The parser is deliberately
# heading/text based rather than tied to a particular table environment, so
# the author's existing LaTeX formatting can evolve without changing the DB.
SECTION_KIND = {
    'Career History': 'career',
    'Academic Degrees': 'education',
    'Awards': 'award',
    'Grants and Rewards': 'grant',
    'Professional Memberships': 'membership',
    'Conference/Symposium Organizer': 'organizer',
    'Professional Service': 'professional_service',
    'Social Service': 'social_service',
    'Other Activities': 'activity',
    'Visits (more than 2 weeks)': 'visit',
}

SUBSECTION_KIND = {
    'Lectures': 'teaching',
    'Teaching Assistant': 'teaching',
    'Student Mentorship': 'mentorship',
}

ALL_HEADINGS = [
    'Personal Data',
    *SECTION_KIND.keys(),
    'Languages',
    'Teaching Experience',
    *SUBSECTION_KIND.keys(),
    'Computer Skills',
    'Visits (more than 2 weeks)',
    'Social Service',
    'Other Activities',
]

DATE_PREFIX = re.compile(
    r'^\s*'
    r'(?P<y1>\d{4})'
    r'(?:\.(?P<m1>\d{1,2}))?'
    r'(?:\.(?P<d1>\d{1,2}))?'
    r'(?:\s*[-–—]\s*'
    r'(?:(?P<present>present)|'
    r'(?:(?P<y2>\d{4})(?:\.(?P<m2>\d{1,2}))?(?:\.(?P<d2>\d{1,2}))?|'
    r'(?P<short_md>\d{1,2}\.\d{1,2})|'
    r'(?P<short>\d{1,2})))'
    r')?\s+'
    r'(?P<body>.+)$',
    re.I,
)


# Author macros used in the long-lived CV source.  Expanding these before the
# generic LaTeX cleanup keeps the author's compact TeX notation compatible
# with stable database matching.  Unknown macros are still handled by the
# generic fallback below, so adding a cosmetic macro does not break parsing.
AUTHOR_MACROS = {
    r'\\ithemsC': 'Center for Interdisciplinary Theoretical and Mathematical Sciences (iTHEMS), RIKEN',
    r'\\ithemsP': 'Interdisciplinary Theoretical and Mathematical Sciences Program (iTHEMS), RIKEN',
    r'\\OsakaPhys': 'Department of Physics, Osaka University',
    r'\\OsakaU': 'Osaka University',
    r'\\KyushuPhys': 'Department of Physics, Kyushu University',
    r'\\KyushuU': 'Kyushu University',
    r'\\JSPS': 'Japan Society for the Promotion of Science',
    r'\\SG': 'Japan Particle and Nuclear Theory Forum',
    r'\\JPS': 'The Physical Society of Japan',
    r'\\KAKENHI': 'JSPS Grant-in-Aid for Scientific Research (KAKENHI)',
    r'\\PTEP': 'PTEP',
    r'\\JHEP': 'J. High Energy Phys.',
    r'\\SciPostCore': 'SciPost Physics Core',
    r'\\IJMPA': 'Int. J. Mod. Phys. A',
    r'\\PLB': 'Phys. Lett. B',
}


def strip_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        # Unescaped % starts a comment.
        m = re.search(r'(?<!\\)%', line)
        if m:
            line = line[:m.start()]
        out.append(line)
    return '\n'.join(out)


def _unwrap_command(text: str, command: str) -> str:
    # Repeat because formatting commands can be nested.
    pat = re.compile(r'\\' + re.escape(command) + r'\s*\{([^{}]*)\}')
    prev = None
    while prev != text:
        prev = text
        text = pat.sub(lambda m: m.group(1), text)
    return text


def tex_to_plain(text: str) -> str:
    text = strip_comments(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Stable author macros carry semantic text (institutions/journals), so expand
    # them before the generic command stripper sees them.
    for macro, value in AUTHOR_MACROS.items():
        text = re.sub(macro + r'(?![A-Za-z@])', value, text)
    # TeX often uses `\ ` after a macro to force a space.  Once the macro is
    # expanded, that control-space is just ordinary whitespace.
    text = text.replace(r'\ ', ' ')
    # Identifier helpers occur in the CV's degree/citation rows.  For DB parsing
    # the identifier itself is the useful part; the base URL is reconstructed
    # explicitly by the schema/export layer.
    text = re.sub(r'\\ID\s*\{[^{}]+\}\s*\{([^{}]+)\}', r'\1', text)
    text = re.sub(r'\\DOI\s*\{([^{}]+)\}', r'\1', text)
    # Links first, while brace structure is still intact.
    text = re.sub(r'\\href\s*\{([^{}]+)\}\s*\{([^{}]*)\}', lambda m: f'{m.group(2)} [{m.group(1)}]', text)
    text = re.sub(r'\\url\s*\{([^{}]+)\}', lambda m: m.group(1), text)
    text = text.replace(r'\OM', 'Okuto Morikawa')
    text = text.replace(r'\&', '&').replace(r'\_', '_').replace(r'\%', '%').replace(r'\#', '#')
    text = text.replace(r'\textasciicircum', '^')
    text = text.replace(r'\textendash', '–').replace(r'\textemdash', '—')
    for cmd in ['textbf', 'textit', 'emph', 'textrm', 'textsf', 'texttt', 'underline', 'mbox', 'mathrm', 'mathbf', 'mathit']:
        text = _unwrap_command(text, cmd)
    # Common mathematical typography occurring in names/titles.
    repl = {
        r'\mathcal{N}': 'N', r'\mathbb{Z}': 'Z', r'\mathbb{R}': 'R', r'\mathbb{C}': 'C',
        r'\theta': 'theta', r'\pi': 'pi', r'\times': 'x', r'\star': '*',
        r'\,': ' ', r'\!': '', r'~': ' ',
    }
    for a, b in repl.items():
        text = text.replace(a, b)
    # LaTeX row breaks are semantic line breaks for the CV tables/lists.
    text = re.sub(r'\\\\(?:\[[^\]]*\])?', '\n', text)
    # Environment/section commands: keep their argument text when useful.
    text = re.sub(r'\\(?:section|subsection|subsubsection)\*?\s*\{([^{}]+)\}', r'\n\1\n', text)
    text = re.sub(r'\\(?:begin|end)\s*\{[^{}]+\}(?:\[[^\]]*\])?', '\n', text)
    text = re.sub(r'\\(?:item|noindent|small|normalsize|footnotesize|scriptsize|centering|raggedright)\b', ' ', text)
    # Remaining simple commands: drop the command name, retain grouped content.
    text = re.sub(r'\\[A-Za-z@]+\*?(?:\[[^\]]*\])?', ' ', text)
    text = text.replace('$', '')
    text = text.replace('{', '').replace('}', '')
    text = text.replace('&', ' ')
    text = text.replace('---', '—').replace('--', '–')
    # Normalize each line but retain line boundaries for continuation grouping.
    lines = []
    for raw in text.splitlines():
        s = re.sub(r'\s+', ' ', raw).strip(' \t|')
        if s:
            lines.append(s)
    return '\n'.join(lines)


def iso_date(y: str, m: str | None = None, d: str | None = None) -> str:
    if m is None:
        return f'{int(y):04d}'
    if d is None:
        return f'{int(y):04d}-{int(m):02d}'
    return f'{int(y):04d}-{int(m):02d}-{int(d):02d}'


def parse_date_prefix(line: str):
    m = DATE_PREFIX.match(line)
    if not m:
        return None
    y1, mo1, d1 = m.group('y1'), m.group('m1'), m.group('d1')
    start = iso_date(y1, mo1, d1)
    end = None
    if m.group('present'):
        end = None
    elif m.group('y2'):
        end = iso_date(m.group('y2'), m.group('m2'), m.group('d2'))
    elif m.group('short_md'):
        sm, sd = m.group('short_md').split('.', 1)
        end = iso_date(y1, sm, sd)
    elif m.group('short'):
        short = m.group('short')
        # A shortened right endpoint uses the finest precision shown on the left.
        if d1:
            end = iso_date(y1, mo1, short)
        elif mo1:
            end = iso_date(y1, short, None)
        else:
            end = iso_date(short, None, None)  # practically unused; kept deterministic
    return start, end, m.group('body').strip()


def find_heading_indices(lines: list[str]):
    found = []
    for i, line in enumerate(lines):
        n = norm(line)
        for h in ALL_HEADINGS:
            if n == norm(h):
                found.append((i, h))
                break
    found.sort()
    return found


def block_between(lines: list[str], heading: str):
    hs = find_heading_indices(lines)
    for idx, (i, h) in enumerate(hs):
        if h == heading:
            j = hs[idx + 1][0] if idx + 1 < len(hs) else len(lines)
            return lines[i + 1:j]
    return []


def group_dated_entries(lines: list[str]):
    out = []
    current = None
    for line in lines:
        parsed = parse_date_prefix(line)
        if parsed:
            if current:
                out.append(current)
            start, end, body = parsed
            current = {'start_date': start, 'end_date': end, 'parts': [body]}
        elif current:
            current['parts'].append(line)
    if current:
        out.append(current)
    for e in out:
        parts = e.pop('parts')
        e['headline'] = parts[0].strip() if parts else ''
        e['text'] = ' '.join(parts).strip()
    return out


def split_title_org(text: str, kind: str):
    s = text.strip(' ,.;')
    title, org = s, None
    if kind == 'education':
        core = re.split(r'\s+Thesis Title:', s, maxsplit=1, flags=re.I)[0].strip()
        if ',' in core:
            title, org = [x.strip() for x in core.split(',', 1)]
        else:
            title = core
    elif kind == 'career' and ',' in s:
        title, org = [x.strip() for x in s.split(',', 1)]
    elif kind == 'award':
        core = re.split(r'\s+Research Title:', s, maxsplit=1, flags=re.I)[0].strip()
        # Award organizations in this CV are introduced after the first comma.
        m = re.match(r'^(.*?),(\s*(?:The |Japan |Kyushu |Wolfram |Soryushi |Shinkawa ).*)$', core, re.I)
        if m:
            title, org = m.group(1).strip(), m.group(2).strip()
        else:
            title = core
    elif kind == 'grant':
        title = re.split(r'\s+Grant Number:', s, maxsplit=1, flags=re.I)[0].strip()
    elif kind == 'professional_service':
        parts = [x.strip() for x in s.split(',') if x.strip()]
        if len(parts) >= 2:
            title = parts[-1]
            org = ', '.join(parts[:-1])
    elif kind == 'organizer':
        # Keep the role phrase as title and the rest as event text.
        m = re.match(r'((?:Organizer|Chair|Editor)[^,]*(?:,\s*(?:chair|editor)[^,]*)*)\s*,\s*(.+)', s, re.I)
        if m:
            title, org = m.group(1).strip(), m.group(2).strip()
    return title, org


def make_id(kind: str, start: str | None, title: str):
    return f'cv-{kind}-{start or "undated"}-{slug(title, 64)}'


def parse_generic_section(lines: list[str], kind: str):
    records = []
    for e in group_dated_entries(lines):
        text = e['text']
        headline = e.get('headline') or text
        title, org = split_title_org(headline, kind)
        activity_doi = None
        if kind == 'activity' and re.match(r'Referee Report on\b', title, re.I):
            # Keep the bibliographic citation in the visible activity title.  Only
            # the DOI identifier itself is split into structured metadata; otherwise
            # the HTML would stop after the quoted manuscript title and hide the
            # journal/citation information present in the author's CV.
            dm = re.search(r'(?:DOI:\s*)?(10\.\d{4,9}/\S+)\s*$', headline, re.I)
            if dm:
                activity_doi = dm.group(1).rstrip('.,;')
                title = headline[:dm.start()].rstrip(' ,.;')
            else:
                title = headline.strip(' ,.;')
        identity_text = title if not org else f'{title} {org}'
        rec = {
            'id': make_id(kind, e['start_date'], identity_text),
            'type': 'cv', 'kind': kind,
            'title_en': title,
            'start_date': e['start_date'],
            'source': 'cv.tex',
            '_latex_text': text,
        }
        if e['end_date']:
            rec['end_date'] = e['end_date']
        if org:
            if kind == 'organizer':
                rec['event_en'] = org
            else:
                rec['organization_en'] = org
        # Section-specific extractions.
        gm = re.search(r'Grant Number:\s*([^.;]+)', text, re.I)
        if gm:
            nums = re.findall(r'JP?[A-Z0-9]+|\b\d{2}[A-Z]\d+\b', gm.group(1))
            if nums:
                rec['grant_number'] = nums[0]
                if len(nums) > 1:
                    rec['grant_numbers'] = nums
        if kind == 'award':
            rm = re.search(r'Research Title:\s*(?:``|“|")?(.*?)(?:\'\'|”|")?$', text, re.I)
            if rm:
                rec['description_en'] = rm.group(1).strip(' ,.;\'"')
        if activity_doi:
            rec['doi'] = activity_doi
            rec['doi_url'] = 'https://doi.org/' + activity_doi
        records.append(rec)
    return records


def parse_teaching(lines: list[str], role: str):
    records = []
    for e in group_dated_entries(lines):
        text = e.get('headline') or e['text']
        qm = re.search(r'(?:``|“|")(.*?)(?:\'\'|”|")', text)
        title = qm.group(1).strip(' ,') if qm else text.split(',', 1)[0].strip()
        org = None
        tail = text[qm.end():] if qm else text
        im = re.search(r'Undergraduate class\s+in\s+(.+)$', tail, re.I)
        if im:
            org = im.group(1).strip(' ,.;')
        rec = {'id': make_id('teaching', e['start_date'], title), 'type':'cv','kind':'teaching',
               'title_en':title,'start_date':e['start_date'],'role':role,'source':'cv.tex','_latex_text':text}
        if e['end_date']: rec['end_date']=e['end_date']
        if org: rec['organization_en']=org
        records.append(rec)
    return records


def parse_mentorship(lines: list[str]):
    records = []
    for e in group_dated_entries(lines):
        text = e['text']
        level = None
        lm = re.match(r'\(([^)]+)\)\s*(.*)', text)
        if lm:
            level, text2 = lm.group(1), lm.group(2)
        else:
            text2 = text
        parts = [x.strip() for x in text2.rsplit(',', 1)]
        people_text = parts[0]
        org = parts[1] if len(parts) == 2 else None
        # Remove bracketed dissertation notes before name splitting.
        people_clean = re.sub(r'\[[^\]]*\]', '', people_text)
        names = [x.strip(' ,') for x in re.split(r'\s+and\s+|\s*,\s*', people_clean) if x.strip()]
        # Initials are part of names, so only split on comma if it actually produced plausible person tokens.
        if any(len(n.split()) < 2 for n in names):
            names = [x.strip(' ,') for x in re.split(r'\s+and\s+', people_clean) if x.strip()]
        for name in names:
            rec={'id':make_id('mentorship',e['start_date'],name),'type':'cv','kind':'mentorship',
                 'title_en':name,'start_date':e['start_date'],'source':'cv.tex','_latex_text':e['text']}
            if e['end_date']: rec['end_date']=e['end_date']
            if level: rec['level_en']=level
            if org: rec['organization_en']=org
            records.append(rec)
    return records


def parse_languages(lines: list[str]):
    text=' '.join(lines).strip()
    out=[]
    if not text: return out
    if re.search(r'\bJapanese\b',text,re.I):
        r={'id':'cv-language-japanese','type':'cv','kind':'language','title_en':'Japanese','source':'cv.tex'}
        if re.search(r'Japanese\s*\(Native\)',text,re.I): r['level_en']='Native'
        out.append(r)
    if re.search(r'\bEnglish\b',text,re.I):
        out.append({'id':'cv-language-english','type':'cv','kind':'language','title_en':'English','source':'cv.tex'})
    return out


def parse_skills(lines: list[str]):
    text=' '.join(lines).strip()
    if not text: return []
    text=re.sub(r'^Efficient programming skills in\s+','',text,flags=re.I).strip(' .')
    skills=[x.strip() for x in re.split(r',|\band\b',text) if x.strip()]
    return [{'id':'cv-skill-programming','type':'cv','kind':'skill','title_en':'Programming / scientific computing',
             'skills':skills,'source':'cv.tex','_latex_text':' '.join(lines).strip()}]


def parse_education(lines: list[str]):
    records=parse_generic_section(lines,'education')
    for r in records:
        text=r.get('_latex_text','')
        tm=re.search(r'Thesis Title:\s*[“"``]*(.*?)(?=\s+Thesis Advisor:|\s+DOI:|\s+HDL:|$)',text,re.I)
        if tm: r['thesis_title_en']=tm.group(1).strip(' ,.;”"\'')
        am=re.search(r'Thesis Advisor:\s*(?:Prof\.\s*)?(.+?)(?:\s*\([^)]*\))?(?=\s+DOI:|\s+HDL:|$)',text,re.I)
        if am: r['advisor']=am.group(1).strip(' ,.;')
        dm=re.search(r'DOI:\s*([^\s,;]+)',text,re.I)
        if dm: r['doi']=dm.group(1).strip(' .')
        hm=re.search(r'HDL:\s*([^\s,;]+)',text,re.I)
        if hm: r['hdl']=hm.group(1).strip(' .')
        if r['title_en'].startswith('Ph.D.'): r['degree']='Ph.D.'
        elif r['title_en'].startswith('M.S.'): r['degree']='M.S.'
        elif r['title_en'].startswith('B.S.'): r['degree']='B.S.'
    return records


def parse_profile(lines: list[str]):
    text='\n'.join(lines)
    p={}
    mm=re.search(r'E-?mail\s+([^\s]+@[^\s]+)',text,re.I)
    if mm:p['email']=mm.group(1)
    mm=re.search(r'Website\s+(https?://\S+)',text,re.I)
    if mm:p['website']=mm.group(1).rstrip('.,')
    mm=re.search(r'ORCID\s+([0-9Xx-]{15,25})',text,re.I)
    if mm:p['orcid']=mm.group(1)
    mm=re.search(r'GitHub\s+(https?://\S+)',text,re.I)
    if mm:p['github']=mm.group(1).rstrip('.,')
    return p


def parse(tex_path: Path):
    raw=tex_path.read_text(encoding='utf-8')
    plain=tex_to_plain(raw)
    lines=plain.splitlines()
    records=[]
    for heading,kind in SECTION_KIND.items():
        if heading=='Academic Degrees':
            records.extend(parse_education(block_between(lines,heading)))
        else:
            records.extend(parse_generic_section(block_between(lines,heading),kind))
    records.extend(parse_teaching(block_between(lines,'Lectures'),'lecturer'))
    records.extend(parse_teaching(block_between(lines,'Teaching Assistant'),'teaching_assistant'))
    records.extend(parse_mentorship(block_between(lines,'Student Mentorship')))
    records.extend(parse_languages(block_between(lines,'Languages')))
    records.extend(parse_skills(block_between(lines,'Computer Skills')))
    # Deduplicate parser output by kind/date/title; this also neutralizes headings that
    # may be encountered twice in nested TeX structures.
    unique=[]; seen=set()
    for r in records:
        key=(r.get('kind'),r.get('start_date'),norm(r.get('title_en')),norm(r.get('organization_en') or r.get('event_en')))
        if key in seen: continue
        seen.add(key); unique.append(r)
    return unique, parse_profile(block_between(lines,'Personal Data')), plain


def record_text(r):
    return ' '.join(str(x) for x in [r.get('title_en'),r.get('organization_en'),r.get('event_en'),r.get('description_en')] if x)


def find_match(records, inc, used=None):
    used = used or set()
    iid = inc.get('id')
    for r in records:
        if id(r) in used:
            continue
        if r.get('id') == iid or iid in (r.get('legacy_ids') or []):
            return r
    # Same kind/date is the primary local key.  Organization/event identity is
    # deliberately weighted strongly because several CV categories contain
    # generic titles such as "Referee" in the same year.
    inc_text = norm(inc.get('_latex_text') or record_text(inc))
    inc_title = norm(inc.get('title_en'))
    inc_org = norm(inc.get('organization_en'))
    inc_event = norm(inc.get('event_en'))
    cands = [r for r in records if r.get('kind') == inc.get('kind') and id(r) not in used]
    same_date = [r for r in cands if r.get('start_date') == inc.get('start_date')]
    scored = []
    for r in (same_date or cands):
        rt = norm(record_text(r))
        rtitle = norm(r.get('title_en'))
        rorg = norm(r.get('organization_en'))
        revent = norm(r.get('event_en'))
        score = similarity(rt, inc_text)
        if rtitle and inc_title:
            score = max(score, .78 * similarity(rtitle, inc_title))
            if rtitle == inc_title:
                score += .18
        if r.get('start_date') == inc.get('start_date'):
            score += .18
        if inc_org and rorg:
            os = similarity(rorg, inc_org)
            same_org = rorg == inc_org or rorg in inc_org or inc_org in rorg
            # For generic same-year titles such as Referee/Reviewer, a clearly
            # different organization means a genuinely different CV record.
            # Do not let title/date similarity collapse a newly added service
            # into an existing one.
            if not same_org and os < .45:
                continue
            score += .38 * os
            if same_org:
                score += .22
            elif os < .60:
                score -= .12
        elif r.get('organization_en') and norm(r.get('organization_en')) in inc_text:
            score += .18
        if inc_event and revent:
            es = similarity(revent, inc_event)
            same_event = revent == inc_event or revent in inc_event or inc_event in revent
            score += .35 * es
            if same_event:
                score += .22
        if rt and inc_text and (rt in inc_text or (rtitle and rtitle in inc_text)):
            score = max(score, .96)
        scored.append((score, r))
    if scored:
        sc, r = max(scored, key=lambda x: x[0])
        if sc >= .80:
            return r
    return None


def merge_tex_record(target, inc):
    # Preserve all metadata the TeX importer does not own.  TeX is authoritative for
    # the current English/basic CV wording, but never destroys Japanese, URLs, external
    # identifiers, manual notes, or ResearchMap provenance.
    protected_date=bool(target.get('date_note'))
    if protected_date and (target.get('start_date')!=inc.get('start_date') or target.get('end_date')!=inc.get('end_date')):
        target['latex_start_date']=inc.get('start_date')
        target['latex_end_date']=inc.get('end_date')
    managed={'title_en','organization_en','event_en','description_en','role','level_en','skills','degree','thesis_title_en','advisor','doi','doi_url','hdl','grant_number','grant_numbers'}
    for k in managed:
        v=inc.get(k)
        if v is None or v=='':
            continue
        if k == 'event_en' and target.get('organization_en'):
            # Organizer rows often render as "role, event, organization".  Keep the
            # existing event/organization split when the organization is a literal suffix.
            org = str(target['organization_en']).strip()
            vv = str(v).strip()
            if norm(org) and norm(vv).endswith(norm(org)):
                cut = vv.lower().rfind(org.lower())
                if cut >= 0:
                    vv = vv[:cut].rstrip(' ,;')
                    v = vv
        target[k]=v
    if not protected_date:
        if inc.get('start_date'): target['start_date']=inc['start_date']
        if 'end_date' in inc: target['end_date']=inc.get('end_date')
    target['source']='cv.tex'
    # The exact source text already lives in sources/cv.tex; do not duplicate raw
    # LaTeX-derived prose into every YAML record or the all-field search index.
    target.pop('latex_text', None)
    return target


def update_profile(profile_path: Path, p: dict):
    if not p or not profile_path.exists(): return 0
    data=load_yaml(profile_path)
    if not data:return 0
    r=data[0]; changed=0
    for k,v in p.items():
        if not v: continue
        if r.get(k)!=v:
            r[k]=v;changed+=1
    r.setdefault('urls',{})
    for k in ['website','github']:
        if p.get(k):r['urls'][k]=p[k]
    if p.get('orcid'):
        r.setdefault('identifiers',{})['orcid']=p['orcid']
        r['urls']['orcid']='https://orcid.org/'+p['orcid']
    if changed:
        save_yaml(profile_path,data)
    return changed


def sync(tex_path: Path, yaml_path: Path, profile_path: Path):
    incoming, profile, _plain=parse(tex_path)
    records=load_yaml(yaml_path)
    added=updated=0
    used=set()
    for inc in incoming:
        target=find_match(records,inc,used=used)
        if target is None:
            inc=dict(inc); inc.pop('_latex_text',None)
            # Keep a concise source-native local id.  Existing records are never renamed
            # solely because their LaTeX rendering changed.
            records.append(inc);added+=1
        else:
            merge_tex_record(target,inc);updated+=1
        used.add(id(target if target is not None else records[-1]))
    records.sort(key=lambda r:(str(r.get('start_date') or ''),str(r.get('id') or '')),reverse=True)
    save_yaml(yaml_path,records)
    pchanges=update_profile(profile_path,profile)
    return len(incoming),added,updated,len(records),pchanges


def main():
    ap=argparse.ArgumentParser(description='Non-destructively upsert the author-maintained CV LaTeX into cv.yaml/profile.yaml.')
    ap.add_argument('tex',nargs='?',type=Path,default=DEFAULT_TEX)
    ap.add_argument('-o','--output',type=Path,default=DEFAULT_YAML)
    ap.add_argument('--profile',type=Path,default=DEFAULT_PROFILE)
    args=ap.parse_args()
    if not args.tex.exists():
        print(f'CV TeX not found; skipping: {args.tex}')
        return
    parsed,added,updated,total,pchanges=sync(args.tex,args.output,args.profile)
    print(f'Parsed {parsed} CV TeX records; +{added}, updated {updated}, total {total}; profile fields updated {pchanges}')


if __name__=='__main__':
    main()
