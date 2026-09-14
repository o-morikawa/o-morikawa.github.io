#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
DATA_DIR=ROOT/'data'; SITE_DIR=ROOT/'site'

def load_records():
    records=[]; seen=set()
    for path in sorted(DATA_DIR.glob('*.yaml')):
        items=yaml.safe_load(path.read_text(encoding='utf-8')) or []
        if not isinstance(items,list):
            raise ValueError(f'{path.name}: top level must be a list')
        for i,r in enumerate(items):
            if not isinstance(r,dict):
                raise ValueError(f'{path.name}: record {i} is not a mapping')
            if not r.get('id') or not r.get('type'):
                raise ValueError(f'{path.name}: record {i} missing id/type')
            if r['id'] in seen:
                raise ValueError(f'duplicate id: {r["id"]}')
            seen.add(r['id']); x=dict(r); x['_source']=path.name; records.append(x)
    return records

def sort_records(records):
    def k(r):
        d=str(r.get('start_date') or r.get('date') or r.get('arxiv_date') or r.get('year') or '')
        return (d,str(r.get('id','')))
    return sorted(records,key=k,reverse=True)

HTML='''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>O. Morikawa - Research database</title>
<style>
:root{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:light dark}
*{box-sizing:border-box}body{max-width:1120px;margin:34px auto;padding:0 20px 70px;line-height:1.48}
h1{margin:0 0 .2rem;font-size:clamp(1.6rem,4vw,2.35rem)}.sub{opacity:.67;margin:.1rem 0 1.3rem}
.controls{display:grid;grid-template-columns:minmax(0,1fr) 170px 180px 150px;gap:.6rem;position:sticky;top:0;padding:.65rem 0;background:Canvas;z-index:2}
input,select{width:100%;font:inherit;padding:.68rem .78rem;border:1px solid #8888;border-radius:8px;background:Canvas;color:CanvasText}
#count{opacity:.62;font-size:.9rem;margin:.2rem 0 .7rem}article{border-top:1px solid #8885;padding:.9rem 0 1rem}
.row{display:flex;justify-content:space-between;gap:1rem;align-items:baseline}.meta{opacity:.65;font-size:.87rem}
.badge{display:inline-block;font-size:.73rem;border:1px solid #8886;border-radius:999px;padding:.05rem .42rem;white-space:nowrap}
.title{font-weight:700;font-size:1.04rem;margin:.14rem 0}.jp{font-weight:500;opacity:.78;margin-top:.08rem}
.authors,.venue,.detail{font-size:.93rem;margin:.12rem 0}.venue,.detail{opacity:.8}.links{font-size:.89rem;margin-top:.28rem}a{color:inherit}
.tags{display:flex;flex-wrap:wrap;gap:.32rem;margin-top:.42rem}.tag{opacity:.76;font-size:.75rem;border:1px solid #8885;border-radius:999px;padding:.04rem .4rem}
.key{opacity:.42;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.72rem;margin-top:.38rem}.empty{padding:2rem 0;opacity:.65}
@media(max-width:760px){.controls{grid-template-columns:1fr 1fr}}@media(max-width:480px){.controls{grid-template-columns:1fr}}
</style>
</head>
<body>
<h1>Research database</h1>
<p class="sub">Searchable standalone view generated from public YAML records. Japanese and English fields are retained separately.</p>
<div class="controls">
<input id="q" type="search" placeholder="Search everything..." autofocus>
<select id="type"><option value="">All types</option></select>
<select id="kind"><option value="">All kinds</option></select>
<select id="lang"><option value="both">EN + JA</option><option value="en">English</option><option value="ja">Japanese</option></select>
</div>
<div id="count"></div><main id="list"></main>
<script id="database" type="application/json">__PAYLOAD__</script>
<script>
function $(x){return document.getElementById(x)}
const data=JSON.parse($('database').textContent),q=$('q'),type=$('type'),kind=$('kind'),lang=$('lang'),count=$('count'),list=$('list');
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty=v=>String(v||'').replace(/[-_]+/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
function flatten(v,o=[]){if(v==null)return o;if(Array.isArray(v))v.forEach(x=>flatten(x,o));else if(typeof v==='object')Object.values(v).forEach(x=>flatten(x,o));else o.push(String(v));return o}
function titleBlock(r){let en=r.title_en||r.title||'',ja=r.title_ja||'';if(lang.value==='en')return `<div class="title">${esc(en||ja)}</div>`;if(lang.value==='ja')return `<div class="title">${esc(ja||en)}</div>`;return `<div class="title">${esc(en||ja)}</div>${ja&&ja!==en?`<div class="jp">${esc(ja)}</div>`:''}`}
function bilingual(en,ja){if(lang.value==='en')return en||ja||'';if(lang.value==='ja')return ja||en||'';return [en,ja&&ja!==en?ja:null].filter(Boolean).join(' / ')}
function links(r){let a=[];for(const [u,l] of [[r.slides_url,'Slides'],[r.researchmap_url,'ResearchMap'],[r.arxiv_url,r.arxiv?'arXiv:'+r.arxiv:'arXiv'],[r.doi_url,'DOI'],[r.inspire_url,'INSPIRE'],[r.url,'link']])if(u)a.push(`<a href="${esc(u)}" target="_blank" rel="noopener">${esc(l)}</a>`);if(r.urls)for(const [k,u] of Object.entries(r.urls))if(u)a.push(`<a href="${esc(u)}" target="_blank" rel="noopener">${esc(pretty(k))}</a>`);return a.join(' · ')}
function render(r){const date=r.start_date||r.arxiv_date||r.year||'';const meta=[date,r.affiliation_period,r.kind,r.status].filter(Boolean).map(esc).join(' · ');let body='';if(r.authors)body+=`<div class="authors">${r.authors.map(esc).join(', ')}</div>`;body+=titleBlock(r);if(r.type==='presentations'){let ev=bilingual(r.event_en,r.event_ja);if(ev)body+=`<div class="venue">${esc(ev)}</div>`;let detail=`Presenter: ${esc(r.presenter||'')}${r.invited?' · invited':''}`;if(r.slides_file)detail+=` · ${esc(r.slides_file)}`;if(r.date_conflict&&r.researchmap_date)detail+=` · ResearchMap date: ${esc(r.researchmap_date)}`;body+=`<div class="detail">${detail}</div>`}else if(r.type==='publications'){let v=[r.journal,r.volume,r.number,r.pages||r.article_number].filter(Boolean).join(' · ');if(v)body+=`<div class="venue">${esc(v)}</div>`}else if(r.type==='cv'){let o=bilingual(r.organization_en,r.organization_ja);if(o)body+=`<div class="venue">${esc(o)}</div>`;let e=bilingual(r.event_en,r.event_ja);if(e)body+=`<div class="detail">${esc(e)}</div>`}else if(r.type==='software'){let d=bilingual(r.description_en,r.description_ja);if(d)body+=`<div class="detail">${esc(d)}</div>`}const lk=links(r);if(lk)body+=`<div class="links">${lk}</div>`;if(r.topics?.length)body+=`<div class="tags">${r.topics.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>`;return `<article id="${esc(r.id)}"><div class="row"><div class="meta">${meta}</div><span class="badge">${esc(r.type)}</span></div>${body}<div class="key">${esc(r.id)}</div></article>`}
function addOptions(el,vals){[...new Set(vals.filter(Boolean))].sort().forEach(v=>{let o=document.createElement('option');o.value=v;o.textContent=pretty(v);el.appendChild(o)})}
addOptions(type,data.map(r=>r.type));addOptions(kind,data.map(r=>r.kind));
const p=new URLSearchParams(location.search);q.value=p.get('q')||'';type.value=p.get('type')||'';kind.value=p.get('kind')||'';lang.value=p.get('lang')||'both';
function update(){let n=q.value.trim().toLowerCase();let rows=data.filter(r=>(!type.value||r.type===type.value)&&(!kind.value||r.kind===kind.value)&&(!n||flatten(r).join(' ').toLowerCase().includes(n)));count.textContent=`${rows.length} / ${data.length} records`;list.innerHTML=rows.length?rows.map(render).join(''):'<div class="empty">No matching records.</div>';let x=new URLSearchParams();if(q.value)x.set('q',q.value);if(type.value)x.set('type',type.value);if(kind.value)x.set('kind',kind.value);if(lang.value!=='both')x.set('lang',lang.value);try{history.replaceState(null,'',location.pathname+(x.toString()?'?'+x:''))}catch(e){}}
[q,type,kind,lang].forEach(e=>e.addEventListener(e===q?'input':'change',update));update();
</script></body></html>'''

def main():
    records=sort_records(load_records())
    payload=json.dumps(records,ensure_ascii=False).replace('</','<\\/')
    SITE_DIR.mkdir(parents=True,exist_ok=True)
    out=SITE_DIR/'index.html'
    out.write_text(HTML.replace('__PAYLOAD__',payload),encoding='utf-8')
    print(f'Wrote {len(records)} records to {out}')
if __name__=='__main__':main()
