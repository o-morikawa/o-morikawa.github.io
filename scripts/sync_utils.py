#!/usr/bin/env python3
from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

import yaml


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
