#!/usr/bin/env bash
# generate-root-readme.sh — produce root README.md from each paper's DESCRIPTION.md
# Args: $1=root $2+ = subdirectory slugs (space-separated)
set -euo pipefail

ROOT="${1:-.}"
shift
SUBDIRS="$@"

README="$ROOT/README.md"

# ── helpers ──────────────────────────────────────────────────────────

slug_to_anchor() {
    # "Vom Wagner zum Walther: Siegfried Entfesselt" → "vom-wagner-zum-walther-siegfried-entfesselt"
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 ]//g' | sed 's/  */-/g'
}

h1_title() {
    grep -m1 '^# ' "$1" 2>/dev/null | sed 's/^# //' || echo "$(basename $(dirname "$1"))"
}

{
    # ── Header ───────────────────────────────────────────────────────
    echo "Technical whitepapers and policy briefs in the public interest."
    echo ""

    # ── TOC ──────────────────────────────────────────────────────────
    for dir in $SUBDIRS; do
        desc="$ROOT/papers/$dir/DESCRIPTION.md"
        if [[ -f "$desc" ]]; then
            title=$(h1_title "$desc")
            anchor=$(slug_to_anchor "$title")
            echo "- [$title](#$anchor)"
        fi
    done
    echo ""

    # ── Paper descriptions ───────────────────────────────────────────
    for dir in $SUBDIRS; do
        desc="$ROOT/papers/$dir/DESCRIPTION.md"
        if [[ -f "$desc" ]]; then
            echo "---"
            echo ""
            cat "$desc"
            echo ""
        fi
    done
} > "$README"

echo "  README (root)"
