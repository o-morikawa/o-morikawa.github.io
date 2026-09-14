#!/usr/bin/env python3
from __future__ import annotations

import json
from html import escape
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required. Install it with: python -m pip install PyYAML"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "publications.yaml"
GENERATED = ROOT / "generated"
SITE = ROOT / "site" / "publications"


def load_publications() -> list[dict]:
    with DATA.open("r", encoding="utf-8") as f:
        records = yaml.safe_load(f) or []
    if not isinstance(records, list):
        raise ValueError("publications.yaml must contain a top-level YAML list")
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"record {i} is not a mapping")
        for required in ("id", "authors", "title", "year", "type", "status"):
            if required not in record:
                raise ValueError(f"record {i} is missing required field: {required}")
    return records


def build_search_index(records: list[dict]) -> list[dict]:
    index = []
    for p in records:
        haystack = " ".join(
            [
                str(p.get("title", "")),
                " ".join(p.get("authors", []) or []),
                " ".join(p.get("topics", []) or []),
                str(p.get("year", "")),
                str(p.get("type", "")),
                str(p.get("status", "")),
                str(p.get("affiliation_period", "")),
            ]
        ).lower()
        index.append({"id": p["id"], "text": haystack})
    return index


def render_html(records: list[dict]) -> str:
    payload = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Publications</title>
  <style>
    :root {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; color-scheme: light dark; }}
    body {{ max-width: 900px; margin: 40px auto; padding: 0 20px 60px; line-height: 1.55; }}
    h1 {{ margin-bottom: .2rem; }}
    .sub {{ opacity: .7; margin-top: 0; }}
    input {{ width: 100%; box-sizing: border-box; font: inherit; padding: .8rem 1rem; margin: 1rem 0 1.5rem; border: 1px solid #8888; border-radius: 8px; }}
    article {{ border-top: 1px solid #8885; padding: 1.2rem 0; }}
    .meta {{ opacity: .72; font-size: .94rem; }}
    .title {{ font-weight: 700; font-size: 1.06rem; }}
    .tags {{ display: flex; gap: .45rem; flex-wrap: wrap; margin-top: .55rem; }}
    .tag {{ border: 1px solid #8886; border-radius: 999px; padding: .12rem .55rem; font-size: .82rem; }}
    a {{ color: inherit; }}
    #count {{ opacity: .65; font-size: .9rem; }}
  </style>
</head>
<body>
  <h1>Publications</h1>
  <p class=\"sub\">Generated from <code>data/publications.yaml</code>.</p>
  <input id=\"q\" type=\"search\" placeholder=\"Search title, author, topic, year, status…\" autofocus>
  <div id=\"count\"></div>
  <main id=\"list\"></main>

  <script id=\"publication-data\" type=\"application/json\">{payload}</script>
  <script>
    const data = JSON.parse(document.getElementById('publication-data').textContent);
    const list = document.getElementById('list');
    const count = document.getElementById('count');
    const q = document.getElementById('q');

    const esc = s => String(s ?? '').replace(/[&<>\"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}}[c]));
    const link = (label, url) => url ? `<a href=\"${{esc(url)}}\">${{label}}</a>` : '';

    function render(rows) {{
      count.textContent = `${{rows.length}} publication${{rows.length === 1 ? '' : 's'}}`;
      list.innerHTML = rows.map(p => {{
        const authors = (p.authors || []).map(esc).join(', ');
        const links = [
          p.arxiv && link('arXiv', p.arxiv),
          p.doi && link('DOI', p.doi),
          p.inspire && link('INSPIRE', p.inspire)
        ].filter(Boolean).join(' · ');
        const tags = (p.topics || []).map(t => `<span class=\"tag\">${{esc(t)}}</span>`).join('');
        return `<article id=\"${{esc(p.id)}}\">
          <div class=\"meta\">${{esc(p.year)}} · ${{esc(p.type)}} · ${{esc(p.status)}} · ${{esc(p.affiliation_period || '')}}</div>
          <div>${{authors}}</div>
          <div class=\"title\">${{esc(p.title)}}</div>
          ${{links ? `<div>${{links}}</div>` : ''}}
          ${{tags ? `<div class=\"tags\">${{tags}}</div>` : ''}}
        </article>`;
      }}).join('');
    }}

    function searchableText(p) {{
      return [p.title, ...(p.authors || []), ...(p.topics || []), p.year, p.type, p.status, p.affiliation_period]
        .filter(Boolean).join(' ').toLowerCase();
    }}

    q.addEventListener('input', () => {{
      const needle = q.value.trim().toLowerCase();
      render(!needle ? data : data.filter(p => searchableText(p).includes(needle)));
    }});

    render(data);
  </script>
</body>
</html>
"""


def main() -> None:
    records = load_publications()
    records.sort(key=lambda p: (p.get("year", 0), p.get("id", "")), reverse=True)

    GENERATED.mkdir(parents=True, exist_ok=True)
    SITE.mkdir(parents=True, exist_ok=True)

    with (GENERATED / "publications.json").open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with (GENERATED / "search-index.json").open("w", encoding="utf-8") as f:
        json.dump(build_search_index(records), f, ensure_ascii=False, indent=2)
        f.write("\n")

    (SITE / "index.html").write_text(render_html(records), encoding="utf-8")

    print(f"Built {len(records)} publication(s)")
    print(f"- {GENERATED / 'publications.json'}")
    print(f"- {GENERATED / 'search-index.json'}")
    print(f"- {SITE / 'index.html'}")


if __name__ == "__main__":
    main()
