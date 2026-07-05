#!/usr/bin/env python3
"""De-artifact OCR output using Grok (xAI) and DeepSeek side-by-side.

Reads raw OCR from work/{edition}/pass1/, sends each page to each model
independently for OCR artifact cleanup, saves to work/{edition}/pass2/{model}/.

Each model runs independently — Grok can race ahead while DeepSeek chugs.
Stop when each model reaches the end of available pass1 pages.

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
from pathlib import Path

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

The book also contains front matter and back matter — pages in English, Hindi, or other modern languages (title pages, tables of contents, publisher information, library stamps, indexes). These are legitimate parts of the edition.

## Instructions

1. Fix OCR errors using your knowledge of Sanskrit and the Kama Sutra.
2. Preserve ALL text: root sutras AND commentary. Do not delete or summarize.
3. Normalize spacing: separate words appropriately per standard Devanagari conventions.
4. Ensure dandas (। and ॥) are correctly placed at sentence/clause boundaries.
5. Do NOT change the wording, grammar, or content — only fix OCR artifacts.
6. FRONT MATTER: If the page contains English, Hindi, or other non-Sanskrit text (title pages, library stamps, tables of contents), preserve it exactly as written. Fix OCR errors in those languages but do NOT translate or convert them into Sanskrit.
7. If a passage is genuinely unreadable, mark it with [?] rather than guessing.

Output ONLY the corrected text. No explanations, no markdown, no commentary."""


TITUS_SYSTEM_PROMPT = """You are a Sanskrit philologist. Below is the Devanagari text of the Kama Sutra root sutras, from the TITUS digital critical edition.

This text was automatically transliterated from Roman (IAST) to Devanagari by a rule-based script. It is NOT OCR — it is a typed digital edition maintained by Indologists at the University of Frankfurt. However, it may contain:

- Transliterator artifacts (Roman→Devanagari mapping errors, e.g., doubled avagraha, incorrect conjunct handling)
- Editorial inconsistencies (punctuation, danda placement, numbering)
- Possible textual corruptions inherited from the source manuscripts
- Sandhi normalization issues

## Instructions

1. Review the text for philological correctness using your knowledge of Sanskrit and the Kama Sutra.
2. Fix transliterator artifacts: incorrect conjuncts, doubled characters, spurious or missing virama/halant, incorrect anusvara placement.
3. Ensure dandas (। and ॥) are correctly placed at sentence and verse boundaries.
4. Normalize sandhi where it is clearly incorrect or inconsistent.
5. Do NOT change the wording or content — this is a critical edition text, not OCR. Only fix clear errors.
6. If a passage appears textually corrupt, mark it with [?] rather than guessing.
7. Preserve the sentence numbering markers like [1.1.1], [1.1.2], etc.

Output ONLY the corrected text. No explanations, no markdown, no commentary."""


def build_user_message(raw_text: str, edition: str, page_stem: str) -> str:
    label = {2001: "2001 edition (modern Hindi commentary, Devanagari)",
             1929: "1929 edition (Jayamangala Sanskrit commentary, Devanagari)",
             "titus": "TITUS digital critical edition (Devanagari transliteration)"}
    ed_label = label.get(int(edition) if edition not in ("titus",) else edition,
                         f"{edition} edition")
    return f"""## {ed_label}, page {page_stem}

{raw_text}"""


# ── API clients ──────────────────────────────────────────────────────────────

def get_grok_client():
    from openai import OpenAI
    key_file = Path.home() / ".xai_api_key"
    if not key_file.exists():
        print("Error: ~/.xai_api_key not found", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=key_file.read_text().strip(), base_url="https://api.x.ai/v1")


def get_deepseek_client():
    from anthropic import Anthropic
    ds_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if not ds_key:
        key_file = Path.home() / ".anthropic_api_key"
        if key_file.exists():
            ds_key = key_file.read_text().strip()
    if not ds_key:
        print("Error: set ANTHROPIC_AUTH_TOKEN or ~/.anthropic_api_key", file=sys.stderr)
        sys.exit(1)
    return Anthropic(api_key=ds_key, base_url="https://api.deepseek.com/anthropic")


# ── Model-specific API calls ─────────────────────────────────────────────────

