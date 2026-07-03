#!/usr/bin/env bash
# generate-readme.sh — produce README.md from DESCRIPTION.md + Makefile file lists
# Called from a paper's Makefile `readme` target.
# Expects env vars: SOURCES, PDFS, DOCXS, BUILDS (paths relative to paper dir)
# For each source file, looks for <file>.desc sidecar with title on line 1, description on line 2.
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
BUILDS="${BUILDS:-}"

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

# Relative link from paper dir to a target (usually just the filename)
# Files live in the same directory as README.
relpath() {
    python3 -c "import os; print(os.path.relpath('$1', '$PAPER_DIR'))"
}

# Read .desc sidecar: line 1 = title, line 2 = description
desc_data() {
    local descfile="${1}.desc"
    local title="$(basename "$1")"
    local desc=""
    if [[ -f "$descfile" ]]; then
        title=$(head -1 "$descfile")
        desc=$(sed -n '2p' "$descfile")
    elif [[ "$1" == *.md ]]; then
        local h1
        h1=$(grep -m1 '^# ' "$1" 2>/dev/null | sed 's/^# //')
        [[ -n "$h1" ]] && title="$h1"
    fi
    echo "$title|$desc"
}

# ═══════════════════════════════════════════════════════════════════════
{
    # ── Description block ────────────────────────────────────────────
    if [[ -f "$DESCRIPTION" ]]; then
        cat "$DESCRIPTION"
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

    # ── Source files ─────────────────────────────────────────────────
    if [[ -n "${SOURCES:-}" ]]; then
        echo "## Contents"
        echo ""
        for f in $SOURCES; do
            [[ -n "$f" ]] || continue
            path="$PAPER_DIR/$f"
            name="${f##*/}"
            link=$(relpath "$path")
            title=$(desc_data "$path" | cut -d'|' -f1)
            [[ -z "$title" ]] && title="$name"
            desc=$(desc_data "$path" | cut -d'|' -f2-)
            dates=($(git_dates "papers/$SLUG/$f" | tr '|' ' '))
            echo "**[$title]($link)** — $desc"
            echo ""
            echo "<small>Created: ${dates[0]:-————} · Updated: ${dates[1]:-————}</small>"
            echo ""
        done
    fi

    # ── Build ────────────────────────────────────────────────────────
    if [[ -n "${BUILDS:-}" ]]; then
        echo "## Build"
        echo ""
        echo "| File | Description |"
        echo "|---|---|"
        for f in $BUILDS; do
            [[ -n "$f" ]] || continue
            path="$PAPER_DIR/$f"
            name="${f##*/}"
            link=$(relpath "$path")
            desc=""
            case "$name" in
                Makefile) desc="Build configuration + file inventory" ;;
                build.sh) desc="Convenience build script" ;;
                book.typ) desc="Typst typesetting source" ;;
            esac
            echo "| [$name]($link) | $desc |"
        done
        echo ""
    fi
} > "$README"

echo "  README $SLUG"
