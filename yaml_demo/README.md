# YAML research database demo

This version treats YAML as the source of truth and generates **one self-contained `site/index.html`**.
The deployed site needs no JSON file, CSS file, JavaScript file, or server-side API.

## Current tree

```text
data/
  publications.yaml
scripts/
  build.py
site/
  index.html
requirements.txt
README.md
```

`build.py` automatically reads every `data/*.yaml` file, so future files can simply be added:

```text
data/
  publications.yaml
  presentations.yaml
  collaborators.yaml
  software.yaml
  books.yaml
  photos.yaml
```

Each record must have at least:

```yaml
- id: unique-id
  type: publications   # future: presentations, software, books, photos, ...
  title: Title
```

Publication-specific details can be added freely, for example:

```yaml
  kind: paper
  authors:
    - O. Morikawa
  year: 2026
  status: preprint
  topics:
    - quantum resonance
```

## Build

```bash
python -m pip install -r requirements.txt
python scripts/build.py
```

Then open `site/index.html` directly in a browser. No local web server is required.

The page provides:

- one search box across all fields of all record types;
- a dynamically generated **Type** filter (`publications`, later `presentations`, etc.);
- all CSS, JavaScript, and data embedded in `index.html`;
- query-string state such as `?q=resonance&type=publications`.

To publish on GitHub Pages, deploy `site/index.html` as the root `index.html` (or configure Pages/Actions to publish the `site/` directory).
