#!/usr/bin/env bash
set -euo pipefail

# split-pdf.sh — split a PDF into individual pages
# Usage: ./split-pdf.sh [input.pdf] [output_dir]

INPUT="${1:-kama-sutra-2001.pdf}"
OUTDIR="${2:-pages}"

if [[ ! -f "$INPUT" ]]; then
    echo "Error: '$INPUT' not found" >&2
    exit 1
fi

mkdir -p "$OUTDIR"

echo "Splitting $INPUT into $OUTDIR/ ..."
qpdf --split-pages "$INPUT" "$OUTDIR/page-%d.pdf"

count=$(ls "$OUTDIR"/*.pdf 2>/dev/null | wc -l)
echo "Done — $count pages written to $OUTDIR/"
