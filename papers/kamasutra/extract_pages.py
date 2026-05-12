#!/usr/bin/env python3
"""Extract all pages from a PDF as PNG + base64 (.png.b64) files.

Usage:
    python3 extract_pages.py kama-sutra-1929.pdf 1929 353
    python3 extract_pages.py kama-sutra-2001.pdf 2001 248 --max-b64-mb 4.5
    python3 extract_pages.py kama-sutra-2001.pdf 2001 248 --resize 0.75
"""
import sys
import base64
from io import BytesIO
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image

def fit_b64(img: Image.Image, max_bytes: int) -> bytes:
    """Encode as PNG base64, downscaling iteratively until under max_bytes."""
    for _ in range(10):
        buf = BytesIO()
        img.save(buf, format='PNG', compress_level=9, optimize=True)
        b64 = base64.b64encode(buf.getvalue())
        if len(b64) <= max_bytes:
            return buf.getvalue()
        new_w = max(int(img.width * 0.8), 400)
        new_h = max(int(img.height * 0.8), 300)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format='PNG', compress_level=9, optimize=True)
    return buf.getvalue()

def main():
    pdf_name = sys.argv[1]
    edition = sys.argv[2]
    total = int(sys.argv[3])

    max_bytes = 0
    resize = 1.0

    i = 4
    while i < len(sys.argv):
        if sys.argv[i] == '--max-b64-mb':
            max_bytes = int(float(sys.argv[i + 1]) * 1_000_000)
            i += 2
        elif sys.argv[i] == '--resize':
            resize = float(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    out_dir = Path(f'work/{edition}/pages')
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = {int(f.stem.split('-')[1]) for f in out_dir.glob('page-*.png') if f.suffix == '.png'}

    # Backfill missing b64
    missing_b64 = []
    for f in sorted(out_dir.glob('page-*.png')):
        if f.suffix == '.png' and not (out_dir / (f.name + '.b64')).exists():
            missing_b64.append(f)
    if missing_b64:
        print(f'{edition}: generating {len(missing_b64)} missing b64 files')
        for png_path in missing_b64:
            b64 = base64.b64encode(png_path.read_bytes()).decode('ascii')
            (out_dir / (png_path.name + '.b64')).write_text(b64, encoding='ascii')

    needed = sorted([p for p in range(1, total + 1) if p not in existing])
    if not needed:
        print(f'{edition}: all {total} pages + b64 complete')
        return

    flags = []
    if resize != 1.0:
        flags.append(f'resize={resize}')
    if max_bytes:
        flags.append(f'max-b64={max_bytes//1000000}MB')
    print(f'{edition}: {len(needed)} pages ({", ".join(flags)})')
    for pg in needed:
        img = convert_from_path(pdf_name, dpi=300, first_page=pg, last_page=pg)[0]
        if resize != 1.0:
            img = img.resize(
                (int(img.width * resize), int(img.height * resize)),
                Image.LANCZOS,
            )
        if max_bytes:
            png_bytes = fit_b64(img, max_bytes)
        else:
            buf = BytesIO()
            img.save(buf, format='PNG', compress_level=9, optimize=True)
            png_bytes = buf.getvalue()

        png_path = out_dir / f'page-{pg:04d}.png'
        png_path.write_bytes(png_bytes)
        (out_dir / f'page-{pg:04d}.png.b64').write_text(
            base64.b64encode(png_bytes).decode('ascii'), encoding='ascii')

        if pg % 25 == 0:
            b64_kb = len(png_bytes) * 4 / 3 / 1024  # approx base64 size
            print(f'  {edition}: {pg}/{total} ({img.width}x{img.height}, ~{b64_kb:.0f}KB b64)')
    print(f'{edition}: done ({total} pages)')

if __name__ == '__main__':
    main()
