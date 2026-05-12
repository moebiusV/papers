#!/usr/bin/env python3
"""OCR pages using local vLLM DeepSeek-OCR-2 endpoint.

Saves text to work/{edition}/pass1/.

Usage:
    python3 ocr_vllm.py 1929                    # all pages
    python3 ocr_vllm.py 1929 --start 1 --end 10 # first 10 pages
    python3 ocr_vllm.py 1929 --dry-run          # show what would run
"""
import sys
import time
import requests
from pathlib import Path

BASE = Path(__file__).resolve().parent
WORK = BASE / "work"
OCR_URL = "http://localhost:8000/ocr"

def main():
    import argparse
    ap = argparse.ArgumentParser(description="OCR pages via local vLLM DeepSeek-OCR-2")
    ap.add_argument("edition", help="Edition: 1929 or 2001")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=120, help="seconds per page")
    args = ap.parse_args()

    edition = args.edition
    pages_dir = WORK / edition / "pages"
    pass1_dir = WORK / edition / "pass1"
    pass1_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(pages_dir.glob("page-*.png"))
    if not pngs:
        print(f"No pages found in {pages_dir}")
        return

    max_page = max(int(f.stem.split("-")[1]) for f in pngs)
    end = args.end if args.end > 0 else max_page
    total = end - args.start + 1

    print(f"OCR {edition}: pages {args.start}-{end} ({total} pages)")
    print(f"Endpoint: {OCR_URL}")

    if args.dry_run:
        print("[dry run]")
        return

    ok, fail, skipped = 0, 0, 0
    for pg in range(args.start, end + 1):
        out_file = pass1_dir / f"page-{pg:04d}.txt"
        if out_file.exists() and out_file.stat().st_size > 20:
            skipped += 1
            if total <= 50:
                print(f"  [{pg}/{end}] done, skip")
            continue

        png_path = pages_dir / f"page-{pg:04d}.png"
        if not png_path.exists():
            print(f"  [{pg}/{end}] no image, skip")
            skipped += 1
            continue

        print(f"  [{pg}/{end}] ", end="", flush=True)
        try:
            with open(png_path, "rb") as f:
                resp = requests.post(OCR_URL,
                    files={"file": (png_path.name, f, "image/png")},
                    data={"mode": "markdown"},
                    timeout=args.timeout)
            if resp.status_code == 200:
                text = resp.text.strip()
                out_file.write_text(text, encoding="utf-8")
                chars = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
                print(f"ok ({chars} deva chars)")
                ok += 1
            else:
                print(f"HTTP {resp.status_code}")
                fail += 1
        except requests.exceptions.Timeout:
            print(f"TIMEOUT ({args.timeout}s)")
            fail += 1
        except Exception as e:
            print(f"ERROR: {e}")
            fail += 1
        time.sleep(args.delay)

    print(f"\nDone: {ok} ok, {skipped} skipped, {fail} failed")

if __name__ == "__main__":
    main()
