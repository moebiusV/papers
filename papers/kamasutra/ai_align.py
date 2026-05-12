#!/usr/bin/env python3
"""AI-powered chapter-level alignment using Grok and DeepSeek.

Replaces trigram-based matching with model-driven alignment that
understands Sanskrit text, recognizes commentary vs. root sutras,
and handles the three text streams draining at different rates.

Two passes:
  1. Sutra alignment (shared root text = anchors)
  2. Commentary alignment (1929 Jayamangala ↔ TITUS commentary)

Usage:
    python3 ai_align.py --model grok              # Grok only
    python3 ai_align.py --model grok --model deepseek  # both (compare)
    python3 ai_align.py --max-chapters 2          # first 2 chapters (test)
    python3 ai_align.py --show-prompt             # show the prompt
"""

import sys
import os
import time
import json
import re
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
WORK_DIR = BASE / "work"

# ── Prompt ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Sanskrit philologist aligning three editions of the Kama Sutra (Vatsyayana).

You are given:
1. TITUS sentences — numbered units from the TITUS digital edition (Devanagari)
2. 2001 OCR text — a printed edition with Hindi commentary
3. 1929 OCR text — a printed edition with Jayamangala Sanskrit commentary

## The three text streams

**TITUS**: A digital edition containing root sutras mixed with Sanskrit commentary
  (Jayamangala). Each sentence is numbered. The TITUS text is clean — no OCR noise.

**2001 edition**: OCR from a modern printed book. Contains root sutras (Sanskrit)
  interleaved with Hindi commentary. The Hindi commentary does NOT appear in TITUS.
  Line/page markers like [p42] show page boundaries.

**1929 edition**: OCR from an older printed book. Contains root sutras interleaved
  with Jayamangala Sanskrit commentary. BOTH root sutras and Sanskrit commentary
  match TITUS. Line/page markers like [p100] show page boundaries.

## The alignment problem

The three editions contain the same root sutras but in different order and with
different commentary interleaved. The OCR editions may have OCR artifacts
(misrecognized characters, spacing issues).

Your job: For each TITUS sentence, find the matching text in the 2001 and 1929
editions.

## Instructions

1. **Root sutras are your anchors.** They appear in all three editions. Find them first.
2. **Commentary text in the OCR editions will NOT match TITUS sentences** —
   recognize it as commentary and skip it. This is expected.
3. **2001 Hindi commentary** does not match TITUS at all — skip it.
4. **1929 Sanskrit commentary** DOES match TITUS — find those matches too.
5. **OCR artifacts** may cause minor character differences — use your Sanskrit
   knowledge to see through them.
6. **TITUS colophons** (chapter-end formulas like "iti śrīvātsyāyanīye...")
   may or may not match the printed editions — flag them as uncertain.
7. If a TITUS sentence genuinely does not appear in an edition, mark it as NOT FOUND.

## Output format

Respond with a JSON object ONLY (no markdown, no explanation):

{
  "alignments": {
    "1.1.1": {
      "titus": "the TITUS Devanagari text",
      "2001": "matching 2001 text or null",
      "1929": "matching 1929 text or null",
      "notes": "optional: all_agree | 1929_diverges | 2001_missing | commentary_only | etc."
    }
  }
}"""


def build_user_message(
    titus_sentences: list[dict],
    text_2001: str,
    text_1929: str,
    chapter_ref: str,
) -> str:
    """Build the user message for one chapter's alignment."""

    # TITUS sentences
    titus_lines = []
    for s in titus_sentences:
        ref = f"{s['book']}.{s['chapter']}.{s['sentence']}"
        titus_lines.append(f"{ref}: {s['deva']}")
    titus_block = "\n".join(titus_lines)

    return f"""## TITUS sentences — Chapter {chapter_ref}

{titus_block}

## 2001 edition OCR text

{text_2001 if text_2001 else '(no 2001 text available for this chapter)'}

## 1929 edition OCR text

{text_1929 if text_1929 else '(no 1929 text available for this chapter)'}"""


# ── OCR text loading ────────────────────────────────────────────────────────

def load_ocr_pages(edition: str, start_page: int, end_page: int,
                   deartifact_model: str = "grok") -> str:
    """Load concatenated OCR text from a page range.

    Uses de-artifacted text when available, falls back to raw OCR.
    Page markers like [p42] are inserted so the AI knows page boundaries.
    """
    pass2_dir = WORK_DIR / edition / "pass2" / deartifact_model
    pass1_dir = WORK_DIR / edition / "pass1"

    chunks = []
    for pg in range(start_page, end_page + 1):
        fname = f"page-{pg:04d}.txt"

        # Try de-artifacted first, then raw
        text = None
        for src_dir in [pass2_dir, pass1_dir]:
            pg_path = src_dir / fname
            if pg_path.exists():
                raw = pg_path.read_text(encoding="utf-8").strip()
                # Skip English summaries / refusals
                deva = sum(1 for c in raw if 0x0900 <= ord(c) <= 0x097F)
                if deva > 50:  # has actual Devanagari content
                    text = raw
                    break

        if text:
            chunks.append(f"[p{pg}] {text}")

    return "\n\n".join(chunks)


