#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
SITE_DIR = ROOT / 'site'


def load_records() -> list[dict]:
    records: list[dict] = []
    seen_ids: set[str] = set()
    for path in sorted(DATA_DIR.glob('*.yaml')):
        items = yaml.safe_load(path.read_text(encoding='utf-8')) or []
        if not isinstance(items, list):
            raise ValueError(f'{path.name}: top level must be a YAML list')
        for i, record in enumerate(items):
            if not isinstance(record, dict):
                raise ValueError(f'{path.name}: record {i} is not a mapping')
            for required in ('id', 'type', 'title'):
                if not record.get(required):
                    raise ValueError(f'{path.name}: record {i} is missing {required}')
            rid = str(record['id'])
            if rid in seen_ids:
                raise ValueError(f'duplicate id: {rid}')
            seen_ids.add(rid)
            rec = dict(record)
            rec['_source'] = path.name
            records.append(rec)
    return records


def sort_records(records: list[dict]) -> list[dict]:
    def key(r: dict):
        dateish = str(r.get('date') or r.get('arxiv') or r.get('arxiv_date') or r.get('year') or '')
        return (dateish, str(r.get('id', '')))
    return sorted(records, key=key, reverse=True)


def render_html(records: list[dict]) -> str:
    payload = json.dumps(records, ensure_ascii=False).replace('</', '<\\/')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>O. Morikawa — Research database</title>