def call_grok(client, system_prompt: str, user_message: str, model: str = "grok-4.3") -> str:
    response = client.chat.completions.create(
        model=model, max_tokens=8192,
        extra_body={"prompt_cache_key": "ocr-deartifact-v1"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def call_deepseek(client, system_prompt: str, user_message: str, model: str = "deepseek-v4-pro") -> str:
    response = client.messages.create(
        model=model, max_tokens=8192,
        system=[{"type": "text", "text": system_prompt}],
        messages=[{"role": "user", "content": user_message}],
        extra_body={"thinking": {"type": "disabled"}},
    )
    text = ""
    thinking = ""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            text += block.text
        if hasattr(block, "thinking") and block.thinking:
            thinking += block.thinking
    stop_reason = getattr(response, "stop_reason", None)
    if stop_reason == "max_tokens":
        if thinking and not text:
            print(f"      [deepseek] WARNING: all {len(thinking)} thinking chars, 0 text — thinking may not be disabled", file=sys.stderr)
        else:
            print(f"      [deepseek] WARNING: stop_reason=max_tokens (got {len(text)} chars)", file=sys.stderr)
    elif stop_reason == "end_turn":
        if not text.strip():
            print(f"      [deepseek] WARNING: stop_reason=end_turn but empty text", file=sys.stderr)
    return text


# ── Merge prompt ─────────────────────────────────────────────────────────────

MERGE_SYSTEM_PROMPT = """You are a Sanskrit philologist. Below are two independently cleaned versions of the same OCR output from a printed Devanagari edition of the Kama Sutra (Vatsyayana).

Each version was produced by a different model fixing OCR artifacts in the same raw OCR. They may have caught different errors.

## Instructions

1. Combine the best corrections from BOTH versions into a single merged text.
2. If Version A fixed a misrecognized character and Version B fixed spacing, apply BOTH fixes.
3. For each difference, choose the reading that is more philologically sound Sanskrit — correct grammar, proper sandhi, attested vocabulary, consistency with the Kama Sutra tradition.
4. If both versions are plausible, prefer the one closer to the original printed text (fewer speculative emendations).
5. If neither reading is satisfactory and the original OCR was garbled, mark with [?].
6. Do NOT introduce new changes beyond what is present in at least one of the two versions.

Output ONLY the merged corrected text. No explanations, no commentary, no diff markers."""


def build_merge_message(ds_text: str, grok_text: str, edition: str, page_stem: str) -> str:
    label = {2001: "2001 edition (modern Hindi commentary, Devanagari)",
             1929: "1929 edition (Jayamangala Sanskrit commentary, Devanagari)"}
    ed_label = label.get(int(edition), f"{edition} edition")
    return f"""## {ed_label}, page {page_stem}

### Version A (DeepSeek)
{ds_text}

### Version B (Grok)
{grok_text}"""


def process_merge(edition: str, max_pages: int = 0, delay: float = 0.5) -> dict:
    """Compare DeepSeek and Grok outputs, merge best corrections.

    Reads from pass2/deepseek/ and pass2/grok/, writes to pass2/merged/.
    Only runs when both inputs exist.
    """
    ds_dir = WORK_DIR / edition / "pass2" / "deepseek"
    grok_dir = WORK_DIR / edition / "pass2" / "grok"
    out_dir = WORK_DIR / edition / "pass2" / "merged"
    out_dir.mkdir(parents=True, exist_ok=True)

    ds_pages = {p.name: p for p in sorted(ds_dir.glob("page-*.txt"))}
    grok_pages = {p.name: p for p in sorted(grok_dir.glob("page-*.txt"))}

    common = sorted(set(ds_pages) & set(grok_pages))
    if not common:
        print("  [merge] no pages with both DeepSeek and Grok outputs")
        return {"model": "merge", "processed": 0, "skipped": 0, "errors": 0}

    if max_pages:
        common = common[:max_pages]

    client = get_deepseek_client()
    total = len(common)
    ok, skipped, errors = 0, 0, 0

    for name in common:
        page_stem = Path(name).stem
        out_path = out_dir / name

        if out_path.exists() and out_path.stat().st_size > 20 and not out_path.read_text(encoding="utf-8").startswith("ERROR"):
            skipped += 1
            continue

        ds_text = ds_pages[name].read_text(encoding="utf-8")
        grok_text = grok_pages[name].read_text(encoding="utf-8")

        if not ds_text.strip() and not grok_text.strip():
            out_path.write_text("", encoding="utf-8")
            ok += 1
            continue

        user_msg = build_merge_message(ds_text, grok_text, edition, page_stem)
        try:
            merged = call_deepseek(client, MERGE_SYSTEM_PROMPT, user_msg)
            out_path.write_text(merged, encoding="utf-8")
            deva = sum(1 for c in merged if 0x0900 <= ord(c) <= 0x097F)
            print(f"  [merge] {page_stem} ok ({deva} deva chars)")
            ok += 1
        except Exception as e:
            print(f"  [merge] {page_stem} ERROR: {e}", file=sys.stderr)
            out_path.write_text(f"ERROR: {e}", encoding="utf-8")
            errors += 1

        time.sleep(delay)

    return {"model": "merge", "processed": ok, "skipped": skipped, "errors": errors}


# ── Per-model processing (independent loops) ────────────────────────────────

MODEL_CONFIG = {
    "grok":     {"get_client": get_grok_client, "call_fn": call_grok},
    "deepseek": {"get_client": get_deepseek_client, "call_fn": call_deepseek},
}


def process_model(edition: str, model: str, max_pages: int = 0, delay: float = 0.5) -> dict:
    """Process pages for a single model independently.

    Reads from pass1/, writes to pass2/{model}/. Skips pages already done.
    Stops when it reaches the last available page in pass1.
    """
    src_dir = WORK_DIR / edition / "pass1"
    out_dir = WORK_DIR / edition / "pass2" / model
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = sorted(src_dir.glob("page-*.txt"))
    if not pages:
        print(f"  [{model}] no pass1 pages found")
        return {"model": model, "processed": 0, "skipped": 0, "errors": 0}

    if max_pages:
        pages = pages[:max_pages]

    cfg = MODEL_CONFIG[model]
    client = cfg["get_client"]()
    call_fn = cfg["call_fn"]

    total = len(pages)
    ok, skipped, errors = 0, 0, 0

    for page_path in pages:
        page_stem = page_path.stem  # "page-0001a", "page-0001b", or "page-0001"
        out_path = out_dir / page_path.name

        if out_path.exists() and out_path.stat().st_size > 20 and not out_path.read_text(encoding="utf-8").startswith("ERROR"):
            skipped += 1
            continue

        raw_text = page_path.read_text(encoding="utf-8")
        if not raw_text.strip():
            out_path.write_text("", encoding="utf-8")
            ok += 1
            continue

        user_msg = build_user_message(raw_text, edition, page_stem)
        try:
            cleaned = call_fn(client, SYSTEM_PROMPT, user_msg)
            out_path.write_text(cleaned, encoding="utf-8")
            deva = sum(1 for c in cleaned if 0x0900 <= ord(c) <= 0x097F)
            print(f"  [{model}] {page_stem} ok ({deva} deva chars)")
            ok += 1
        except Exception as e:
            print(f"  [{model}] {page_stem} ERROR: {e}", file=sys.stderr)
            out_path.write_text(f"ERROR: {e}", encoding="utf-8")
            errors += 1

        time.sleep(delay)

    return {"model": model, "processed": ok, "skipped": skipped, "errors": errors}


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="De-artifact OCR output with Grok and DeepSeek")
    ap.add_argument("--edition", type=str, help="Process only this edition (2001 or 1929)")
    ap.add_argument("--model", type=str, action="append", dest="models",
                    help="Use only this model (can repeat: --model grok --model deepseek)")
    ap.add_argument("--max", type=int, default=0, help="Max pages per model (0=all available)")
    ap.add_argument("--delay", type=float, default=0.5, help="Delay between API calls")
    ap.add_argument("--show-prompt", action="store_true", help="Show the system prompt")
    ap.add_argument("--merge-only", action="store_true",
                    help="Only run merge pass (requires pass2 outputs from both models)")
    ap.add_argument("--no-merge", action="store_true",
                    help="Skip the merge pass (only run model passes)")
    args = ap.parse_args()

    if args.show_prompt:
        print("=" * 72)
        print("SYSTEM PROMPT:")
        print("=" * 72)
        print(SYSTEM_PROMPT)
        print()
        print("USER MESSAGE TEMPLATE:")
        print(build_user_message("{RAW_OCR_TEXT}", "2001", "page-0000"))
        return

    models = args.models if args.models else ["grok", "deepseek"]
    editions = [args.edition] if args.edition else ["1929", "2001"]

    print(f"Editions: {editions}")
    print(f"Models: {models}")
    print(f"Max pages per model: {args.max if args.max else 'all available'}")

    all_stats = {}

    # Phase 1 & 2: De-artifact with each model independently
    if not args.merge_only:
        for edition in editions:
            print(f"\n{'='*60}")
            print(f"Edition: {edition}")
            for model in models:
                print(f"  [{model}] starting...")
                stats = process_model(edition, model, max_pages=args.max, delay=args.delay)
                all_stats[f"{edition}/{model}"] = stats

    # Phase 3: Merge best corrections from both models
    if not args.no_merge:
        for edition in editions:
            print(f"\n{'='*60}")
            print(f"Edition: {edition} — Merge pass")
            print(f"  [merge] starting...")
            stats = process_merge(edition, max_pages=args.max, delay=args.delay)
            all_stats[f"{edition}/merge"] = stats

    print(f"\n{'='*60}")
    for key, s in all_stats.items():
        print(f"  {key}: {s['processed']} processed, {s['skipped']} skipped, {s['errors']} errors")


if __name__ == "__main__":
    main()
