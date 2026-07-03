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

# First italic line, minus asterisks and date suffix
tagline() {
    grep -m1 '^\*.*\*$' "$1" 2>/dev/null | sed 's/^\*//;s/\*$//' | sed 's/ — ....*//'
}

desc_count() {
    find "$ROOT/papers/$1" -name '*.desc' 2>/dev/null | wc -l
}

git_dates() {
    local f="$1"
    local created modified
    if git -C "$ROOT" log --diff-filter=A --format="%ai" -- "$f" 2>/dev/null | tail -1 | grep -q .; then
        created=$(git -C "$ROOT" log --diff-filter=A --format="%ai" -- "$f" 2>/dev/null | tail -1 | cut -d' ' -f1)
    else
        created="————"
    fi
    if git -C "$ROOT" log --format="%ai" -1 -- "$f" 2>/dev/null | grep -q .; then
        modified=$(git -C "$ROOT" log --format="%ai" -1 -- "$f" 2>/dev/null | cut -d' ' -f1)
    else
        modified="————"
    fi
    echo "$created $modified"
}

# "2026-04-08" -> "April 2026"
month_year() {
    date -d "$1" "+%B %Y" 2>/dev/null || echo "$1"
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
            title=$(h1_title "$desc")
            tl=$(tagline "$desc")
            count=$(desc_count "$dir")
            dates=($(git_dates "papers/$dir/"))
            created_my=$(month_year "${dates[0]}")

            echo "---"
            echo ""
            echo "## [$title](papers/$dir/)"
            echo ""
            echo "*$tl* — $created_my ($count documents)"
            echo ""
            echo "<small>Updated: ${dates[1]:-————}</small>"
            echo ""

            # Body text (skip H1, blank, tagline, blank)
            linenum=0
            while IFS= read -r line; do
                linenum=$((linenum + 1))
                [[ $linenum -le 4 ]] && continue
                echo "$line"
            done < "$desc"
            echo ""
        fi
    done
} > "$README"

echo "  README (root)"
