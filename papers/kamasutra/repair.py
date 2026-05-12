#!/usr/bin/env python3
"""Discrepancy repair pass: three witnesses, model determines correct reading.

Default: DeepSeek primary (~free), Sonnet fallback on suspicious output.
Use --sonnet to force Sonnet for all repairs.

DeepSeek silently fabricated output during OCR (image-to-text censorship),
so we validate every repair: if DeepSeek's output has <40% Devanagari
characters, it's likely fabricated and we retry with Sonnet.

Reads from SQLite database, writes per-model repair columns for comparison.
Uses Anthropic prompt caching (cache_control on system message).
"""

import sys
import os
import time
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent
WORK_DIR = BASE / "work"

# Static part of the prompt — cached as a system message
SYSTEM_PROMPT = """You are a Sanskrit philologist resolving textual discrepancies in the Kama Sutra (Vatsyayana).

Three independent witnesses disagree on a passage. Determine the correct reading and explain your reasoning.

The 2001 and 1929 editions are OCR outputs from printed books — they will contain OCR artifacts (misrecognized characters, dropped or added marks, spacing irregularities). TITUS is a digital edition (Roman transliteration), not subject to OCR noise, but may contain its own editorial errors.

## Instructions

1. Compare all three readings. Note specific character-level differences.
2. Use Sanskrit grammar, meaning, and context to determine the most plausible reading.
3. TITUS is an independent witness, not ground truth — it may itself contain errors.
4. Always reason from Sanskrit grammar, meaning, and context — never default to "it's an OCR error" without explaining why the reading makes sense in context.
5. Common OCR error patterns to consider: ब/व confusion, स/श confusion, dropped anusvara, भ/म confusion — but always confirm against context.

Respond in this format:

CORRECTED: <the corrected Sanskrit text in Devanagari>
REASONING: <brief explanation of your reasoning>"""


def _build_user_message(titus: str, text_2001: str, text_1929: str, context: str) -> str:
    """Build the variable part of the repair prompt (not cached)."""
    ctx_lines = [f"BEFORE: {b}" for b in context.get("before", [])]
    ctx_lines.append(">>> DISPUTED <<<")
    ctx_lines.extend(f"AFTER: {a}" for a in context.get("after", []))
    ctx_str = "\n".join(ctx_lines) if ctx_lines else "(no surrounding context)"

    return f"""## Witnesses

**TITUS digital edition** (Roman transliteration with diacritics):
{titus or '(no TITUS reading)'}

**2001 printed edition OCR** (Devanagari, modern Hindi commentary edition):
{text_2001 or '(no reading from 2001 edition)'}

**1929 printed edition OCR** (Devanagari, Yashodhara's Jayamangala commentary):
{text_1929 or '(no reading from 1929 edition)'}

## Context (neighboring aligned sentences)

{ctx_str}"""


def _parse_response(content: str) -> tuple[str, str]:
    """Extract CORRECTED and REASONING from model response."""
    corrected = ""
    reasoning = ""
    for line in content.split("\n"):
        if line.startswith("CORRECTED:"):
            corrected = line[len("CORRECTED:"):].strip()
        elif line.startswith("REASONING:"):
            reasoning = line[len("REASONING:"):].strip()
        elif reasoning:
            reasoning += " " + line.strip()
    if not corrected:
        corrected = content
    return corrected, reasoning


