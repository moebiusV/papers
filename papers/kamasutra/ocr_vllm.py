#!/usr/bin/env python3
"""OCR pages using local vLLM DeepSeek-OCR-2 endpoint.

Saves:
  - Plain text to work/{edition}/pass1/
  - Full JSON with bounding boxes to work/{edition}/pass1_json/ (when available)

Supports split-page mode (--split): reads from pages_a/ and pages_b/,
saving output with a/b suffix (page-0001a.txt, page-0001b.txt).

Usage:
    python3 ocr_vllm.py 1929                    # all pages from pages/
    python3 ocr_vllm.py 1929 --split            # all pages from pages_a/ + pages_b/
    python3 ocr_vllm.py 1929 --split --start 1 --end 10
    python3 ocr_vllm.py 1929 --dry-run          # show what would run
"""
import sys
import json
import time
import requests
from pathlib import Path

BASE = Path(__file__).resolve().parent
WORK = BASE / "work"
OCR_URL = "http://localhost:8000/ocr"


def save_output(edition: str, page_stem: str, text: str, json_data: dict | None):
    """Save OCR output: plain text to pass1/, JSON+bboxes to pass1_json/."""
    pass1_dir = WORK / edition / "pass1"
    pass1_dir.mkdir(parents=True, exist_ok=True)

    out_file = pass1_dir / f"{page_stem}.txt"
    out_file.write_text(text, encoding="utf-8")

    if json_data:
        json_dir = WORK / edition / "pass1_json"
        json_dir.mkdir(parents=True, exist_ok=True)
        json_file = json_dir / f"{page_stem}.json"
        json_file.write_text(json.dumps(json_data, ensure_ascii=False, indent=2),
                            encoding="utf-8")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="OCR pages via local vLLM DeepSeek-OCR-2")
    ap.add_argument("edition", help="Edition: 1929 or 2001")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=120, help="seconds per page")
    ap.add_argument("--force", action="store_true", help="Re-OCR even if output exists")
    ap.add_argument("--split", action="store_true",
                    help="OCR from pages_a/ and pages_b/ (split-page mode)")
    args = ap.parse_args()

    edition = args.edition

    if args.split:
        source_dirs = [
            (WORK / edition / "pages_a", "a"),
            (WORK / edition / "pages_b", "b"),
        ]
    else:
        source_dirs = [(WORK / edition / "pages", "")]

    pass1_dir = WORK / edition / "pass1"
    pass1_dir.mkdir(parents=True, exist_ok=True)

    # Collect all pages from all source dirs, interleave A/B
    jobs = []  # (png_path, page_stem)
    for src_dir, suffix in source_dirs:
        for png in sorted(src_dir.glob("page-*.png")):
            stem = png.stem  # e.g. "page-0001"
            page_stem = stem + suffix if suffix else stem
            jobs.append((png, page_stem))

    if not jobs:
        print(f"No pages found in source directories")
        return

    # Sort interleaved: 0001a, 0001b, 0002a, 0002b, ...
    def _sort_key(job):
        stem = job[1]  # "page-0001a"
        num = int(stem.split("-")[1].rstrip("ab"))
        suf = stem[-1] if stem[-1] in "ab" else ""
        return (num, suf)

    jobs.sort(key=_sort_key)

    # Filter by page number range
    def page_num(stem):
        return int(stem.split("-")[1].rstrip("ab"))

    if args.end > 0:
        jobs = [(p, s) for p, s in jobs
                if args.start <= page_num(s) <= args.end]
    elif args.start > 1:
        jobs = [(p, s) for p, s in jobs
                if page_num(s) >= args.start]

    # Filter already-done
    if not args.force:
        jobs = [(p, s) for p, s in jobs
                if not (pass1_dir / f"{s}.txt").exists()
                or (pass1_dir / f"{s}.txt").stat().st_size <= 20]

    total = len(jobs)
    suffix_info = " (split A/B)" if args.split else ""
    print(f"OCR {edition}{suffix_info}: {total} pages to process")
    print(f"Endpoint: {OCR_URL}")

    if args.dry_run:
        print("[dry run]")
        for png, stem in jobs[:20]:
            print(f"  {stem}")
        if total > 20:
            print(f"  ... and {total - 20} more")
        return

    ok, fail = 0, 0
    for idx, (png_path, page_stem) in enumerate(jobs, 1):
        print(f"  [{idx}/{total}] {page_stem} ", end="", flush=True)
        try:
            with open(png_path, "rb") as f:
                resp = requests.post(OCR_URL,
                    files={"file": (png_path.name, f, "image/png")},
                    data={"mode": "markdown"},
                    timeout=args.timeout)

            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                json_data = None

                if "application/json" in content_type:
                    json_data = resp.json()
                    text = json_data.get("text", "")
                    regions = json_data.get("regions", [])
                    bbox_count = len(regions)
                    chars = json_data["page"].get("total_chars", len(text))
                    deva = json_data["page"].get("devanagari_chars",
                            sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F))
                    print(f"ok ({deva} deva chars, {bbox_count} regions)",
                          flush=True)

                elif "text/plain" in content_type or not content_type:
                    text = resp.text.strip()
                    chars = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
                    print(f"ok ({chars} deva chars)", flush=True)
                else:
                    text = resp.text.strip()
                    chars = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
                    print(f"ok ({chars} deva chars, unknown content type)",
                          flush=True)

                save_output(edition, page_stem, text, json_data)
                ok += 1
            else:
                print(f"HTTP {resp.status_code}: {resp.text[:100]}", flush=True)
                fail += 1

        except requests.exceptions.Timeout:
            print(f"TIMEOUT ({args.timeout}s)")
            fail += 1
        except Exception as e:
            print(f"ERROR: {e}")
            fail += 1

        time.sleep(args.delay)

    print(f"\nDone: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
