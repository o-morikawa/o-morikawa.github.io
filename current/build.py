#!/usr/bin/env python3
"""Build current/index.html from current/current.md.

Usage:
    python3 build.py

The script deliberately keeps the toolchain small: it uses Python-Markdown if
available, otherwise Mistune. Install either package if neither is present.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "current.md"
OUTPUT = ROOT / "index.html"


def read_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Read a tiny YAML-like front matter block containing scalar key/value pairs."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("current.md starts front matter but has no closing ---")
    meta: dict[str, str] = {}
    for raw in text[4:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            raise ValueError(f"Invalid front-matter line: {raw!r}")
        key, value = raw.split(":", 1)
        meta[key.strip()] = value.strip().strip('"\'')
    return meta, text[end + 5 :]


def render_markdown(text: str) -> str:
    """Render Markdown with one of two small, common Python libraries."""
    try:
        import markdown  # type: ignore
    except ImportError:
        markdown = None

    if markdown is not None:
        return markdown.markdown(
            text,
            extensions=["extra", "sane_lists"],
            output_format="html5",
        )

    try:
        import mistune  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "A Markdown renderer is required. Install one with:\n"
            "    python3 -m pip install mistune\n"
            "or:\n"
            "    python3 -m pip install markdown"
        ) from exc

    renderer = mistune.create_markdown(escape=False)
    return renderer(text)


def main() -> int:
    raw = SOURCE.read_text(encoding="utf-8")
    meta, markdown_body = read_front_matter(raw)

    title = meta.get("title", "Current activities")
    site_name = meta.get("site_name", "Okuto Morikawa")
    lang = meta.get("lang", "en")

    body = render_markdown(markdown_body)

    document = f'''<!doctype html>
<html lang="{escape(lang, quote=True)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="current/build.py">
  <title>{escape(site_name)}: {escape(title)}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --page-bg: #ffffff;
      --text: #202124;
      --muted: #5f6368;
      --line: #dfe1e5;
      --link: #1a5fb4;
      --header-bg: #f7f8fa;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --page-bg: #151719;
        --text: #e8eaed;
        --muted: #aab0b6;
        --line: #3c4043;
        --link: #8ab4f8;
        --header-bg: #1d2023;
      }}
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--page-bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
                   "Noto Sans JP", Helvetica, Arial, sans-serif;
      font-size: 16px;
      line-height: 1.65;
    }}
    header {{
      background: var(--header-bg);
      border-bottom: 1px solid var(--line);
    }}
    .header-inner, main {{
      width: min(1080px, calc(100% - 2rem));
      margin: 0 auto;
    }}
    .header-inner {{ padding: 1.1rem 0 1rem; }}
    .site-name {{ font-size: 1.15rem; font-weight: 650; }}
    .page-title {{
      margin: .2rem 0 0;
      color: var(--muted);
      font-size: .95rem;
      font-weight: 500;
    }}
    main {{ padding: 1.8rem 0 4rem; }}
    h2 {{
      margin: 2.1rem 0 .8rem;
      padding-bottom: .25rem;
      border-bottom: 1px solid var(--line);
      font-size: 1.35rem;
      line-height: 1.3;
    }}
    h2:first-child {{ margin-top: 0; }}
    ul, ol {{ padding-left: 1.65rem; }}
    li {{ margin: .42rem 0; }}
    li p {{ margin: .25rem 0; }}
    a {{ color: var(--link); text-decoration-thickness: .06em; text-underline-offset: .12em; }}
    a:hover {{ text-decoration-thickness: .11em; }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: .92em;
    }}
    mjx-container {{ overflow-x: auto; overflow-y: hidden; }}
    footer {{
      width: min(1080px, calc(100% - 2rem));
      margin: 0 auto;
      padding: 1rem 0 2rem;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: .82rem;
    }}
    @media print {{
      header {{ background: none; }}
      a {{ color: inherit; }}
      footer {{ display: none; }}
    }}
  </style>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true
      }},
      options: {{ skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }}
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
  <!-- Generated from current.md by build.py. Do not edit this file directly. -->
  <header>
    <div class="header-inner">
      <div class="site-name">{escape(site_name)}</div>
      <div class="page-title">{escape(title)}</div>
    </div>
  </header>
  <main>
{body}
  </main>
  <footer>Generated from <code>current.md</code> by <code>build.py</code>.</footer>
</body>
</html>
'''

    OUTPUT.write_text(document, encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"build.py: {exc}", file=sys.stderr)
        raise SystemExit(1)
