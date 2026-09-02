#!/usr/bin/env python3
r"""Normalize roman mathematical constants in TeX math regions.

Only high-confidence transformations are automatic.  Text outside TeX math
delimiters is copied byte for byte: this prevents an English word such as
``it`` or a TikZ style name from being mistaken for a product involving the
imaginary unit.  A bare ``i`` is not replaced globally because the exact-WKB
chapters also use it as a summation index.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


EXPLICIT_REPLACEMENTS = (
    (r"\mathrm{i}", r"\rmi"),
    (r"{\rm i}", r"\rmi"),
    (r"\mathrm{d}", r"\rmd"),
    (r"{\rm d}", r"\rmd"),
    (r"\mathrm{e}", r"\rme"),
    (r"{\rm e}", r"\rme"),
)

MEASURE = re.compile(
    r"(?<![A-Za-z\\^])d(?=(?:\^[{]?\d|"
    r"[xyzrktupqER](?:\b|[_'])))"
)

IMAGINARY_PRODUCT = re.compile(
    r"(?<![A-Za-z_\\^])i(?=(?:\s|\\[,!;:])*(?:"
    r"k(?=[xr]|\b|[_'])|(?:E|x|r)(?:\b|[_'])|\(|"
    r"\\(?:pi|theta|omega|epsilon|varepsilon|gamma|delta|alpha|beta|eta|"
    r"kappa|zeta|phi|chi|psi|mu|nu|lambda|Theta|Lambda|sin|sinh|cos|"
    r"cosh|sqrt|frac|ln|log|oint|int|lim|Tilde|hbar|infty)"
    r"(?:\b|_|(?=\d))"
    r"))"
)

MATH_ENVIRONMENTS = (
    "equation",
    "align",
    "alignat",
    "gather",
    "multline",
    "eqnarray",
    "displaymath",
    "math",
)

_ENVIRONMENT_PATTERN = "|".join(
    rf"{name}\*?" for name in MATH_ENVIRONMENTS
)
MATH_REGION = re.compile(
    rf"(?s)(?:"
    rf"\$\$(?:(?!\$\$)[\s\S])*\$\$|"
    rf"(?<!\\)\$(?:\\.|[^\\$])*(?<!\\)\$|"
    rf"\\\[(?:(?!\\\])(?:\\.|[^\\]))*\\\]|"
    rf"\\\((?:(?!\\\))(?:\\.|[^\\]))*\\\)|"
    rf"\\begin\{{(?P<env>{_ENVIRONMENT_PATTERN})\}}.*?"
    rf"\\end\{{(?P=env)\}}"
    rf")"
)

PROTECTED_ARGUMENT = re.compile(
    r"\\(?:label|ref|eqref|pageref|cite|index|tag|text|mbox)\{[^{}]*\}"
)


def is_escaped(text: str, position: int) -> bool:
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
    raise ValueError(f"unbalanced brace beginning at byte {opening}")


def delimiter_token_end(text: str, position: int) -> int | None:
    """Return the end of the delimiter token following ``\\left``/``\\right``."""
    while position < len(text) and text[position].isspace():
        position += 1
    if position >= len(text):
        return None
    if text[position] != "\\":
        return position + 1
    if position + 1 < len(text) and not text[position + 1].isalpha():
        return position + 2
    match = re.match(r"\\[A-Za-z]+", text[position:])
    return position + len(match.group(0)) if match else None


def matching_sized_delimiter(text: str, opening: int) -> tuple[int, int] | None:
    """Locate the outer ``\\right`` for a ``\\left`` beginning at *opening*."""
    opening_end = delimiter_token_end(text, opening + len(r"\left"))
    if opening_end is None:
        return None
    depth = 1
    cursor = opening_end
    while cursor < len(text):
        next_left = text.find(r"\left", cursor)
        next_right = text.find(r"\right", cursor)
        candidates = [value for value in (next_left, next_right) if value >= 0]
        if not candidates:
            return None
        command_start = min(candidates)
        if command_start == next_left:
            command_end = delimiter_token_end(text, command_start + len(r"\left"))
            if command_end is None:
                cursor = command_start + len(r"\left")
                continue
            depth += 1
        else:
            command_end = delimiter_token_end(text, command_start + len(r"\right"))
            if command_end is None:
                cursor = command_start + len(r"\right")
                continue
            depth -= 1
            if depth == 0:
                return command_start, command_end
        cursor = command_end
    return None


def matching_plain_delimiter(text: str, opening: int) -> int | None:
    """Match a plain TeX grouping delimiter after ``\\exp``."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = [pairs[text[opening]]]
    cursor = opening + 1
    while cursor < len(text):
        character = text[cursor]
        if is_escaped(text, cursor):
            cursor += 1
            continue
        if character in pairs:
            stack.append(pairs[character])
        elif stack and character == stack[-1]:
            stack.pop()
            if not stack:
                return cursor
        cursor += 1
    return None


