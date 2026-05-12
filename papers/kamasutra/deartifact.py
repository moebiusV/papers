#!/usr/bin/env python3
"""De-artifact OCR output using Grok (xAI) and DeepSeek side-by-side.

Reads raw OCR from work/{edition}/pass1/, sends each page to both models
for OCR artifact cleanup, saves to work/{edition}/pass2/{model}/.

Chain of custody: pass1 is never modified. pass2 is the cleaned output.
Each model gets its own directory so outputs can be compared.

Usage:
    python3 deartifact.py                          # both editions, both models
    python3 deartifact.py --edition 1929           # 1929 only
    python3 deartifact.py --model grok             # Grok only
    python3 deartifact.py --max 5                  # first 5 pages only (test)
    python3 deartifact.py --show-prompt            # show the prompts
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
WORK_DIR = BASE / "work"

# ── Prompt ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Sanskrit philologist. Below is OCR output from a printed Devanagari edition of the Kama Sutra (Vatsyayana).

The OCR was performed by a vision model on photographed book pages. It contains typical OCR artifacts:
- Misrecognized characters (e.g., ब/व confusion, स/श confusion, भ/म confusion)
- Dropped or spurious anusvara (ं), visarga (ः), and virama (्)
- Spacing irregularities (run-together words, split compounds)
- Garbled or hallucinated character sequences
- Danda (।) and double-danda (॥) may be missing or misplaced

## Instructions

1. Fix OCR errors using your knowledge of Sanskrit and the Kama Sutra.
2. Preserve ALL text: root sutras AND commentary. Do not delete or summarize.
3. Normalize spacing: separate words appropriately per standard Devanagari conventions.
4. Ensure dandas (। and ॥) are correctly placed at sentence/clause boundaries.
5. Do NOT change the wording, grammar, or content — only fix OCR artifacts.
6. If a passage is genuinely unreadable, mark it with [?] rather than guessing.

Output ONLY the corrected Devanagari text. No explanations, no markdown, no English."""


def build_user_message(raw_text: str, edition: str, page_num: int) -> str:
    """Build the user message with the raw OCR text."""
    label = {2001: "2001 edition (modern Hindi commentary, Devanagari)",
             1929: "1929 edition (Jayamangala Sanskrit commentary, Devanagari)"}
    ed_label = label.get(int(edition), f"{edition} edition")

    return f"""## {ed_label}, page {page_num}

{raw_text}"""


# ── API clients ──────────────────────────────────────────────────────────────

def get_grok_client():
    """Create OpenAI-compatible client for xAI Grok."""
    from openai import OpenAI
    key_file = Path.home() / ".xai_api_key"
    if not key_file.exists():
        print("Error: ~/.xai_api_key not found", file=sys.stderr)
        sys.exit(1)
    api_key = key_file.read_text().strip()
    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )


def get_deepseek_client():
    """Create Anthropic-compatible client for DeepSeek."""
    from anthropic import Anthropic
    ds_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if not ds_key:
        key_file = Path.home() / ".anthropic_api_key"
        if key_file.exists():
            ds_key = key_file.read_text().strip()
    if not ds_key:
        print("Error: set ANTHROPIC_AUTH_TOKEN or ~/.anthropic_api_key", file=sys.stderr)
        sys.exit(1)
    return Anthropic(
        api_key=ds_key,
        base_url="https://api.deepseek.com/anthropic",
    )


# ── Model-specific API calls ─────────────────────────────────────────────────

def call_grok(client, system_prompt: str, user_message: str, model: str = "grok-3") -> str:
    """Send to Grok via OpenAI-compatible API."""
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def call_deepseek(client, system_prompt: str, user_message: str, model: str = "deepseek-v4-pro") -> str:
    """Send to DeepSeek via Anthropic-compatible API."""
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[{"type": "text", "text": system_prompt}],
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


# ── Core processing ──────────────────────────────────────────────────────────

def process_page(
    page_path: Path,
    edition: str,
    models: list[str],
    clients: dict,
    out_dirs: dict,
    delay: float = 0.5,
) -> dict:
    """Process one page through specified models. Returns results dict."""
    page_num = int(page_path.stem.split("-")[1])
    raw_text = page_path.read_text(encoding="utf-8")

    if not raw_text.strip():
        # Empty page — write empty output for all models
        for model in models:
            out_path = out_dirs[model] / page_path.name
            out_path.write_text("", encoding="utf-8")
        return {"page": page_num, "status": "empty", "models": {}}

    user_msg = build_user_message(raw_text, edition, page_num)
    results = {"page": page_num, "status": "ok", "models": {}}

    for model in models:
        out_path = out_dirs[model] / page_path.name
        if out_path.exists():
            # Already processed — skip
            results["models"][model] = "skipped"
            continue

        try:
            if model == "grok":
                cleaned = call_grok(clients["grok"], SYSTEM_PROMPT, user_msg)
            elif model == "deepseek":
                cleaned = call_deepseek(clients["deepseek"], SYSTEM_PROMPT, user_msg)
            else:
                raise ValueError(f"Unknown model: {model}")

            out_path.write_text(cleaned, encoding="utf-8")
            results["models"][model] = "ok"
            time.sleep(delay)

        except Exception as e:
            print(f"  ERROR [{model}]: {e}", file=sys.stderr)
            results["models"][model] = f"error: {e}"
            # Write error marker so we can retry
            out_path.write_text(f"ERROR: {e}", encoding="utf-8")

    return results


