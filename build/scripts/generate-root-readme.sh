#!/usr/bin/env bash
# generate-root-readme.sh — produce root README.md from each paper's DESCRIPTION.md
# DESCRIPTION.md uses MIME headers: Title:, Tagline:, Creation-Date:, Description:
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

# Parse MIME-format DESCRIPTION.md. Sets global variables:
#   DESC_TITLE, DESC_TAGLINE, DESC_CREATION, DESC_BODY
desc_parse() {
    local f="$1"
    DESC_TITLE=""; DESC_TAGLINE=""; DESC_CREATION=""; DESC_BODY=""
    local collect="" key value
    while IFS= read -r line; do
        if [[ -n "$collect" ]]; then
            DESC_BODY="${DESC_BODY}${line}
"
            continue
        fi
        if [[ "$line" =~ ^([A-Za-z-]+):[[:space:]]*(.*) ]]; then
            key="${BASH_REMATCH[1],,}"
            value="${BASH_REMATCH[2]}"
            case "$key" in
                title)          DESC_TITLE="$value" ;;
                tagline)        DESC_TAGLINE="$value" ;;
                creation-date)  DESC_CREATION="$value" ;;
                description)    collect=1; DESC_BODY="$value
" ;;
            esac
        elif [[ -z "$line" ]] && [[ -n "$DESC_TITLE" ]] && [[ -z "$collect" ]]; then
            collect=1
        fi
    done < "$f"
}

git_creation() {
    git -C "$ROOT" log --diff-filter=A --format="%ai" -- "papers/$1/" 2>/dev/null | tail -1 | cut -d' ' -f1
}

git_modified() {
    git -C "$ROOT" log --format="%ai" -1 -- "papers/$1/" 2>/dev/null | cut -d' ' -f1
}

month_year() {
    date -d "$1" "+%B %Y" 2>/dev/null || echo "$1"
}

desc_count() {
    find "$ROOT/papers/$1" -name '*.desc' 2>/dev/null | wc -l
}

{
    echo "Technical whitepapers and policy briefs in the public interest."
    echo ""

    # ── TOC ──────────────────────────────────────────────────────────
    for dir in $SUBDIRS; do
        desc="$ROOT/papers/$dir/DESCRIPTION.md"
        [[ -f "$desc" ]] || continue
        desc_parse "$desc"
        count=$(desc_count "$dir")
        tl="$DESC_TAGLINE"
        [[ -n "$tl" ]] && tl=" — *$tl*"
        echo "- [$DESC_TITLE](papers/$dir/)$tl ($count documents)"
    done
    echo ""

    # ── Paper descriptions ───────────────────────────────────────────
    for dir in $SUBDIRS; do
        desc="$ROOT/papers/$dir/DESCRIPTION.md"
        [[ -f "$desc" ]] || continue
        desc_parse "$desc"
        count=$(desc_count "$dir")

        creation="$DESC_CREATION"
        [[ -z "$creation" ]] && creation=$(git_creation "$dir")
        created_my=$(month_year "$creation")
        modified=$(git_modified "$dir")

        echo "---"
        echo ""
        echo "## [$DESC_TITLE](papers/$dir/)"
        echo ""
        echo "$DESC_TAGLINE ($count documents)"
        echo ""
        echo "<small>Created: $created_my · Updated: ${modified:-————}</small>"
        echo ""
        echo "$DESC_BODY"
    done
} > "$README"

echo "  README (root)"
