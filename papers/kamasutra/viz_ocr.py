#!/usr/bin/env python3
"""Generate a side-by-side OCR verification PDF using ImageMagick + Typst.

ImageMagick draws yellow bounding boxes directly on a copy of the image
(in pixel coordinates, no scaling). Typst does the side-by-side layout
with OCR text.

Usage:
    python3 viz_ocr.py work/1929/pages/page-0013.png \\
                       work/1929/pass1_json/page-0013a.json \\
                       -o /tmp/page-0013a-check.pdf
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path

FONT_DIR = Path.home() / ".fonts"
FONT_FAMILY = "Noto Sans Devanagari"
IMAGE_WIDTH = 360  # pt
GAP = 14           # pt between image and text
MARGIN = 16        # pt page margin


def generate_typst(image_path: Path, json_paths: list[Path], output_pdf: Path):
    img_w_px, img_h_px = get_image_size(image_path)
    scale = IMAGE_WIDTH / img_w_px
    img_h_pt = img_h_px * scale
    text_width = IMAGE_WIDTH

    # Collect regions
    all_regions = []
    for jp in json_paths:
        with open(jp) as f:
            data = json.load(f)
        for i, region in enumerate(data.get("regions", [])):
            all_regions.append({
                "bbox": region["bbox"],
                "text": region["text"],
                "source": jp.stem.replace("page-", ""),
                "idx": i + 1,
            })

    # Step 1: Draw yellow boxes on image copy with ImageMagick
    work_dir = output_pdf.parent
    annotated = work_dir / f"_annotated_{image_path.name}"
    shutil.copy2(image_path, annotated)

    scale_x = img_w_px / 1000
    scale_y = img_h_px / 1000
    for r in all_regions:
        x1, y1, x2, y2 = r["bbox"]
        x1_px = int(x1 * scale_x)
        y1_px = int(y1 * scale_y)
        x2_px = int(x2 * scale_x)
        y2_px = int(y2 * scale_y)
        subprocess.run([
            "convert", str(annotated),
            "-fill", "none",
            "-stroke", "#FFD700",
            "-strokewidth", "3",
            "-draw", f"rectangle {x1_px},{y1_px} {x2_px},{y2_px}",
            str(annotated),
        ], check=True)

    # Step 2: Build Typst layout (image + text columns)
    text_lines = []
    for r in all_regions:
        label = f"[{r['idx']}/{r['source']}]"
        escaped = _escape_typst(r["text"])
        text_lines.append(
            f"    [ #text(size: 0.8em, fill: rgb(\"#999999\"))[{label}]"
            f"\\ #text(fill: rgb(\"#1a1a1a\"))[{escaped}] ]")

    page_w = IMAGE_WIDTH + GAP + text_width + 2 * MARGIN
    text_h_est = max(img_h_pt, len(all_regions) * 24 + 20)
    page_h = text_h_est + 2 * MARGIN

    typst_src = f"""#set page(width: {page_w:.1f}pt, height: {page_h:.1f}pt, margin: {MARGIN}pt)
#set text(font: "{FONT_FAMILY}", size: 10pt, lang: "hi")

// Left panel: image at fixed size
#place(top + left, dx: 0pt, dy: 0pt,
  image("{annotated.name}", width: {IMAGE_WIDTH:.1f}pt))

// Right panel: text column at fixed offset
#place(top + left, dx: {IMAGE_WIDTH + GAP:.1f}pt, dy: 0pt,
  block(width: {text_width:.1f}pt, spacing: 0.6em,[
{chr(10).join(text_lines)}
  ]))
"""

    typst_path = output_pdf.with_suffix(".typ")
    typst_path.write_text(typst_src, encoding="utf-8")

    result = subprocess.run([
        "typst", "compile",
        "--font-path", str(FONT_DIR),
        str(typst_path), str(output_pdf),
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Typst error:\n{result.stderr}", file=sys.stderr)
        print(f"Typst source kept at: {typst_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved: {output_pdf}")
    print(f"Typst: {typst_path}")


def _escape_typst(text: str) -> str:
    # Escape Typst special characters
    text = text.replace("\\", "\\\\")
    text = text.replace("#", "\\#")
    return text


def get_image_size(path: Path) -> tuple[int, int]:
    from PIL import Image
    img = Image.open(path)
    return img.size


def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Generate OCR verification PDF with bounding boxes")
    ap.add_argument("image", type=Path, help="Original page PNG")
    ap.add_argument("jsons", type=Path, nargs="+",
                    help="One or more OCR JSON files")
    ap.add_argument("-o", "--output", type=Path, required=True,
                    help="Output PDF path")
    args = ap.parse_args()

    if not shutil.which("typst"):
        print("Error: typst not found", file=sys.stderr)
        sys.exit(1)
    if not shutil.which("convert"):
        print("Error: ImageMagick convert not found", file=sys.stderr)
        sys.exit(1)
    if not Path(FONT_DIR, "NotoSansDevanagari-Regular.ttf").exists():
        print(f"Error: font not found at {FONT_DIR}", file=sys.stderr)
        sys.exit(1)

    generate_typst(args.image.resolve(), [j.resolve() for j in args.jsons],
                   args.output.resolve())


if __name__ == "__main__":
    main()
