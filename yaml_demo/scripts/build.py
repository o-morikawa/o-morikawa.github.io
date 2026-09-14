#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required. Install it with: python -m pip install PyYAML"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"


def load_records() -> list[dict]:
    """Load every data/*.yaml file into one flat searchable record list."""
    records: list[dict] = []
    seen_ids: set[str] = set()

    for path in sorted(DATA_DIR.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            items = yaml.safe_load(f) or []

        if not isinstance(items, list):
            raise ValueError(f"{path.name}: top level must be a YAML list")

        for i, record in enumerate(items):
            if not isinstance(record, dict):
                raise ValueError(f"{path.name}: record {i} is not a mapping")

            for required in ("id", "type", "title"):
                if not record.get(required):
                    raise ValueError(
                        f"{path.name}: record {i} is missing required field: {required}"
                    )

            record_id = str(record["id"])
            if record_id in seen_ids:
                raise ValueError(f"duplicate id: {record_id}")
            seen_ids.add(record_id)

            # Keep source filename as provenance/debug metadata. It is searchable too.
            normalized = dict(record)
            normalized["_source"] = path.name
            records.append(normalized)

    return records


def sort_records(records: list[dict]) -> list[dict]:
    def key(record: dict):
        # date works for future presentation records; year works for publications.
        dateish = str(record.get("date") or record.get("year") or "")
        return (dateish, str(record.get("id", "")))

    return sorted(records, key=key, reverse=True)


def render_html(records: list[dict]) -> str:
    payload = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>O. Morikawa — Research database</title>
  <style>
    :root {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color-scheme: light dark;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      max-width: 960px;
      margin: 42px auto;
      padding: 0 22px 64px;
      line-height: 1.5;
    }}
    h1 {{ margin: 0 0 .25rem; font-size: clamp(1.65rem, 4vw, 2.35rem); }}
    .sub {{ opacity: .68; margin: 0 0 1.5rem; }}
    .controls {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 190px;
      gap: .7rem;
      margin: 0 0 .75rem;
    }}
    input, select {{
      width: 100%;
      font: inherit;
      padding: .78rem .9rem;
      border: 1px solid #8888;
      border-radius: 8px;
      background: transparent;
      color: inherit;
    }}
    #count {{ opacity: .62; font-size: .9rem; margin: .2rem 0 1rem; }}
    article {{ border-top: 1px solid #8885; padding: 1.05rem 0 1.15rem; }}
    .row {{ display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }}
    .type {{
      display: inline-block;
      font-size: .77rem;
      border: 1px solid #8886;
      border-radius: 999px;
      padding: .08rem .48rem;
      text-transform: lowercase;
      white-space: nowrap;
    }}
    .meta {{ opacity: .68; font-size: .9rem; }}
    .title {{ font-weight: 700; font-size: 1.05rem; margin: .15rem 0; }}
    .authors {{ margin-top: .15rem; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: .38rem; margin-top: .5rem; }}
    .tag {{ opacity: .82; font-size: .8rem; border: 1px solid #8885; border-radius: 999px; padding: .08rem .48rem; }}
    .links {{ margin-top: .32rem; font-size: .92rem; }}
    a {{ color: inherit; }}
    .empty {{ padding: 2rem 0; opacity: .65; }}
    @media (max-width: 640px) {{
      .controls {{ grid-template-columns: 1fr; }}
      .row {{ align-items: flex-start; }}
    }}
  </style>
</head>
<body>
  <h1>Research database</h1>
  <p class="sub">One-file view generated from YAML. Search across all record types.</p>

  <div class="controls">
    <input id="q" type="search" placeholder="Search title, author, topic, venue, year…" autofocus>
    <select id="type" aria-label="Record type">
      <option value="">All types</option>
    </select>
  </div>
  <div id="count"></div>
  <main id="list"></main>

  <!-- All data needed by the page are embedded here. No fetch(), JSON file, CSS, or JS asset is required. -->
  <script id="database" type="application/json">{payload}</script>
  <script>
    const data = JSON.parse(document.getElementById('database').textContent);
    const q = document.getElementById('q');
    const typeSelect = document.getElementById('type');
    const count = document.getElementById('count');
    const list = document.getElementById('list');

    const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({{
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }}[c]));

    const prettyType = value => String(value || '')
      .replace(/[-_]+/g, ' ')
      .replace(/\\b\\w/g, c => c.toUpperCase());

    const url = value => {{
      if (!value) return '';
      const s = String(value);
      if (/^https?:\\/\\//i.test(s)) return s;
      return '';
    }};

    function flatten(value, out = []) {{
      if (value == null) return out;
      if (Array.isArray(value)) {{
        value.forEach(v => flatten(v, out));
      }} else if (typeof value === 'object') {{
        Object.values(value).forEach(v => flatten(v, out));
      }} else {{
        out.push(String(value));
      }}
      return out;
    }}

    function searchableText(record) {{
      return flatten(record).join(' ').toLowerCase();
    }}

    function publicationHtml(r) {{
      const authors = (r.authors || []).map(esc).join(', ');
      const links = [
        url(r.arxiv) && `<a href="${{esc(url(r.arxiv))}}">arXiv</a>`,
        url(r.doi) && `<a href="${{esc(url(r.doi))}}">DOI</a>`,
        url(r.inspire) && `<a href="${{esc(url(r.inspire))}}">INSPIRE</a>`
      ].filter(Boolean).join(' · ');
      const tags = (r.topics || []).map(t => `<span class="tag">${{esc(t)}}</span>`).join('');
      const meta = [r.year, r.kind, r.status, r.affiliation_period].filter(Boolean).map(esc).join(' · ');

      return `
        <article id="${{esc(r.id)}}">
          <div class="row"><div class="meta">${{meta}}</div><span class="type">${{esc(r.type)}}</span></div>
          ${{authors ? `<div class="authors">${{authors}}</div>` : ''}}
          <div class="title">${{esc(r.title)}}</div>
          ${{links ? `<div class="links">${{links}}</div>` : ''}}
          ${{tags ? `<div class="tags">${{tags}}</div>` : ''}}
        </article>`;
    }}

    function presentationHtml(r) {{
      const speaker = r.speaker ? esc(r.speaker) : '';
      const meta = [r.date, r.venue, r.kind, r.language].filter(Boolean).map(esc).join(' · ');
      const tags = (r.topics || []).map(t => `<span class="tag">${{esc(t)}}</span>`).join('');
      return `
        <article id="${{esc(r.id)}}">
          <div class="row"><div class="meta">${{meta}}</div><span class="type">${{esc(r.type)}}</span></div>
          ${{speaker ? `<div class="authors">${{speaker}}</div>` : ''}}
          <div class="title">${{esc(r.title)}}</div>
          ${{tags ? `<div class="tags">${{tags}}</div>` : ''}}
        </article>`;
    }}

    function genericHtml(r) {{
      const meta = [r.date, r.year, r.kind, r.status].filter(Boolean).map(esc).join(' · ');
      return `
        <article id="${{esc(r.id)}}">
          <div class="row"><div class="meta">${{meta}}</div><span class="type">${{esc(r.type)}}</span></div>
          <div class="title">${{esc(r.title)}}</div>
        </article>`;
    }}

    function recordHtml(r) {{
      if (r.type === 'publications') return publicationHtml(r);
      if (r.type === 'presentations') return presentationHtml(r);
      return genericHtml(r);
    }}

    function populateTypes() {{
      const types = [...new Set(data.map(r => r.type).filter(Boolean))].sort();
      for (const type of types) {{
        const option = document.createElement('option');
        option.value = type;
        option.textContent = prettyType(type);
        typeSelect.appendChild(option);
      }}
    }}

    function applyUrlState() {{
      const params = new URLSearchParams(location.search);
      if (params.has('q')) q.value = params.get('q') || '';
      if (params.has('type')) typeSelect.value = params.get('type') || '';
    }}

    function updateUrlState() {{
      const params = new URLSearchParams();
      if (q.value.trim()) params.set('q', q.value.trim());
      if (typeSelect.value) params.set('type', typeSelect.value);
      const suffix = params.toString();
      history.replaceState(null, '', suffix ? `?${{suffix}}` : location.pathname);
    }}

    function render() {{
      const needle = q.value.trim().toLowerCase();
      const selectedType = typeSelect.value;

      const rows = data.filter(r =>
        (!selectedType || r.type === selectedType) &&
        (!needle || searchableText(r).includes(needle))
      );

      count.textContent = `${{rows.length}} / ${{data.length}} records`;
      list.innerHTML = rows.length
        ? rows.map(recordHtml).join('')
        : '<div class="empty">No matching records.</div>';

      updateUrlState();
    }}

    populateTypes();
    applyUrlState();
    q.addEventListener('input', render);
    typeSelect.addEventListener('change', render);
    render();
  </script>
</body>
</html>
'''


def main() -> None:
    records = sort_records(load_records())
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    output = SITE_DIR / "index.html"
    output.write_text(render_html(records), encoding="utf-8")

    print(f"Built {len(records)} record(s) from {len(list(DATA_DIR.glob('*.yaml')))} YAML file(s)")
    print(f"- {output}")
    print("Deploy only site/index.html if you want a single-file website.")


if __name__ == "__main__":
    main()