def normalize_exponentials(text: str) -> str:
    r"""Convert delimited ``\exp`` calls to the book's ``\rme^{...}`` form."""
    output: list[str] = []
    cursor = 0
    while True:
        start = text.find(r"\exp", cursor)
        if start < 0:
            output.append(text[cursor:])
            break
        output.append(text[cursor:start])
        argument_start = start + len(r"\exp")
        while argument_start < len(text) and text[argument_start].isspace():
            argument_start += 1
        if text.startswith(r"\!", argument_start):
            argument_start += len(r"\!")
            while argument_start < len(text) and text[argument_start].isspace():
                argument_start += 1

        if text.startswith(r"\left", argument_start):
            opening_end = delimiter_token_end(
                text, argument_start + len(r"\left")
            )
            closing = matching_sized_delimiter(text, argument_start)
            if opening_end is not None and closing is not None:
                closing_start, closing_end = closing
                argument = text[opening_end:closing_start]
                output.append(r"\rme^{" + argument + "}")
                cursor = closing_end
                continue
        elif (
            argument_start < len(text)
            and text[argument_start] in "([{"
        ):
            closing = matching_plain_delimiter(text, argument_start)
            if closing is not None:
                argument = text[argument_start + 1:closing]
                output.append(r"\rme^{" + argument + "}")
                cursor = closing + 1
                continue

        output.append(text[start:argument_start])
        cursor = argument_start
    return "".join(output)


def leading_differential(group: str) -> tuple[str, bool]:
    if re.match(r"\s*\\rmd(?:\s|\^|$)", group):
        return group, True
    match = re.match(r"(\s*)d(?=(?:$|\^|[A-Za-z\\]))", group)
    if not match:
        return group, False
    start, end = match.span()
    remainder = group[end:]
    separator = " " if remainder and not remainder.startswith(" ") else ""
    return (
        group[:start] + match.group(1) + r"\rmd" + separator + remainder,
        True,
    )


def normalize_fractions(text: str) -> str:
    output: list[str] = []
    cursor = 0
    while True:
        start = text.find(r"\frac", cursor)
        if start < 0:
            output.append(text[cursor:])
            break
        output.append(text[cursor:start])
        after = start + len(r"\frac")
        while after < len(text) and text[after].isspace():
            after += 1
        if after >= len(text) or text[after] != "{":
            output.append(text[start:after])
            cursor = after
            continue
        numerator_end = matching_brace(text, after)
        denominator_start = numerator_end + 1
        while denominator_start < len(text) and text[denominator_start].isspace():
            denominator_start += 1
        if denominator_start >= len(text) or text[denominator_start] != "{":
            output.append(text[start : numerator_end + 1])
            cursor = numerator_end + 1
            continue
        denominator_end = matching_brace(text, denominator_start)
        numerator = normalize_fractions(text[after + 1 : numerator_end])
        denominator = normalize_fractions(
            text[denominator_start + 1 : denominator_end]
        )
        numerator_new, numerator_is_d = leading_differential(numerator)
        denominator_new, denominator_is_d = leading_differential(denominator)
        if numerator_is_d and denominator_is_d:
            numerator, denominator = numerator_new, denominator_new
        whitespace = text[numerator_end + 1 : denominator_start]
        output.append(r"\frac{" + numerator + "}" + whitespace + "{" + denominator + "}")
        cursor = denominator_end + 1
    return "".join(output)


def normalize_unprotected_math(text: str) -> str:
    for old, new in EXPLICIT_REPLACEMENTS:
        text = text.replace(old, new)
    # The spacing belongs to the differential symbol in the house style.
    # Thus an explicit thin space followed by \rmd is written once as \dd.
    text = text.replace(r"\,\rmd", r"\dd")
    text = normalize_fractions(text)
    text = MEASURE.sub(r"\\rmd ", text)
    text = IMAGINARY_PRODUCT.sub(r"\\rmi ", text)
    text = re.sub(r"(\\pi\s+)i(?=\s*n\b)", r"\1\\rmi", text)
    text = text.replace(r"\rmd ^", r"\rmd^")
    # A braced superscript on a bare e denotes the exponential throughout the
    # monograph; electric charge is written as e or e^2.
    text = re.sub(r"(?<![A-Za-z\\])e\^\{", r"\\rme^{", text)
    text = normalize_exponentials(text)
    return text


def normalize_math(text: str) -> str:
    """Normalize a math region while preserving structural command keys."""
    protected: list[str] = []

    def reserve(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"\x00QRPROTECTED{len(protected) - 1}\x00"

    text = PROTECTED_ARGUMENT.sub(reserve, text)
    text = normalize_unprotected_math(text)
    for index, original in enumerate(protected):
        text = text.replace(f"\x00QRPROTECTED{index}\x00", original)
    return text


def normalize(text: str) -> str:
    """Apply notation changes only inside recognized TeX math regions."""
    return MATH_REGION.sub(lambda match: normalize_math(match.group(0)), text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()

    changed: list[Path] = []
    for path in sorted(arguments.root.rglob("*.tex")):
        original = path.read_text(encoding="utf-8")
        revised = normalize(original)
        if revised != original:
            changed.append(path)
            if arguments.write:
                path.write_text(revised, encoding="utf-8")
            print(path)

    print(f"changed_files={len(changed)}")
    if changed and not arguments.write:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
