#!/usr/bin/env bash
# generate-readme.sh — produce README.md from DESCRIPTION.md + Makefile file lists
# Called from a paper's Makefile `readme` target.
# Expects env vars: SOURCES, PDFS, DOCXS (paths relative to paper dir)
# Only files with a .desc sidecar appear in the README.
# Args: $1=paper-dir $2=slug $3=root
set -euo pipefail

PAPER_DIR="${1:-.}"
SLUG="${2:-$(basename "$PAPER_DIR")}"
ROOT="${3:-$(cd "$PAPER_DIR/../.." && pwd)}"

README="$PAPER_DIR/README.md"
DESCRIPTION="$PAPER_DIR/DESCRIPTION.md"

SOURCES="${SOURCES:-}"
PDFS="${PDFS:-}"
DOCXS="${DOCXS:-}"

cd "$ROOT"

# ── helpers ──────────────────────────────────────────────────────────

# Parse MIME-format DESCRIPTION.md. Sets global variables:
#   DESC_TITLE, DESC_TAGLINE, DESC_CREATION, DESC_BODY
desc_mime_parse() {
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

git_dates() {
    local f="$1"
    local created modified
    if git log --follow --diff-filter=A --format="%ai" -- "$f" 2>/dev/null | tail -1 | grep -q .; then
        created=$(git log --follow --diff-filter=A --format="%ai" -- "$f" 2>/dev/null | tail -1 | cut -d' ' -f1)
    else
        created="————"
    fi
    if git log --format="%ai" -1 -- "$f" 2>/dev/null | grep -q .; then
        modified=$(git log --format="%ai" -1 -- "$f" 2>/dev/null | cut -d' ' -f1)
    else
        modified="————"
    fi
    echo "$created|$modified"
}

relpath() {
    python3 -c "import os; print(os.path.relpath('$1', '$PAPER_DIR'))"
}

# Parse a .desc file (MIME-style headers).  Returns:
#   title|output-formats|tagline
# Fields not present are empty.
desc_parse() {
    local descfile="$1"
    local title="" formats="" tagline="" creation="" modified="" desc="" collect="" key="" value
    if [[ ! -f "$descfile" ]]; then
        echo "|||||"
        return
    fi
    while IFS= read -r line; do
        if [[ -z "$line" ]] && [[ -z "$collect" ]]; then
            collect="desc"
            continue
        fi
        if [[ -n "$collect" ]]; then
            desc="${desc}${line} "
            continue
        fi
        if [[ "$line" =~ ^([A-Za-z-]+):[[:space:]]*(.*) ]]; then
            key="${BASH_REMATCH[1],,}"
            value="${BASH_REMATCH[2]}"
            case "$key" in
                title)          title="$value" ;;
                output-formats) formats="$value" ;;
                tagline)        tagline="$value" ;;
                creation-date)  creation="$value" ;;
                last-modified)  modified="$value" ;;
                description)    collect="desc"; desc="$value " ;;
            esac
        fi
    done < "$descfile"
    desc="${desc% }"
    echo "${title}|${formats}|${tagline}|${creation}|${modified}|${desc}"
}

# ═══════════════════════════════════════════════════════════════════════
{
    # ── Description block ────────────────────────────────────────────
    if [[ -f "$DESCRIPTION" ]]; then
        desc_mime_parse "$DESCRIPTION"
        creation="$DESC_CREATION"
        [[ -z "$creation" ]] && creation=$(git_creation "$SLUG")
        created_my=$(month_year "$creation")
        modified=$(git_modified "$SLUG")

        count=$(find "$PAPER_DIR" -name '*.desc' 2>/dev/null | wc -l)

        echo "# $DESC_TITLE"
        echo ""
        echo "$DESC_TAGLINE ($count documents)"
        echo ""
        echo "<small>Created: $created_my · Updated: ${modified:-————}</small>"
        echo ""
        echo "$DESC_BODY"
        echo ""
        echo "---"
        echo ""
    fi

    # ── Download section ─────────────────────────────────────────────
    # Dates use project Creation-Date + git-modified, same as header above.
    if [[ -n "${PDFS:-}" ]] || [[ -n "${DOCXS:-}" ]]; then
        echo "## Download"
        echo ""
        echo "| Format | Link | Created | Updated |"
        echo "|---|---|---|---|"
        for f in $PDFS $DOCXS; do
            [[ -n "$f" ]] || continue
            ext="${f##*.}"
            name="${f##*/}"
            link=$(relpath "$PAPER_DIR/$f")
            echo "| ${ext^^} | [$name]($link) | ${creation:-————} | ${modified:-————} |"
        done
        echo ""
    fi

    # ── Contents ─────────────────────────────────────────────────────
    # Only files with a .desc sidecar appear here.
    has_content=""
    for f in $SOURCES; do
        [[ -n "$f" ]] || continue
        path="$PAPER_DIR/$f"
        [[ -f "$path.desc" ]] || continue   # skip files without .desc
        has_content="1"
    done

    if [[ -n "$has_content" ]]; then
        echo "## Contents"
        echo ""
        for f in $SOURCES; do
            [[ -n "$f" ]] || continue
            path="$PAPER_DIR/$f"
            [[ -f "$path.desc" ]] || continue
            name="${f##*/}"
            link=$(relpath "$path")
            parsed="$(desc_parse "$path.desc")"
            title=$(echo "$parsed" | cut -d'|' -f1)
            [[ -z "$title" ]] && title="$name"
            tagline=$(echo "$parsed" | cut -d'|' -f3)
            desc_creation=$(echo "$parsed" | cut -d'|' -f4)
            desc_modified=$(echo "$parsed" | cut -d'|' -f5)
            dates=($(git_dates "papers/$SLUG/$f" | tr '|' ' '))
            file_created="$desc_creation"
            file_modified="$desc_modified"
            # Fallback chain: .desc > git per-file > project date
            [[ -z "$file_created" ]] && file_created="${dates[0]}"
            [[ "$file_created" == "————" ]] && file_created="$creation"
            [[ -z "$file_modified" ]] && file_modified="${dates[1]}"
            [[ "$file_modified" == "————" ]] && file_modified="$modified"
            echo "**[$title]($link)** — $tagline"
            echo ""
            echo "<small>Created: ${file_created:-————} · Updated: ${file_modified:-————}</small>"
            echo ""
        done
    fi

} > "$README"

echo "  README $SLUG"
