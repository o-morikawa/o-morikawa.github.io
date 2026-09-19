#!/usr/bin/env bash
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/.venv"
PYTHON="$VENV/bin/python"

if [ ! -x "$PYTHON" ]; then
    python3 -m venv "$VENV"
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install -r "$HERE/requirements.txt"
fi

"$PYTHON" "$HERE/build.py"
