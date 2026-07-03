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
    local title="" formats="" tagline="" desc="" collect="" key="" value
    if [[ ! -f "$descfile" ]]; then
        echo "||"
        return
    fi
    while IFS= read -r line; do
        # Blank line ends headers; everything after is Description
        if [[ -z "$line" ]] && [[ -z "$collect" ]]; then
            collect="desc"
            continue
        fi
        if [[ -n "$collect" ]]; then
            # Accumulating multi-line Description
            desc="${desc}${line} "
            continue
        fi
        # Header line: Key: Value
        if [[ "$line" =~ ^([A-Za-z-]+):[[:space:]]*(.*) ]]; then
            key="${BASH_REMATCH[1],,}"        # lowercase
            value="${BASH_REMATCH[2]}"
            case "$key" in
                title)          title="$value" ;;
                output-formats) formats="$value" ;;
                tagline)        tagline="$value" ;;
                description)    collect="desc"; desc="$value " ;;
            esac
        fi
    done < "$descfile"
    # Trim trailing space
    desc="${desc% }"
    echo "${title}|${formats}|${tagline}|${desc}"
}

# ═══════════════════════════════════════════════════════════════════════
{
    # ── Description block ────────────────────────────────────────────
    if [[ -f "$DESCRIPTION" ]]; then
        dates=($(git_dates "papers/$SLUG/" | tr '|' ' '))
        created_my=$(date -d "${dates[0]}" "+%B %Y" 2>/dev/null || echo "${dates[0]}")
        # Output H1 + tagline with date + body
        linenum=0
        while IFS= read -r line; do
            linenum=$((linenum + 1))
            if [[ $linenum -eq 1 ]]; then
                echo "$line"
                echo ""
            elif [[ $linenum -eq 2 ]]; then
                continue  # skip blank after H1
            elif [[ $linenum -eq 3 ]]; then
                echo "$line — $created_my"
                echo ""
            elif [[ $linenum -eq 4 ]]; then
                continue  # skip blank after tagline
            else
                echo "$line"
            fi
        done < "$DESCRIPTION"
        echo ""
        echo "---"
        echo ""
    fi

    # ── Download section ─────────────────────────────────────────────
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
            dates=($(git_dates "papers/$SLUG/$f" | tr '|' ' '))
            echo "| ${ext^^} | [$name]($link) | ${dates[0]:-————} | ${dates[1]:-————} |"
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
            dates=($(git_dates "papers/$SLUG/$f" | tr '|' ' '))
            echo "**[$title]($link)** — $tagline"
            echo ""
            echo "<small>Created: ${dates[0]:-————} · Updated: ${dates[1]:-————}</small>"
            echo ""
        done
    fi

} > "$README"

echo "  README $SLUG"
