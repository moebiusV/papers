#!/usr/bin/env bash
# build.sh — render (buildabook) and compile the book
# Usage: ./build.sh [--watch]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v buildabook &>/dev/null; then
    echo "error: buildabook not found in PATH." >&2
    exit 1
fi

if [[ "${1:-}" == "--watch" ]]; then
    buildabook typst
    echo "Watching for changes. Press Ctrl-C to stop."
    exec typst watch rendered/book.typ viking-poets.pdf
else
    buildabook pdf
    echo "Built: $SCRIPT_DIR/viking-poets.pdf"
fi