<style>
:root{{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:light dark}}
*{{box-sizing:border-box}}body{{max-width:1060px;margin:36px auto;padding:0 20px 64px;line-height:1.48}}
h1{{margin:0 0 .2rem;font-size:clamp(1.6rem,4vw,2.3rem)}}.sub{{opacity:.68;margin:.1rem 0 1.35rem}}
.controls{{display:grid;grid-template-columns:minmax(0,1fr) 190px 180px;gap:.65rem;margin-bottom:.55rem}}
input,select{{width:100%;font:inherit;padding:.7rem .82rem;border:1px solid #8888;border-radius:8px;background:transparent;color:inherit}}
#count{{opacity:.64;font-size:.9rem;margin:.25rem 0 1rem}}article{{border-top:1px solid #8885;padding:1rem 0 1.1rem}}
.row{{display:flex;justify-content:space-between;gap:1rem;align-items:baseline}}.meta{{opacity:.67;font-size:.88rem}}
.badge{{display:inline-block;font-size:.74rem;border:1px solid #8886;border-radius:999px;padding:.07rem .45rem;white-space:nowrap}}
.authors{{margin:.13rem 0}}.title{{font-weight:700;font-size:1.04rem;margin:.12rem 0}}
.venue{{opacity:.82;font-size:.93rem;margin:.18rem 0}}.links{{font-size:.9rem;margin-top:.28rem}}a{{color:inherit}}
.tags{{display:flex;flex-wrap:wrap;gap:.34rem;margin-top:.48rem}}.tag{{opacity:.78;font-size:.77rem;border:1px solid #8885;border-radius:999px;padding:.06rem .43rem}}
.key{{opacity:.46;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.74rem;margin-top:.42rem}}.empty{{padding:2rem 0;opacity:.65}}
@media(max-width:700px){{.controls{{grid-template-columns:1fr}}.row{{align-items:flex-start}}}}
</style>
</head>
<body>
<h1>Research database</h1>
<p class="sub">Self-contained view generated from public YAML data.</p>
<div class="controls">
  <input id="q" type="search" placeholder="Search title, author, topic, journal, year…" autofocus>
  <select id="type"><option value="">All types</option></select>
  <select id="kind"><option value="">All kinds</option></select>
</div>
<div id="count"></div><main id="list"></main>
<script id="database" type="application/json">{payload}</script>
<script>
const data=JSON.parse(document.getElementById('database').textContent);
const q=document.getElementById('q'),type=document.getElementById('type'),kind=document.getElementById('kind'),count=document.getElementById('count'),list=document.getElementById('list');
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
const pretty=v=>String(v||'').replace(/[-_]+/g,' ').replace(/\\b\\w/g,c=>c.toUpperCase());
function flatten(v,o=[]){{if(v==null)return o;if(Array.isArray(v))v.forEach(x=>flatten(x,o));else if(typeof v==='object')Object.values(v).forEach(x=>flatten(x,o));else o.push(String(v));return o}}
function journalLine(r){{if(r.kind==='thesis')return [r.school,r.year].filter(Boolean).join(' · ');if(!r.journal)return r.status==='preprint'?'Preprint':'';let s=r.journal;if(r.volume)s+=' '+r.volume;if(r.number)s+=' ('+r.number+')';if(r.pages)s+=', '+r.pages;if(r.year)s+=' ('+r.year+')';return s}}
function publicationHtml(r){{const authors=(r.authors||[]).map(esc).join(', ');const links=[[r.arxiv_url,r.arxiv?'arXiv:'+r.arxiv:'arXiv'],[r.doi_url,'DOI'],[r.inspire_url,'INSPIRE']].filter(x=>x[0]).map(x=>`<a href="${{esc(x[0])}}" target="_blank" rel="noopener">${{esc(x[1])}}</a>`).join(' · ');const tags=(r.topics||[]).map(t=>`<span class="tag">${{esc(t)}}</span>`).join('');const meta=[r.arxiv_date||r.year,r.affiliation_period,r.kind,r.status].filter(Boolean).map(esc).join(' · ');return `<article id="${{esc(r.id)}}"><div class="row"><div class="meta">${{meta}}</div><span class="badge">${{esc(r.type)}}</span></div>${{authors?`<div class="authors">${{authors}}</div>`:''}}<div class="title">${{esc(r.title)}}</div>${{journalLine(r)?`<div class="venue">${{esc(journalLine(r))}}</div>`:''}}${{links?`<div class="links">${{links}}</div>`:''}}${{tags?`<div class="tags">${{tags}}</div>`:''}}<div class="key">${{esc(r.id)}}</div></article>`}}
function genericHtml(r){{return `<article id="${{esc(r.id)}}"><div class="row"><div class="meta">${{esc(r.date||r.year||'')}}</div><span class="badge">${{esc(r.type)}}</span></div><div class="title">${{esc(r.title)}}</div><div class="key">${{esc(r.id)}}</div></article>`}}
function renderRecord(r){{return r.type==='publications'?publicationHtml(r):genericHtml(r)}}
function addOptions(el,vals){{[...new Set(vals.filter(Boolean))].sort().forEach(v=>{{const o=document.createElement('option');o.value=v;o.textContent=pretty(v);el.appendChild(o)}})}}
addOptions(type,data.map(r=>r.type));addOptions(kind,data.map(r=>r.kind));
const params=new URLSearchParams(location.search);q.value=params.get('q')||'';type.value=params.get('type')||'';kind.value=params.get('kind')||'';
function update(){{const needle=q.value.trim().toLowerCase();const rows=data.filter(r=>(!type.value||r.type===type.value)&&(!kind.value||r.kind===kind.value)&&(!needle||flatten(r).join(' ').toLowerCase().includes(needle)));count.textContent=`${{rows.length}} / ${{data.length}} records`;list.innerHTML=rows.length?rows.map(renderRecord).join(''):'<div class="empty">No matching records.</div>';const p=new URLSearchParams();if(q.value)p.set('q',q.value);if(type.value)p.set('type',type.value);if(kind.value)p.set('kind',kind.value);history.replaceState(null,'',location.pathname+(p.toString()?'?'+p:''));}}
q.addEventListener('input',update);type.addEventListener('change',update);kind.addEventListener('change',update);update();
</script>
</body></html>'''


def main():
    records = sort_records(load_records())
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    out = SITE_DIR / 'index.html'
    out.write_text(render_html(records), encoding='utf-8')
    print(f'Wrote {len(records)} records to {out}')


if __name__ == '__main__':
    main()
