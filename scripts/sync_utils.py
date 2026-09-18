#!/usr/bin/env python3
from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

import yaml


def strip_latex_comments(text: str) -> str:
    """Remove unescaped LaTeX comments while preserving line structure."""
    out = []
    for line in text.splitlines():
        m = re.search(r'(?<!\\)%', line)
        if m:
            line = line[:m.start()]
        out.append(line)
    return '\n'.join(out)


def _balanced_group(text: str, start: int, open_char: str = '{', close_char: str = '}'):
    """Return (content, next_index) for a balanced group starting at *start*."""
    if start >= len(text) or text[start] != open_char:
        return None, start
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == open_char and (i == 0 or text[i - 1] != '\\'):
            depth += 1
        elif ch == close_char and (i == 0 or text[i - 1] != '\\'):
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    return None, start


def load_zero_arg_macros(path: Path | None):
    r"""Read zero-argument ``newcommand``-style macros from a shared preamble.

    Only commands without arguments are imported.  Structural commands such as
    ``\newcommand{\foo}[1]{...}`` are intentionally ignored; the database
    importers only need semantic aliases such as journal names, affiliations,
    and ``\OM``.  Nested braces in replacement text are supported.
    """
    if path is None or not Path(path).exists():
        return {}
    text = strip_latex_comments(Path(path).read_text(encoding='utf-8'))
    pat = re.compile(r'\\(?:newcommand|renewcommand|providecommand)\*?\s*')
    macros = {}
    pos = 0
    while True:
        m = pat.search(text, pos)
        if not m:
            break
        i = m.end()
        while i < len(text) and text[i].isspace():
            i += 1
        name = None
        if i < len(text) and text[i] == '{':
            group, j = _balanced_group(text, i)
            if group is not None:
                name = group.strip()
                i = j
        elif i < len(text) and text[i] == '\\':
            nm = re.match(r'\\[A-Za-z@]+', text[i:])
            if nm:
                name = nm.group(0)
                i += len(nm.group(0))
        if not name or not re.fullmatch(r'\\[A-Za-z@]+', name):
            pos = m.end()
            continue
        while i < len(text) and text[i].isspace():
            i += 1
        # Optional [n] means the command takes arguments.  Skip it entirely.
        if i < len(text) and text[i] == '[':
            j = text.find(']', i + 1)
            if j < 0:
                pos = i + 1
                continue
            argc = text[i + 1:j].strip()
            if argc and argc != '0':
                pos = j + 1
                continue
            i = j + 1
            while i < len(text) and text[i].isspace():
                i += 1
        if i >= len(text) or text[i] != '{':
            pos = i + 1
            continue
        replacement, j = _balanced_group(text, i)
        if replacement is None:
            pos = i + 1
            continue
        if '#' not in replacement:
            macros[name] = replacement
        pos = j
    return macros


def expand_zero_arg_macros(text: str, macros: dict[str, str] | None, passes: int = 8) -> str:
    """Expand semantic zero-argument macros, longest name first.

    Multiple passes allow aliases whose replacement contains another imported
    zero-argument macro.  Unknown/argument-taking commands remain untouched for
    the dedicated TeX parsers to handle.
    """
    if not macros:
        return text
    out = text
    items = sorted(macros.items(), key=lambda kv: len(kv[0]), reverse=True)
    for _ in range(max(1, passes)):
        before = out
        for macro, value in items:
            out = re.sub(re.escape(macro) + r'(?![A-Za-z@])', lambda _m, v=value: v, out)
        if out == before:
            break
    return out


def load_yaml(path: Path):
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding='utf-8')) or []
    if not isinstance(data, list):
        raise ValueError(f'{path}: top level must be a list')
    return data


def save_yaml(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(records, allow_unicode=True, sort_keys=False, width=1000),
        encoding='utf-8',
    )


def norm(value) -> str:
    s = str(value or '').lower()
    s = s.replace('–', '-').replace('—', '-').replace('−', '-')
    s = s.replace('ℤ', 'z').replace('𝒩', 'n').replace('θ', 'theta').replace('π', 'pi')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def similarity(a, b) -> float:
    aa, bb = norm(a), norm(b)
    if not aa or not bb:
        return 0.0
    if aa == bb:
        return 1.0
    return SequenceMatcher(None, aa, bb).ratio()


def author_signature(name: str) -> str:
    parts = norm(name).split()
    return parts[-1] if parts else ''


def same_author_list(a, b) -> bool:
    aa = [author_signature(x) for x in (a or [])]
    bb = [author_signature(x) for x in (b or [])]
    return bool(aa) and aa == bb


def slug(value: str, limit: int = 72) -> str:
    s = norm(value).replace(' ', '-')
    return s[:limit].rstrip('-') or 'untitled'


def merge_unique(existing: Iterable | None, incoming: Iterable | None):
    out = []
    for values in (existing or [], incoming or []):
        for value in values:
            if value is not None and value not in out:
                out.append(value)
    return out


def split_top_level_items(block: str, environment: str = 'enumerate'):
    r"""Return top-level \item bodies from a LaTeX list.

    Nested enumerate/itemize environments are retained inside the parent item.
    The caller should pass text beginning at or before the first outer list.
    """
    outer_begin = f'\\begin{{{environment}}}'
    lines = block.splitlines()
    depth = 0
    started = False
    current = []
    items = []
    for line in lines:
        begins = len(re.findall(r'\\begin\{(?:enumerate|itemize)\}', line))
        ends = len(re.findall(r'\\end\{(?:enumerate|itemize)\}', line))
        if not started:
            if outer_begin in line:
                started = True
                depth += begins - ends
            continue
        stripped = line.lstrip()
        if depth == 1 and stripped.startswith('\\item'):
            if current:
                items.append('\n'.join(current).strip())
            current = [stripped[len('\\item'):].strip()]
        else:
            if current:
                current.append(line)
        depth += begins - ends
        if depth <= 0:
            if current:
                body = '\n'.join(current)
                body = re.sub(r'\\end\{(?:enumerate|itemize)\}\s*$', '', body).strip()
                if body:
                    items.append(body)
            break
    return items


def section_text(text: str, heading: str, level: str = 'subsection') -> str:
    marker = f'\\{level}{{{heading}}}'
    start = text.find(marker)
    if start < 0:
        raise ValueError(f'Missing {marker}')
    body_start = start + len(marker)
    next_marker = f'\\{level}{{'
    end = text.find(next_marker, body_start)
    return text[body_start:] if end < 0 else text[body_start:end]
