#!/usr/bin/env bash
# build.sh — compile book.typ → book.pdf
# Usage: ./build.sh [--watch]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v typst &>/dev/null; then
    echo "error: typst not found." >&2
    echo "Install with: cargo install typst-cli" >&2
    echo "         or: https://github.com/typst/typst/releases" >&2
    exit 1
fi

if [[ "${1:-}" == "--watch" ]]; then
    echo "Watching for changes. Press Ctrl-C to stop."
    exec typst watch book.typ book.pdf
else
    typst compile book.typ book.pdf
    echo "Built: $SCRIPT_DIR/book.pdf"
fi
