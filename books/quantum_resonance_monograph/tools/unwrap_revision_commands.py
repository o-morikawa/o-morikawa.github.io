#!/usr/bin/env python3
r"""Remove obsolete revision/color wrappers while preserving their arguments.

The source papers contain nested and multiline uses such as
``\revone{...\magenta{...}...}``, for which a regular-expression replacement
is unsafe.  This script performs a small balanced-brace scan.  It deliberately
operates only on TeX source files and leaves the general-purpose definitions
in ``omphys.sty`` untouched.
"""

from __future__ import annotations

import argparse
from pathlib import Path


WRAPPERS = ("revone", "revtwo", "revthr", "revthree", "magenta")


def is_escaped(text: str, position: int) -> bool:
    """Return whether the character at *position* is backslash escaped."""
    backslashes = 0
    cursor = position - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    for cursor in range(opening, len(text)):
        character = text[cursor]
        if character == "{" and not is_escaped(text, cursor):
            depth += 1
        elif character == "}" and not is_escaped(text, cursor):
            depth -= 1
            if depth == 0:
                return cursor
    raise ValueError(f"unbalanced wrapper beginning at byte {opening}")


def unwrap_once(text: str) -> tuple[str, int]:
    replacements: list[tuple[int, int, str]] = []
    cursor = 0
    while cursor < len(text):
        match = None
        for command in WRAPPERS:
            marker = "\\" + command
            if text.startswith(marker, cursor):
                after = cursor + len(marker)
                while after < len(text) and text[after].isspace():
                    after += 1
                if after < len(text) and text[after] == "{":
                    match = (after, matching_brace(text, after))
                    break
        if match is None:
            cursor += 1
            continue
        opening, closing = match
        replacements.append((cursor, closing + 1, text[opening + 1 : closing]))
        cursor = closing + 1

    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]
    return text, len(replacements)


def unwrap_all(text: str) -> tuple[str, int]:
    total = 0
    while True:
        text, count = unwrap_once(text)
        total += count
        if count == 0:
            return text, total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()

    changed = 0
    removed = 0
    for path in sorted(arguments.root.rglob("*.tex")):
        original = path.read_text(encoding="utf-8")
        cleaned, count = unwrap_all(original)
        if count:
            changed += 1
            removed += count
            if not arguments.check:
                path.write_text(cleaned, encoding="utf-8")
            print(f"{path}: {count}")

    print(f"files={changed} wrappers={removed}")
    if arguments.check and removed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