def process_edition(
    edition: str,
    models: list[str],
    max_pages: int = 0,
    delay: float = 0.5,
) -> dict:
    """Process all pages of one edition through specified models."""
    src_dir = WORK_DIR / edition / "pass1"
    if not src_dir.exists():
        print(f"Source directory not found: {src_dir}")
        return {"edition": edition, "error": "no pass1 dir"}

    pages = sorted(src_dir.glob("page-*.txt"))
    if not pages:
        print(f"No pages found in {src_dir}")
        return {"edition": edition, "error": "no pages"}

    if max_pages:
        pages = pages[:max_pages]

    # Set up output directories
    out_dirs = {}
    for model in models:
        out_dir = WORK_DIR / edition / "pass2" / model
        out_dir.mkdir(parents=True, exist_ok=True)
        out_dirs[model] = out_dir

    # Create clients for requested models
    clients = {}
    if "grok" in models:
        clients["grok"] = get_grok_client()
    if "deepseek" in models:
        clients["deepseek"] = get_deepseek_client()

    total = len(pages)
    stats = {"edition": edition, "total": total, "processed": 0,
             "skipped": 0, "errors": 0, "empty": 0}

    for i, page_path in enumerate(pages):
        page_num = int(page_path.stem.split("-")[1])
        done_models = []
        for m in models:
            out_path = out_dirs[m] / page_path.name
            if out_path.exists() and out_path.stat().st_size > 0:
                done_models.append(m)
        if set(done_models) == set(models):
            stats["skipped"] += 1
            if total <= 20:
                print(f"[{edition} {i+1}/{total}] page {page_num:04d} — already done ({', '.join(done_models)})")
            continue

        print(f"[{edition} {i+1}/{total}] page {page_num:04d} ", end="", flush=True)

        result = process_page(page_path, edition, models, clients, out_dirs, delay)

        model_status = result["models"]
        for m in models:
            s = model_status.get(m, "missing")
            if s == "ok":
                print(f"[{m}:ok] ", end="", flush=True)
                stats["processed"] += 1
            elif s == "skipped":
                print(f"[{m}:skip] ", end="", flush=True)
                stats["skipped"] += 1
            else:
                print(f"[{m}:ERR] ", end="", flush=True)
                stats["errors"] += 1
        print()

    return stats


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="De-artifact OCR output with Grok and DeepSeek")
    ap.add_argument("--edition", type=str, help="Process only this edition (2001 or 1929)")
    ap.add_argument("--model", type=str, action="append", dest="models",
                    help="Use only this model (can repeat: --model grok --model deepseek)")
    ap.add_argument("--max", type=int, default=0, help="Max pages per edition (0=all)")
    ap.add_argument("--delay", type=float, default=0.5, help="Delay between API calls")
    ap.add_argument("--show-prompt", action="store_true", help="Show the system prompt")
    args = ap.parse_args()

    if args.show_prompt:
        print("=" * 72)
        print("SYSTEM PROMPT:")
        print("=" * 72)
        print(SYSTEM_PROMPT)
        print()
        print("=" * 72)
        print("USER MESSAGE TEMPLATE:")
        print("=" * 72)
        print(build_user_message("{RAW_OCR_TEXT}", "2001", 0))
        return

    models = args.models if args.models else ["grok", "deepseek"]
    editions = [args.edition] if args.edition else ["1929", "2001"]

    print(f"Editions: {editions}")
    print(f"Models: {models}")
    print(f"Max pages per edition: {args.max if args.max else 'all'}")
    print()

    all_stats = {}
    for edition in editions:
        stats = process_edition(edition, models, max_pages=args.max, delay=args.delay)
        all_stats[edition] = stats
        print()

    # Summary
    print("=" * 60)
    for edition, stats in all_stats.items():
        print(f"{edition}: total={stats.get('total',0)} "
              f"processed={stats.get('processed',0)} "
              f"skipped={stats.get('skipped',0)} "
              f"errors={stats.get('errors',0)}")


if __name__ == "__main__":
    main()