def load_chapter_titus(conn, book: int, chapter: int) -> list[dict]:
    """Load TITUS sentences for a chapter from the database."""
    rows = conn.execute("""
        SELECT book, chapter, sentence, titus_deva, titus_roman
        FROM sentences
        WHERE book = ? AND chapter = ?
        ORDER BY sentence
    """, (book, chapter)).fetchall()

    return [
        {
            "book": r[0],
            "chapter": r[1],
            "sentence": r[2],
            "deva": r[3] or "",
            "roman": r[4] or "",
        }
        for r in rows
    ]


# ── API clients ──────────────────────────────────────────────────────────────

def get_grok_client():
    from openai import OpenAI
    key_file = Path.home() / ".xai_api_key"
    if not key_file.exists():
        print("Error: ~/.xai_api_key not found", file=sys.stderr)
        sys.exit(1)
    return OpenAI(
        api_key=key_file.read_text().strip(),
        base_url="https://api.x.ai/v1",
    )


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
    return Anthropic(
        api_key=ds_key,
        base_url="https://api.deepseek.com/anthropic",
    )


def call_grok(client, system: str, user: str, model: str = "grok-3") -> str:
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def call_deepseek(client, system: str, user: str, model: str = "deepseek-v4-pro") -> str:
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[{"type": "text", "text": system}],
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


# ── Response parsing ─────────────────────────────────────────────────────────

def parse_alignment_response(content: str) -> dict:
    """Extract JSON alignment from model response."""
    # Find JSON object in response
    # Look for {"alignments": ...}
    json_match = re.search(r'\{[^{]*"alignments"\s*:\s*\{', content)
    if json_match:
        start = json_match.start()
        # Find matching closing brace
        depth = 0
        end = start
        for i, c in enumerate(content[start:], start):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        try:
            return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

    # Try to parse the whole response as JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Fallback: return raw content
    return {"error": "could not parse JSON", "raw": content}


# ── Chapter-level alignment ──────────────────────────────────────────────────

def align_chapter(
    client,
    model: str,
    call_fn,
    conn,
    book: int,
    chapter: int,
    page_hint_2001: int,
    page_hint_1929: int,
    pages_per_edition: int = 30,
) -> dict:
    """Align one chapter using AI. Returns parsed alignment result."""

    titus_sentences = load_chapter_titus(conn, book, chapter)
    if not titus_sentences:
        return {"error": f"no TITUS sentences for {book}.{chapter}"}

    # Load OCR text with generous page range
    text_2001 = load_ocr_pages("2001", page_hint_2001,
                                page_hint_2001 + pages_per_edition - 1)
    text_1929 = load_ocr_pages("1929", page_hint_1929,
                                page_hint_1929 + pages_per_edition - 1)

    chapter_ref = f"{book}.{chapter}"
    user_msg = build_user_message(titus_sentences, text_2001, text_1929, chapter_ref)

    response = call_fn(client, SYSTEM_PROMPT, user_msg)
    return parse_alignment_response(response)


# ── Main alignment loop ──────────────────────────────────────────────────────

def align_all(
    conn,
    model: str,
    max_chapters: int = 0,
    delay: float = 1.0,
) -> dict:
    """Walk forward through all chapters, aligning with AI.

    Uses page hints from previously aligned chapters to narrow the search.
    """

    # Get all chapters from TITUS
    chapters = conn.execute("""
        SELECT DISTINCT book, chapter FROM sentences
        ORDER BY book, chapter
    """).fetchall()

    if max_chapters:
        chapters = chapters[:max_chapters]

    # Initialize clients
    if model == "grok":
        client = get_grok_client()
        call_fn = call_grok
    elif model == "deepseek":
        client = get_deepseek_client()
        call_fn = call_deepseek
    else:
        raise ValueError(f"Unknown model: {model}")

    # Page hints start at 1 for each edition
    hint_2001 = 1
    hint_1929 = 1

    all_results = {}
    stats = {"aligned": 0, "not_found": 0, "errors": 0}

    for book, chapter in chapters:
        ref = f"{book}.{chapter}"
        print(f"[{model}] Chapter {ref}: ", end="", flush=True)

        try:
            result = align_chapter(
                client, model, call_fn, conn,
                book, chapter, hint_2001, hint_1929,
            )

            alignments = result.get("alignments", {})
            found = sum(1 for a in alignments.values()
                       if a.get("2001") or a.get("1929"))
            not_found = len(alignments) - found

            print(f"{found} found, {not_found} not found")

            # Update page hints based on last matched pages
            # (We'd refine this as we go — for now, just advance by
            #  estimated pages per chapter)
            titus_sentences = load_chapter_titus(conn, book, chapter)
            hint_2001 += len(titus_sentences) // 3 + 5  # rough estimate
            hint_1929 += len(titus_sentences) // 2 + 8

            all_results[ref] = result
            stats["aligned"] += found
            stats["not_found"] += not_found

        except Exception as e:
            print(f"ERROR: {e}")
            stats["errors"] += 1
            all_results[ref] = {"error": str(e)}

        time.sleep(delay)

    return {"results": all_results, "stats": stats}


