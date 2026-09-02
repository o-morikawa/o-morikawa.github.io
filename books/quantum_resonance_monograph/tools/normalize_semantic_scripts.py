#!/usr/bin/env python3
r"""Normalize upright semantic scripts with ``\vsub``, ``\vsup``, and ``\vsupb``.

The transformation is deliberately conservative.  It recognizes only a
single TeX atom followed by an explicit ``\mathrm{...}`` script.  Numeric,
algebraic, tensor, derivative, and free-form scripts are left unchanged.
Run without ``--write`` to audit the files that would change.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ATOM = r"(?:\\(?:mathcal|mathsf|mathbf|mathit|bm)\{[^{}]+\}|\\(?:mathcal|mathsf|mathbf|mathit|bm)\s+[A-Za-z]|\\(?!(?:begin|end|left|right)\b)[A-Za-z]+(?:\{[^{}]+\})?|[A-Za-z0-9])"
LABEL = r"\\mathrm\{([^{}]+)\}"
# Do not begin a match inside a pre-existing algebraic script.  Composite
# bases such as ``E_n^{\mathrm{R}}`` need a judgement about whether ``n`` is
# algebraic or semantic and are intentionally left for manual normalization.
START = r"(?<![A-Za-z0-9_\\^])"

SUP_SUB = re.compile(
    START + rf"(?P<base>{ATOM})\^\{{{LABEL}\}}_\{{{LABEL}\}}"
)
SUB_SUP = re.compile(
    START + rf"(?P<base>{ATOM})_\{{{LABEL}\}}\^\{{{LABEL}\}}"
)
SUP = re.compile(START + rf"(?P<base>{ATOM})\^\{{{LABEL}\}}")
SUB = re.compile(START + rf"(?P<base>{ATOM})_\{{{LABEL}\}}")


def modernize_roman_scripts(text: str) -> str:
    r"""Convert legacy ``{\rm label}`` scripts before macro normalization."""
    text = re.sub(
        r"([_^])\{\\rm\s+([^{}]+)\}",
        lambda m: rf"{m.group(1)}{{\mathrm{{{m.group(2)}}}}}",
        text,
    )
    text = re.sub(
        r"([_^])\{\\rm\{([^{}]+)\}\}",
        lambda m: rf"{m.group(1)}{{\mathrm{{{m.group(2)}}}}}",
        text,
    )
    return text


def normalize(text: str) -> str:
    text = modernize_roman_scripts(text)
    text = SUP_SUB.sub(
        lambda m: rf"\vsupb{{{m.group('base')}}}{{{m.group(2)}}}{{{m.group(3)}}}",
        text,
    )
    text = SUB_SUP.sub(
        lambda m: rf"\vsupb{{{m.group('base')}}}{{{m.group(3)}}}{{{m.group(2)}}}",
        text,
    )
    text = SUP.sub(
        lambda m: rf"\vsup{{{m.group('base')}}}{{{m.group(2)}}}", text
    )
    text = SUB.sub(
        lambda m: rf"\vsub{{{m.group('base')}}}{{{m.group(2)}}}", text
    )
    return text


def source_files(root: Path) -> list[Path]:
    files = [root / "main.tex"]
    for directory in (
        root / "chapters",
        root / "source_compendium",
        root / "solutions_ja",
    ):
        files.extend(sorted(directory.rglob("*.tex")))
    return [path for path in files if path.exists()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()

    changed: list[Path] = []
    for path in source_files(arguments.root):
        original = path.read_text(encoding="utf-8")
        revised = normalize(original)
        if revised == original:
            continue
        changed.append(path)
        if arguments.write:
            path.write_text(revised, encoding="utf-8")
        print(path.relative_to(arguments.root))
    print(f"changed_files={len(changed)}")
    if changed and not arguments.write:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