def _deva_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are Devanagari (U+0900–U+097F)."""
    if not text:
        return 0.0
    deva = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
    alpha = sum(1 for c in text if c.isalpha() or 0x0900 <= ord(c) <= 0x097F)
    return deva / max(alpha, 1)


def repair_one(
    client,
    model: str,
    system_prompt: str,
    user_message: str,
    use_caching: bool = True,
) -> tuple[str, str]:
    """Send a repair request. Returns (corrected, reasoning).

    When use_caching=True, the system prompt is sent with cache_control
    so Anthropic caches it across calls (massive cost savings for batch work).
    """
    system_block = {"type": "text", "text": system_prompt}
    if use_caching:
        system_block["cache_control"] = {"type": "ephemeral"}

    response = client.messages.create(
        model=model,
        max_tokens=512,
        system=[system_block],
        messages=[{"role": "user", "content": user_message}],
    )
    content = response.content[0].text
    return _parse_response(content)


# ── Database-backed repair ───────────────────────────────────────────────────

def get_repair_rows(conn, model: str = "deepseek") -> list[dict]:
    """Fetch rows needing repair from the database."""
    if model == "deepseek":
        view = "needs_repair_deepseek"
    elif model == "sonnet":
        view = "needs_repair_sonnet"
    else:
        view = "needs_repair_deepseek"

    rows = conn.execute(f"""
        SELECT id, book, chapter, sentence, titus_roman,
               text_2001_raw, text_1929_raw, flags, confidence
        FROM {view}
        ORDER BY book, chapter, sentence
    """).fetchall()

    return [
        {
            "id": r[0],
            "book": r[1],
            "chapter": r[2],
            "sentence": r[3],
            "titus_roman": r[4],
            "text_2001": r[5],
            "text_1929": r[6],
            "flags": r[7],
            "confidence": r[8],
        }
        for r in rows
    ]


def get_context(conn, book: int, chapter: int, sentence: int, window: int = 3) -> dict:
    """Get neighboring TITUS sentences for context."""
    before = [
        r[0] for r in conn.execute("""
            SELECT titus_roman FROM sentences
            WHERE book = ? AND chapter = ? AND sentence < ?
            ORDER BY sentence DESC LIMIT ?
        """, (book, chapter, sentence, window)).fetchall()
    ][::-1]

    after = [
        r[0] for r in conn.execute("""
            SELECT titus_roman FROM sentences
            WHERE book = ? AND chapter = ? AND sentence > ?
            ORDER BY sentence ASC LIMIT ?
        """, (book, chapter, sentence, window)).fetchall()
    ]

    return {"before": before, "after": after}


def save_repair(conn, row_id: int, model: str, corrected: str, reasoning: str) -> None:
    """Write a single repair result back to the database."""
    col_deva = f"repair_{model}"
    col_reason = f"repair_{model}_reason"
    # Validate column names to prevent injection
    allowed = {"deepseek", "sonnet", "opus"}
    if model not in allowed:
        raise ValueError(f"Invalid model: {model}")

    conn.execute(
        f"UPDATE sentences SET {col_deva} = ?, {col_reason} = ? WHERE id = ?",
        (corrected, reasoning, row_id),
    )
    conn.commit()


def repair_all(
    conn,
    client_ds,       # DeepSeek client (or None)
    client_anth,     # Anthropic client
    model_ds: str,
    model_fallback: str,
    delay: float = 0.5,
    max_repairs: int = 0,
    start: int = 0,
    force_fallback: bool = False,
) -> dict:
    """Run repair on flagged rows with censorship-aware fallback.

    Returns counts of rows repaired by each model.
    """
    rows = get_repair_rows(conn, "deepseek")
    total = len(rows)
    if max_repairs:
        total = min(max_repairs, total)
    if start:
        rows = rows[start:]

    batch = rows[:total]
    counts = {"deepseek": 0, "sonnet": 0, "opus": 0, "errors": 0}

    for i, row in enumerate(batch):
        ref = f"{row['book']}.{row['chapter']}.{row['sentence']}"
        flags = row["flags"] or ""
        print(f"[repair {i+1}/{len(batch)}] {ref} flags={flags}", end=" ")

        ctx = get_context(conn, row["book"], row["chapter"], row["sentence"])
        user_msg = _build_user_message(
            row["titus_roman"], row["text_2001"], row["text_1929"], ctx,
        )

        model_used = model_fallback if force_fallback else model_ds
        client = client_anth if force_fallback else client_ds
        caching = not force_fallback  # DeepSeek may not support caching

        try:
            corrected, reasoning = repair_one(
                client, model_used, SYSTEM_PROMPT, user_msg, use_caching=caching,
            )

            # Validate: if DeepSeek output is suspicious, retry with fallback
            if not force_fallback and client_ds is not None and model_used == model_ds:
                dr = _deva_ratio(corrected)
                if dr < 0.4:
                    print(f"[deva_ratio={dr:.2f} -> fallback] ", end="")
                    corrected, reasoning = repair_one(
                        client_anth, model_fallback, SYSTEM_PROMPT, user_msg,
                        use_caching=True,
                    )
                    model_used = model_fallback
                    counts[model_fallback] = counts.get(model_fallback, 0) + 1
                else:
                    counts[model_used] = counts.get(model_used, 0) + 1
            else:
                counts[model_used] = counts.get(model_used, 0) + 1

            save_repair(conn, row["id"], "deepseek", corrected, reasoning)
            print(f"[{model_used}] {corrected[:80]}...")
        except Exception as e:
            print(f"ERROR: {e}")
            # Try fallback if primary failed
            if not force_fallback and client_ds is not None:
                try:
                    print(f"  retrying with fallback...")
                    corrected, reasoning = repair_one(
                        client_anth, model_fallback, SYSTEM_PROMPT, user_msg,
                        use_caching=True,
                    )
                    save_repair(conn, row["id"], "deepseek", corrected, reasoning)
                    counts[model_fallback] = counts.get(model_fallback, 0) + 1
                except Exception as e2:
                    print(f"  fallback also failed: {e2}")
                    counts["errors"] += 1
            else:
                counts["errors"] += 1

        time.sleep(delay)

    print(f"\nModel usage: DeepSeek={counts.get('deepseek', 0)}, "
          f"{model_fallback}={counts.get(model_fallback, 0)}, "
          f"errors={counts.get('errors', 0)}")
    return counts


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Repair OCR discrepancies")
    ap.add_argument("--max", type=int, default=0, help="Max repairs (0=all)")
    ap.add_argument("--start", type=int, default=0, help="Start from row index")
    ap.add_argument("--delay", type=float, default=0.5, help="Delay between calls")
    ap.add_argument("--sonnet", action="store_true", help="Use Sonnet for all repairs")
    ap.add_argument("--opus", action="store_true", help="Use Opus for all repairs")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be repaired")
    ap.add_argument("--show-prompt", action="store_true", help="Show the cached system prompt")
    args = ap.parse_args()

    if args.show_prompt:
        print("=" * 72)
        print("CACHED SYSTEM PROMPT (static, cached across all repair calls):")
        print("=" * 72)
        print(SYSTEM_PROMPT)
        print()
        print("=" * 72)
        print("USER MESSAGE TEMPLATE (variable per sentence, NOT cached):")
        print("=" * 72)
        print(_build_user_message(
            "{TITUS_ROMAN}", "{TEXT_2001}", "{TEXT_1929}",
            {"before": ["{BEFORE_1}", "{BEFORE_2}"], "after": ["{AFTER_1}", "{AFTER_2}"]},
        ))
        return

    # Import DB module
    sys.path.insert(0, str(BASE))
    from db import get_db, summary

    conn = get_db()

    repair_rows = conn.execute(
        "SELECT COUNT(*) FROM needs_repair_deepseek"
    ).fetchone()[0]

    print(f"Rows needing repair: {repair_rows}")

    if args.dry_run:
        rows = get_repair_rows(conn, "deepseek")
        print(f"\nFirst 5 flagged rows:")
        for r in rows[:5]:
            ref = f"{r['book']}.{r['chapter']}.{r['sentence']}"
            print(f"  [{ref}] flags={r['flags']}")
            print(f"    TITUS: {(r['titus_roman'] or '')[:120]}")
            print(f"    2001:  {(r['text_2001'] or '')[:120]}")
            print(f"    1929:  {(r['text_1929'] or '')[:120]}")
        conn.close()
        return

    # Build clients
    import anthropic
    from process import make_client

    client_anth = make_client(use_anthropic=True)

    if args.opus:
        model_fallback = "claude-opus-4-7"
        force_fallback = True
        client_ds = None
        model_ds = ""
    elif args.sonnet:
        model_fallback = "claude-sonnet-4-6"
        force_fallback = True
        client_ds = None
        model_ds = ""
    else:
        model_fallback = "claude-sonnet-4-6"
        force_fallback = False
        ds_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        if not ds_key:
            key_file = Path.home() / ".anthropic_api_key"
            if key_file.exists():
                ds_key = key_file.read_text().strip()
        client_ds = anthropic.Anthropic(
            api_key=ds_key,
            base_url="https://api.deepseek.com/anthropic",
        )
        model_ds = "deepseek-v4-pro"

    total = min(args.max, repair_rows) if args.max else repair_rows

    print(f"Repairing {total} rows (start={args.start})")
    print(f"Primary: {model_ds or 'none'}, Fallback: {model_fallback}")
    print(f"Prompt caching: {'enabled' if not args.sonnet and not args.opus else 'sonnet/opus — caching active'}")
    print()

    counts = repair_all(
        conn, client_ds, client_anth,
        model_ds, model_fallback,
        delay=args.delay,
        max_repairs=total,
        start=args.start,
        force_fallback=force_fallback,
    )

    s = summary(conn)
    print(f"\nDatabase state:")
    print(f"  Repaired (DeepSeek): {s['repaired_ds']}")
    print(f"  Needs repair (DeepSeek): {s['needs_repair_ds']}")

    conn.close()


if __name__ == "__main__":
    main()
