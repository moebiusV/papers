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
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 ]//g' | sed 's/  */-/g'
}

h1_title() {
    grep -m1 '^# ' "$1" 2>/dev/null | sed 's/^# //' || echo "$(basename $(dirname "$1"))"
}

# First italic line in DESCRIPTION.md, minus the asterisks and date suffix
tagline() {
    grep -m1 '^\*.*\*$' "$1" 2>/dev/null | sed 's/^\*//;s/\*$//' | sed 's/ — ....*//'
}

desc_count() {
    find "$ROOT/papers/$1" -name '*.desc' 2>/dev/null | wc -l
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
            tl=$(tagline "$desc")
            count=$(desc_count "$dir")
            [[ -n "$tl" ]] && tl=" — *$tl*"
            echo "- [$title](#$anchor)$tl ($count documents)"
        fi
    done
    echo ""

    # ── Paper descriptions ───────────────────────────────────────────
    for dir in $SUBDIRS; do
        desc="$ROOT/papers/$dir/DESCRIPTION.md"
        if [[ -f "$desc" ]]; then
            count=$(desc_count "$dir")
            echo "---"
            echo ""
            cat "$desc"
            echo ""
            echo "<small>$count documents</small>"
            echo ""
        fi
    done
} > "$README"

echo "  README (root)"
