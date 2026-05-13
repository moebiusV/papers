#!/usr/bin/env python3
"""Split page PNGs into top (A) and bottom (B) halves, composited over
full-size white backgrounds so the OCR model allocates full token budget.

A = top 55%, anchored to top of white canvas
B = bottom 55%, anchored to top of white canvas
Overlap = 10% of page height

Uses ImageMagick for compositing and maximum PNG compression.
Output: work/{edition}/pages_a/ and work/{edition}/pages_b/
"""

import sys
import subprocess
from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parent
WORK = BASE / "work"


def split_pages(edition: str, dry_run: bool = False):
    pages_dir = WORK / edition / "pages"
    a_dir = WORK / edition / "pages_a"
    b_dir = WORK / edition / "pages_b"

    pngs = sorted(pages_dir.glob("page-*.png"))
    if not pngs:
        print(f"No pages found in {pages_dir}")
        return

    if not dry_run:
        a_dir.mkdir(parents=True, exist_ok=True)
        b_dir.mkdir(parents=True, exist_ok=True)

    split_a = 0.55   # top crop covers top 55%
    split_b = 0.45   # bottom crop starts at 45%

    for png in pngs:
        img = Image.open(png)
        w, h = img.size

        a_h = int(h * split_a)
        b_y = int(h * split_b)

        print(f"{png.name}: {w}x{h} A=0..{a_h} B={b_y}..{h}")

        if dry_run:
            continue

        # Crop A (top 55%) and B (bottom 55%) with ImageMagick
        a_crop = a_dir / png.name
        b_crop = b_dir / png.name

        # A: crop top, composite onto full-size white canvas (anchored top)
        subprocess.run([
            "convert", str(png),
            "-crop", f"{w}x{a_h}+0+0", "+repage",
            "-background", "white",
            "-gravity", "north",
            "-extent", f"{w}x{h}",
            "-define", "png:compression-level=9",
            "-define", "png:compression-filter=5",
            "-define", "png:compression-strategy=1",
            str(a_crop),
        ], check=True)

        # B: crop bottom, composite onto full-size white canvas (anchored top)
        subprocess.run([
            "convert", str(png),
            "-crop", f"{w}x{h - b_y}+0+{b_y}", "+repage",
            "-background", "white",
            "-gravity", "north",
            "-extent", f"{w}x{h}",
            "-define", "png:compression-level=9",
            "-define", "png:compression-filter=5",
            "-define", "png:compression-strategy=1",
            str(b_crop),
        ], check=True)

    print(f"\nSplit {len(pngs)} pages into {a_dir} and {b_dir}")


def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Split page PNGs into top/bottom halves for OCR")
    ap.add_argument("edition", help="Edition: 1929 or 2001")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    split_pages(args.edition, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
