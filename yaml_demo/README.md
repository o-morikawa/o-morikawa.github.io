# Publications YAML demo

Minimal prototype of a researcher-publications database.

## Structure

```text
data/
  publications.yaml
scripts/
  build.py
generated/
  publications.json
  search-index.json
site/
  publications/
    index.html
```

## Build

```bash
python -m pip install -r requirements.txt
python scripts/build.py
```

## Preview locally

From the project root:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/site/publications/
```

The HTML is deliberately minimal. `data/publications.yaml` is the source of truth; JSON and HTML are generated artifacts.