# ── Save to DB ───────────────────────────────────────────────────────────────

def save_alignment(conn, chapter_ref: str, alignment: dict, model: str) -> int:
    """Save AI alignment results to the database. Returns rows updated."""
    parts = chapter_ref.split(".")
    book, chapter = int(parts[0]), int(parts[1])

    alignments = alignment.get("alignments", {})
    updated = 0

    for ref, data in alignments.items():
        # ref format: "book.chapter.sentence" (e.g., "1.1.1")
        sent_parts = ref.split(".")
        if len(sent_parts) != 3:
            continue
        sent = int(sent_parts[2])

        # Update the appropriate model columns
        if model == "grok":
            conn.execute("""
                UPDATE sentences SET text_2001_grok = ?, text_1929_grok = ?
                WHERE book = ? AND chapter = ? AND sentence = ?
            """, (data.get("2001"), data.get("1929"), book, chapter, sent))
        elif model == "deepseek":
            conn.execute("""
                UPDATE sentences SET text_2001_deepseek = ?, text_1929_deepseek = ?
                WHERE book = ? AND chapter = ? AND sentence = ?
            """, (data.get("2001"), data.get("1929"), book, chapter, sent))

        updated += 1

    conn.commit()
    return updated


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="AI-powered chapter alignment")
    ap.add_argument("--model", type=str, action="append", dest="models",
                    help="Model to use (repeat for multiple: --model grok --model deepseek)")
    ap.add_argument("--max-chapters", type=int, default=0,
                    help="Max chapters to align (0=all)")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="Delay between API calls")
    ap.add_argument("--show-prompt", action="store_true",
                    help="Show the system prompt and user template")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be aligned without API calls")
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
        print(build_user_message(
            [{"book": 1, "chapter": 1, "sentence": 1,
              "deva": "धर्मार्थकामेभ्यो नमः", "roman": "dharmārthakāmebhyo namaḥ"}],
            "[p1] धर्मार्थकामेभ्यो नमः ॥ ...",
            "[p1] धर्मार्थकामेभ्यो नमः ॥ ...",
            "1.1",
        ))
        return

    models = args.models if args.models else ["grok"]
    print(f"Models: {models}")

    sys.path.insert(0, str(BASE))
    from db import get_db
    conn = get_db()

    if args.dry_run:
        chapters = conn.execute("""
            SELECT DISTINCT book, chapter FROM sentences ORDER BY book, chapter
        """).fetchall()
        if args.max_chapters:
            chapters = chapters[:args.max_chapters]
        for book, chapter in chapters:
            sents = load_chapter_titus(conn, book, chapter)
            print(f"  {book}.{chapter}: {len(sents)} TITUS sentences")
        conn.close()
        return

    all_model_results = {}
    for model in models:
        print(f"\n{'='*60}")
        print(f"Aligning with {model}...")
        print(f"{'='*60}")
        result = align_all(conn, model, max_chapters=args.max_chapters,
                          delay=args.delay)
        all_model_results[model] = result

        # Save to DB
        print(f"\nSaving {model} results to DB...")
        total = 0
        for ref, alignment in result["results"].items():
            if "error" not in alignment:
                n = save_alignment(conn, ref, alignment, model)
                total += n
        print(f"  Updated {total} rows")

        s = result["stats"]
        print(f"  Stats: {s['aligned']} aligned, {s['not_found']} not found, "
              f"{s['errors']} errors")

    conn.close()

    # Summary
    print(f"\n{'='*60}")
    print("Alignment complete")
    for model, result in all_model_results.items():
        s = result["stats"]
        print(f"  {model}: {s['aligned']} aligned, {s['not_found']} not found, "
              f"{s['errors']} errors")


if __name__ == "__main__":
    main()
