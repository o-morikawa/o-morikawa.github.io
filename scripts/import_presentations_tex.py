from __future__ import annotations
import re, sys, importlib.util
from pathlib import Path
from datetime import datetime

spec=importlib.util.spec_from_file_location('ib','/mnt/data/research_database_demo_v3/scripts/import_bib.py')
ib=importlib.util.module_from_spec(spec); spec.loader.exec_module(ib)
tex_to_text=ib.tex_to_text
infer_topics=ib.infer_topics

MONTHS={m:i for i,m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],1)}

def clean_tex(s):
    s=s.replace('\\OM','O. Morikawa')
    # href -> label
    s=re.sub(r'\\href\{[^{}]*\}\{([^{}]*)\}',r'\1',s)
    s=re.sub(r'\\url\{([^{}]*)\}',r'\1',s)
    # formatting macros retain body; repeat to handle simple nested-free
    for _ in range(4):
        s=re.sub(r'\\(?:textbf|textit|emph)\{([^{}]*)\}',r'\1',s)
    s=s.replace('\\&','&').replace('\\textasciicircum','^')
    s=s.replace('\\,',' ').replace('\\!','')
    s=s.replace('\\\\',' ')
    return tex_to_text(s)

def split_top_items(block):
    # main conference list has no nested enumerate; split on line-start item
    parts=re.split(r'(?m)^\s*\\item\s+', block)
    return [p.strip() for p in parts[1:] if p.strip()]

def extract_title(raw):
    m=re.search(r'``(.*?)\'\'', raw, re.S)
    if not m:
        return None,None
    return clean_tex(m.group(1)), m.span()

def parse_date(text):
    # returns start,end, span; match last Month day(--day)?, year
    pat=r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:--(\d{1,2}))?,\s*(\d{4})\b'
    ms=list(re.finditer(pat,text))
    if not ms: return None,None,None
    m=ms[-1]; mon=MONTHS[m.group(1)]; d1=int(m.group(2)); d2=int(m.group(3)) if m.group(3) else d1; y=int(m.group(4))
    return f'{y:04d}-{mon:02d}-{d1:02d}', f'{y:04d}-{mon:02d}-{d2:02d}', m.span()

def aff(date):
    if not date: return None
    ym=int(date[:7].replace('-',''))
    if ym<=202103: return 'Kyushu University'
    if ym<=202403: return 'Osaka University'
    return 'RIKEN (iTHEMS)'

def slug(s):
    s=s.lower().replace('ℤ','z').replace('𝒩','n').replace('θ','theta').replace('π','pi')
    s=re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s[:60].rstrip('-')

def parse_main(path):
    text=Path(path).read_text()
    sec=text.split('\\subsection{Conference activities, talks, and seminars}',1)[1].split('\\subsection{Other talks}',1)[0]
    block=sec.split('\\begin{enumerate}',1)[1].rsplit('\\end{enumerate}',1)[0]
    recs=[]
    for idx,raw in enumerate(split_top_items(block),1):
        title,tspan=extract_title(raw)
        if not title:
            print('NO TITLE',idx,raw[:100],file=sys.stderr); continue
        presenter='Okuto Morikawa'
        mp=re.search(r'\\textit\{talk by\s+([^{}]+)\}',raw,re.I)
        role='self'
        if mp:
            presenter=clean_tex(mp.group(1)); role='collaborator'
        invited=bool(re.search(r'\\textbf\{Invited (?:Speaker|Seminar)\}',raw))
        kind='poster' if '\\textbf{Poster}' in raw else ('seminar' if 'Invited Seminar' in raw else 'talk')
        start,end,dspan=parse_date(raw)
        rest=raw[tspan[1]:]
        rest=re.sub(r'\\textit\{talk by\s+[^{}]+\},?', '', rest, flags=re.I)
        rest=re.sub(r'\\textbf\{(Invited Speaker|Invited Seminar|Poster)\}\s*(?:at\s*)?,?', '', rest)
        rest=rest.strip(' ,\n')
        if dspan:
            # dspan applies raw; easier remove date pattern from rest
            rest=re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:--\d{1,2})?,\s*\d{4}\s*$', '', rest).strip(' ,\n')
        event=clean_tex(rest)
        rid=f"presentation-{start or 'undated'}-{slug(title)}"
        # collision later suffix
        topics=infer_topics(title,{})
        rec={
            'id':rid,'type':'presentations','kind':kind,'role':role,
            'presenter':presenter,'invited':invited,
            'title_en':title,'title_ja':None,'event_en':event,'event_ja':None,
            'start_date':start,'end_date':end if end!=start else None,
            'year':int(start[:4]) if start else None,'affiliation_period':aff(start),
            'topics':topics,'source':'presentation.tex'
        }
        recs.append(rec)
    # ensure ids unique
    seen={}
    for r in recs:
        base=r['id']; n=seen.get(base,0)+1; seen[base]=n
        if n>1:r['id']=f'{base}-{n}'
    return recs

if __name__=='__main__':
    import yaml
    rs=parse_main('/mnt/data/presentation.tex')
    print('count',len(rs),file=sys.stderr)
    print(yaml.safe_dump(rs,allow_unicode=True,sort_keys=False,width=1000))
