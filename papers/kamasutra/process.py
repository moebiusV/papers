#!/usr/bin/env python3
"""
Multi-edition OCR and translation pipeline for the Kama Sutra.

Two source PDFs:
  - kama-sutra-2001.pdf (248 pages, primary — has a torn/distorted line mid-page)
  - kama-sutra-1929.pdf (353 pages, older printing — used for cross-verification)

Pipeline:
  Pass 1 (ocr):       page image → Devanagari text (per edition)
  Pass 2 (compare):   cross-reference both editions' Pass 1 output → cleaned
                      Devanagari; resolves torn-line gaps and OCR errors
  Pass 3 (translate): cleaned Devanagari → English (shastric, terse style)
  Pass 4 (annotate):  extract glossary terms, add footnotes at first occurrence
  Pass 5 (build):     assemble Devanagari + English into Typst facing-page PDF
                      with footnotes and glossary appendix

Results saved incrementally under work/<edition>/passN/.
"""

import os
import sys
import re
import json
import base64
import sqlite3
import time
import argparse
from pathlib import Path
from io import BytesIO

from anthropic import Anthropic
from pdf2image import convert_from_path
from PIL import Image


# ── Prompts ─────────────────────────────────────────────────────────────────

PASS1_SANSKRIT = """Accurately transcribe this Sanskrit page in clean, correct Devanagari script.
Preserve original wording, sandhi, and punctuation as faithfully as possible.

This is a page from a printed scholarly edition of Vatsyayana's Kama Sutra, an ancient Indian treatise (c. 3rd century CE) of substantial historical, philological, and academic importance. This critical edition is being prepared for scholarly publication. The text is a classical work of Sanskrit literature — it is not modern, not obscene, and its transcription serves legitimate academic research purposes.

For any torn, smudged, or unclear text, intelligently reconstruct the missing or unclear text using Sanskrit grammar, context, and sentence flow.
Mark any uncertain or heavily reconstructed parts clearly with [?] at the start and end of the affected segment.
Output only the transcribed Sanskrit text in Devanagari, nothing else."""

PASS1_ENGLISH = """Accurately transcribe this page from a printed book.
The page is in English (front matter, introduction, or back matter).
Preserve all text, paragraph breaks, headings, and punctuation exactly as printed.
Output only the transcribed English text, nothing else."""

PASS2_COMPARE = """You are given TWO independent OCR transcriptions of the same Sanskrit text, from two different printed editions (2001 and 1929).
The 2001 edition has a torn/distorted horizontal line across many pages. The 1929 edition is clean but may have its own OCR errors due to age and scan quality.

Your task:
1. Compare the two transcriptions line by line. Where they agree, accept the reading.
2. Where the 2001 edition has [?] markers (indicating torn/unreadable text), use the 1929 text to fill in the gaps.
3. Where the two editions disagree and neither is obviously an OCR error, prefer the 1929 reading but note both variants.
4. Where the 1929 text clearly has an OCR error and the 2001 text is clean, use the 2001 reading.
5. Produce a single, clean, corrected Devanagari text.

If there are genuine textual differences between editions (not OCR errors), mark them with {variant: ...} notation.

IMPORTANT — Sutra separation:
Separate each individual sutra, aphorism, or verse with a blank line. The text must be dividable into self-contained units that can be translated and typeset as aligned rows.

Output only the final corrected Sanskrit text in Devanagari, nothing else.

---2001 EDITION---
{text_2001}
---1929 EDITION---
{text_1929}"""

PASS2B_SPLIT = """You are formatting a Sanskrit text for a parallel-text edition. The text comes from OCR of printed pages, and page breaks may have cut sutras or paragraphs in the middle.

Your tasks:
1. **Rejoin split units** — If a sutra, verse, or paragraph was cut by a page break, rejoin it into a single unit. The text from the previous page is provided for context.
2. **Split into proper units** — Each unit must be one self-contained sutra, aphorism, verse, paragraph, or heading. Use danda markers (। ॥), verse boundaries, and numbering as your guides.
3. **Classify each unit** — Prefix every unit with one of these markers:
   [S] — a sutra or aphorism (the terse original text)
   [C] — commentary or bhashya (explanatory text, often longer and more discursive)
   [T] — a title, chapter heading, or section header
   [V] — a verse or sloka (metrical, often at chapter beginnings/endings)
   [P] — a prose paragraph that is neither sutra nor commentary (e.g., colophon, introduction)
4. **Preserve all text** — Do not edit or correct the Sanskrit. Only fix the boundaries and add markers.

Each unit should typically be 1-5 lines. Separate each unit with a single blank line.

Output only the formatted text with blank lines between units, nothing else.

---PREVIOUS PAGE END (for context)---
{prev_text}

---CURRENT PAGE---
{text}"""

PASS3_PROMPT = """Translate this Sanskrit text into English. It is from Vatsyayana's Kama Sutra.

The original style is:
- Systematic, shastric, pedantic — like a technical manual, not poetry
- Terse and dense — the Sanskrit is famously compact; the English should be tight and economical
- Scholarly and analytical — dry, precise, observational, not emotional
- Classificatory — the author loves lists, categories, and taxonomies
- NOT flowery, NOT breezy, NOT wordy — closer to a legal or scientific treatise than to love poetry

IMPORTANT — Proper nouns and untranslatable terms:
- Geographical names (places, regions, rivers, mountains), ethnic/tribal names, and technical Sanskrit terms should be LEFT UNTRANSLATED in their standard Roman transliteration. Do NOT replace them with modern equivalents.
- Examples: keep "Lata" not "Gujarat", "Sindh" not "Punjab", "Anga" not "Bengal", "Vatsya" not "Vatsyayana".
- These terms will be explained in a glossary.

CRITICAL — Output format:
The input text is divided into separate units (sutras, aphorisms, paragraphs) separated by blank lines.
Preserve this exact structure in your output. Each input unit must become exactly one output unit, separated by a blank line.
Do NOT merge units together. Do NOT split a unit into multiple units.
The row alignment across languages depends on matching unit counts.

Translate accordingly: keep it tight, precise, and methodical. Do not expand or embellish.
Output only the English translation, with blank-line-separated units, nothing else."""

PASS3_HEBREW = """Translate this Sanskrit text into Hebrew. It is from Vatsyayana's Kama Sutra.

The original is a shastra — a systematic, technical treatise. It is terse, aphoristic, and densely classified, like a legal or scientific manual.

Your Hebrew should match this register. Do NOT use conversational Modern Israeli Hebrew. Instead, use the kind of Hebrew an old rabbi or yeshiva student would deploy when studying a halakhic or philosophical text — Mishnaic in texture, with some Aramaicisms, compact syntax, and a scholarly gravity. Think Mishnah / Rambam / mesekhta prose, not street Hebrew, not newspaper Hebrew, not modern academic Hebrew.

That said: it should be readable by a modern Israeli without trouble. They might find it archaic, elevated, yeshivish — but they should not struggle to parse it. It's the Hebrew of a rav teaching his talmidim in 2026, rooted in Mishnaic patterns but alive and natural for our time. Not a tanna cosplay, not a responsum for the 12th century. The cadence of somebody who learns Gemara and Rambam daily — but is explaining to students now.

Specific guidance:
- Short, punchy clauses; paratactic over hypotactic
- Rabbinic constructions where natural (של, כינויי קניין, משקלים ארמיים קלים)
- Light Aramaicisms for precision and weight (דהיינו, כלשון, איכא, ליתא, מילתא — but don't overdo it)
- Lists and classifications should feel like a משנה — numbered, crisp, dry
- Detached, analytical tone; never emotional, never poetic
- No street Hebrew, no newspaper Hebrew, no faux-Biblical grandiosity

IMPORTANT — Proper nouns:
- Geographical names, ethnic/tribal names, and technical Sanskrit terms should be LEFT UNTRANSLATED in their standard Roman transliteration.
- Do NOT Hebraicize them. Keep "Lata", "Sindh", "Anga" as-is.

CRITICAL — Output format:
The input text is divided into separate units (sutras, aphorisms, paragraphs) separated by blank lines.
Preserve this exact structure in your output. Each input unit must become exactly one output unit, separated by a blank line.
Do NOT merge units together. Do NOT split a unit into multiple units.
The row alignment across languages depends on matching unit counts.

Translate accordingly: tight, precise, methodical, scholarly. Do not expand or embellish.
Output only the Hebrew translation, with blank-line-separated units, nothing else."""

PASS35_GLOSSARY = """You are building a glossary for an English translation of Vatsyayana's Kama Sutra.

Below is the complete English translation. Identify ALL geographical place names, ethnic/tribal group names, and technical Sanskrit terms that were left untranslated.

For each term:
1. The term as it appears in the text (Roman transliteration)
2. The modern geographical equivalent or English definition (1-2 sentences)
3. The category: "place" (geographical), "people" (ethnic/tribal), or "term" (technical Sanskrit concept)

Focus especially on:
- Place names: ancient Indian regions, cities, rivers, mountains (e.g., Lata, Sindh, Anga, Vanga, Kalinga, Videha, Pataliputra, Ganges/Yamuna, Himalaya/Vindhya)
- Ethnic/tribal names: groups of people (e.g., Abhira, Andhra, Dravida)
- Technical terms that are central to the text and hard to translate (e.g., dharma, artha, kama, veshya, nayaka/nayika, samprayoga)

Output ONLY valid JSON as a list of objects:
[{"term": "Lata", "definition": "Ancient region corresponding to modern southern Gujarat and northern Maharashtra.", "category": "place"}, ...]

Do NOT include common Sanskrit words that have obvious English equivalents. Focus on terms a modern reader would need explained.

---TEXT---
{full_text}"""


# ── Paths ───────────────────────────────────────────────────────────────────

def work_dir(base: Path, edition: str, pass_name: str) -> Path:
    d = base / "work" / edition / pass_name
    d.mkdir(parents=True, exist_ok=True)
    return d

def page_file(workdir: Path, page_num: int) -> Path:
    return workdir / f"page-{page_num:04d}.txt"


# ── PDF utilities ───────────────────────────────────────────────────────────

def pdf_page_count(pdf_path: Path) -> int:
    from pdf2image.pdf2image import pdfinfo_from_path
    return pdfinfo_from_path(str(pdf_path))["Pages"]

def pdf_page_to_image(pdf_path: Path, page_num: int, dpi: int = 300) -> Image.Image:
    images = convert_from_path(
        pdf_path, dpi=dpi, first_page=page_num, last_page=page_num
    )
    return images[0]

MAX_IMAGE_BYTES = 4_500_000  # Anthropic limit is 5MB, leave headroom

def image_to_base64(img: Image.Image, max_bytes: int = MAX_IMAGE_BYTES) -> tuple[str, str]:
    """Encode image as base64, downscaling iteratively if needed.

    Returns (base64_data, media_type) — e.g. ('iVBOR...', 'image/png').
    """
    for _ in range(10):
        buf = BytesIO()
        img.save(buf, format="PNG", compress_level=9)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        if len(encoded) <= max_bytes:
            return encoded, "image/png"
        ratio = 0.8
        new_w = max(int(img.width * ratio), 400)
        new_h = max(int(img.height * ratio), 300)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    # If even 400px wide PNG at max compression exceeds the limit, something
    # is wrong — return it anyway and let the API reject it.
    buf = BytesIO()
    img.save(buf, format="PNG", compress_level=9)
    return base64.b64encode(buf.getvalue()).decode("ascii"), "image/png"


# ── API client ──────────────────────────────────────────────────────────────

def make_client(use_anthropic: bool = False) -> Anthropic:
    if use_anthropic:
        key_file = Path.home() / ".anthropic_api_key"
        if not key_file.exists():
            print("Error: --anthropic set but ~/.anthropic_api_key not found", file=sys.stderr)
            sys.exit(1)
        api_key = key_file.read_text().strip()
        base_url = "https://api.anthropic.com"
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        if not api_key:
            print("Error: set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN", file=sys.stderr)
            sys.exit(1)
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    return Anthropic(api_key=api_key, base_url=base_url)


# ── API calls ───────────────────────────────────────────────────────────────

def call_vision(client: Anthropic, model: str, image_b64: str, prompt: str, media_type: str = "image/png") -> str:
    msg = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return msg.content[0].text


def call_text(client: Anthropic, model: str, prompt: str) -> str:
    """Send a text-only message and return the response."""
    msg = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── Pass 1: OCR ─────────────────────────────────────────────────────────────

def pass1_page(
    client: Anthropic,
    model: str,
    pdf_path: Path,
    page_num: int,
    total: int,
    out_dir: Path,
    english: bool,
    resume: bool,
    delay: float,
) -> bool:
    pfx = f"[P1:{pdf_path.stem}:{page_num}/{total}]"
    out_file = page_file(out_dir, page_num)

    if resume and out_file.exists():
        print(f"{pfx} already done, skipping")
        return True

    prompt = PASS1_ENGLISH if english else PASS1_SANSKRIT
    label = "OCR-en" if english else "OCR-deva"
    print(f"{pfx} converting to image...")
    img = pdf_page_to_image(pdf_path, page_num)
    b64, media_type = image_to_base64(img)
    print(f"{pfx} {label} ({len(b64)//1000} KB, {media_type})...")

    try:
        text = call_vision(client, model, b64, prompt, media_type)
        out_file.write_text(text, encoding="utf-8")
        print(f"{pfx} saved ({len(text)} chars)")
        return True
    except Exception as e:
        print(f"{pfx} ERROR — {e}", file=sys.stderr)
        return False


def run_pass1(
    client: Anthropic,
    model: str,
    pdf_path: Path,
    start: int,
    end: int,
    english_pages: set,
    resume: bool,
    delay: float,
    base_dir: Path,
):
    _stem = pdf_path.stem
    _parts = _stem.rsplit("-", 1)
    edition = _parts[1] if len(_parts) == 2 and _parts[1].isdigit() else _stem
    out_dir = work_dir(base_dir, edition, "pass1")
    total = pdf_page_count(pdf_path)
    end = min(end, total)

    print(f"Pass 1 (OCR): {pdf_path.name} — pages {start}–{end}/{total}")
    ok, fail = 0, 0
    for pn in range(start, end + 1):
        english = pn in english_pages
        if pass1_page(client, model, pdf_path, pn, total, out_dir, english, resume, delay):
            ok += 1
        else:
            fail += 1
    print(f"Pass 1 done — {ok} ok, {fail} failed\n")
    return out_dir


# ── Pass 2: Cross-reference comparison ──────────────────────────────────────

def run_pass2(
    client: Anthropic,
    model: str,
    primary_edition: str,
    secondary_edition: str,
    start: int,
    end: int,
    resume: bool,
    delay: float,
    base_dir: Path,
):
    """Compare Pass 1 outputs from two editions and produce cleaned Devanagari.

    The primary edition (2001) drives the page numbering. For each primary page,
    we send both the primary and secondary Pass 1 text to the model for
    cross-referencing and gap-filling.

    Since editions don't have matching page numbers, we rely on the model's
    ability to align the texts by content. A better approach for production
    would be to first concatenate both full texts, align them globally, then
    split back into the primary's page structure.
    """
    p1_primary = work_dir(base_dir, primary_edition, "pass1")
    p1_secondary = work_dir(base_dir, secondary_edition, "pass1")
    out_dir = work_dir(base_dir, primary_edition, "pass2")

    # Count available primary pages
    primary_pages = sorted([
        int(f.stem.split("-")[1]) for f in p1_primary.glob("page-*.txt")
    ])
    if not primary_pages:
        print("Pass 2: no Pass 1 output found for primary edition. Run Pass 1 first.")
        return

    total = max(primary_pages)
    end = min(end, total)

    # Load all secondary text as a single reference corpus
    secondary_text = ""
    secondary_pages = sorted(p1_secondary.glob("page-*.txt"))
    for sp in secondary_pages:
        secondary_text += sp.read_text(encoding="utf-8") + "\n"

    print(f"Pass 2 (compare): {primary_edition} ← {secondary_edition} — pages {start}–{end}")
    ok, fail = 0, 0

    for pn in range(start, end + 1):
        pfx = f"[P2:{pn}/{end}]"
        out_file = page_file(out_dir, pn)

        if resume and out_file.exists():
            print(f"{pfx} already done, skipping")
            ok += 1
            continue

        primary_file = page_file(p1_primary, pn)
        if not primary_file.exists():
            print(f"{pfx} no primary text for page {pn}, skipping")
            continue

        text_2001 = primary_file.read_text(encoding="utf-8")

        # For the comparison prompt, send the primary page text plus a chunk
        # of secondary text (~neighboring pages, since editions don't align 1:1)
        # The model will find the matching content.
        prompt = PASS2_COMPARE.format(
            text_2001=text_2001,
            text_1929=secondary_text,
        )

        print(f"{pfx} comparing ({len(text_2001)} primary + {len(secondary_text)} secondary chars)...")
        try:
            result = call_text(client, model, prompt)
            out_file.write_text(result, encoding="utf-8")
            print(f"{pfx} saved ({len(result)} chars)")
            ok += 1
        except Exception as e:
            print(f"{pfx} ERROR — {e}", file=sys.stderr)
            fail += 1
        time.sleep(delay)

    print(f"Pass 2 done — {ok} ok, {fail} failed\n")

    # Auto-run sutra splitting on comparison output
    out_dir = run_pass2b(client, model, out_dir, primary_edition, start, end, resume, delay, base_dir)
    return out_dir


# ── Pass 2b: Sutra splitting ─────────────────────────────────────────────────

def run_pass2b(
    client: Anthropic,
    model: str,
    p2_dir: Path,
    edition: str,
    start: int,
    end: int,
    resume: bool,
    delay: float,
    base_dir: Path,
):
    """Split cleaned Devanagari into sutras, handling cross-page joins.

    Phase 1: Per-page splitting with previous-page context for rejoining.
    Phase 2: Concatenate all pages, deduplicate rejoined sutras at boundaries,
             assign global numbering, write individual sutra files.
    """
    split_dir = work_dir(base_dir, edition, "pass2-split")
    sutras_dir = work_dir(base_dir, edition, "sutras")

    pages = sorted([int(f.stem.split("-")[1]) for f in p2_dir.glob("page-*.txt")])
    if not pages:
        return sutras_dir

    total = max(pages)
    end = min(end, total)

    # ── Phase 1: Per-page splitting ──────────────────────────────────────
    print(f"Pass 2b (format-check + sutra-split): {edition} — pages {start}–{end}")
    ok, fail = 0, 0

    for i, pn in enumerate(range(start, end + 1)):
        pfx = f"[P2b:{pn}/{end}]"
        out_file = page_file(split_dir, pn)

        if resume and out_file.exists():
            existing = out_file.read_text(encoding="utf-8")
            units = [u for u in existing.split("\n\n") if u.strip()]
            print(f"{pfx} already done ({len(units)} units), skipping")
            ok += 1
            continue

        source_file = page_file(p2_dir, pn)
        if not source_file.exists():
            continue

        source_text = source_file.read_text(encoding="utf-8")

        # Get last ~500 chars of previous page for cross-page context
        prev_text = ""
        prev_page = pn - 1
        if prev_page >= start:
            prev_file = page_file(p2_dir, prev_page)
            if prev_file.exists():
                prev_full = prev_file.read_text(encoding="utf-8")
                prev_text = prev_full[-500:] if len(prev_full) > 500 else prev_full

        prompt = PASS2B_SPLIT.format(text=source_text, prev_text=prev_text or "(none — this is the first page)")
        print(f"{pfx} splitting ({len(source_text)} chars)...")

        try:
            result = call_text(client, model, prompt)
            out_file.write_text(result, encoding="utf-8")
            units = [u for u in result.split("\n\n") if u.strip()]
            print(f"{pfx} saved ({len(units)} units)")
            ok += 1
        except Exception as e:
            print(f"{pfx} ERROR — {e}", file=sys.stderr)
            out_file.write_text(source_text, encoding="utf-8")
            fail += 1
        time.sleep(delay)

    print(f"Pass 2b split done — {ok} ok, {fail} failed")

    # ── Phase 2: Concatenate + deduplicate + number ──────────────────────
    print("Pass 2b: assembling global sutra sequence...")
    all_units = []
    prev_last = ""

    for pn in range(start, end + 1):
        sf = page_file(split_dir, pn)
        if not sf.exists():
            continue
        text = sf.read_text(encoding="utf-8")
        units = [u.strip() for u in text.split("\n\n") if u.strip()]
        if not units:
            continue

        # Check if first unit of this page is a continuation/rejoin
        # of the last unit from the previous page. Simple heuristic:
        # if the first unit is very similar to the previous page's last,
        # skip it (it was the rejoined version).
        if prev_last and units:
            # Compare first 100 chars
            first_start = units[0][:100]
            prev_start = prev_last[:100]
            if first_start == prev_start:
                # This unit was the rejoined one; skip it
                units = units[1:]
            elif len(units[0]) > len(prev_last) * 1.5 and prev_start in units[0]:
                # The first unit on this page is an expanded version of prev_last
                # (rejoined with its continuation). Replace prev_last.
                if all_units:
                    all_units[-1] = units[0]
                units = units[1:]

        prev_last = units[-1] if units else prev_last
        all_units.extend(units)

    # Write individual sutra files
    # Clear existing sutras
    for old in sutras_dir.glob("sutra-*.txt"):
        old.unlink()

    for idx, unit in enumerate(all_units, 1):
        sf = sutras_dir / f"sutra-{idx:05d}.txt"
        sf.write_text(unit, encoding="utf-8")

    print(f"Pass 2b done — {len(all_units)} sutras written to {sutras_dir}")

    # Populate the SQLite database
    db_file = db_path(base_dir, edition)
    db_populate_from_sutras(db_file, sutras_dir)
    print(f"  DB populated: {db_file}\n")
    return sutras_dir


# ── Pass 3: Translation ─────────────────────────────────────────────────────

def run_pass3(
    client: Anthropic,
    model: str,
    edition: str,
    start: int,
    end: int,
    resume: bool,
    delay: float,
    base_dir: Path,
    languages: str = "en",
):
    """Translate individual sutras (from Pass 2b) to target language(s).

    Uses prompt caching: the translation instructions are cached server-side,
    so each sutra call only charges for the sutra text + output tokens.

    languages: comma-separated — 'en', 'he', or 'en,he'
    """
    sutras_dir = work_dir(base_dir, edition, "sutras")

    sutra_files = sorted(sutras_dir.glob("sutra-*.txt"))
    if not sutra_files:
        # Fall back to page-level Pass 2 output
        p2_dir = work_dir(base_dir, edition, "pass2-split")
        page_files = sorted(p2_dir.glob("page-*.txt"))
        if not page_files:
            print("Pass 3: no sutras or split pages found. Run Pass 2 first.")
            return work_dir(base_dir, edition, "pass3")
        # Translate from page-level split files
        return _run_pass3_pages(
            client, model, edition, start, end, resume, delay, base_dir, languages
        )

    total = len(sutra_files)

    langs = [l.strip() for l in languages.split(",")]

    for lang in langs:
        if lang == "en":
            system_prompt = PASS3_PROMPT
            suffix = "pass3"
            label = "English"
        elif lang == "he":
            system_prompt = PASS3_HEBREW
            suffix = "pass3-he"
            label = "Hebrew"
        else:
            print(f"Pass 3: unknown language '{lang}', skipping")
            continue

        out_dir = work_dir(base_dir, edition, suffix)
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"Pass 3 (translate-{label}): {edition} — {total} sutras (prompt-cached)")

        # Cached system prompt — the translation instructions stay the same
        system = [{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }]

        ok, fail = 0, 0

        for sf in sutra_files:
            sutra_id = sf.stem  # e.g., "sutra-00001"
            out_file = out_dir / f"{sutra_id}.txt"

            if resume and out_file.exists():
                ok += 1
                continue

            sutra_text = sf.read_text(encoding="utf-8")
            pfx = f"[P3-{lang}:{sutra_id}]"

            try:
                msg = client.messages.create(
                    model=model,
                    max_tokens=2048,
                    system=system,
                    messages=[{
                        "role": "user",
                        "content": sutra_text,
                    }],
                )
                result = msg.content[0].text
                out_file.write_text(result, encoding="utf-8")
                ok += 1
                if ok % 50 == 0:
                    print(f"{pfx} {ok}/{total} done")
            except Exception as e:
                print(f"{pfx} ERROR — {e}", file=sys.stderr)
                fail += 1
            time.sleep(delay)

        # Update DB with translations
        db_file = db_path(base_dir, edition)
        if db_file.exists():
            n = db_update_translations(db_file, lang, out_dir)
            print(f"  DB updated: {n} rows ({label})")

        print(f"Pass 3 ({label}) done — {ok} ok, {fail} failed\n")

    return work_dir(base_dir, edition, "pass3")


def _run_pass3_pages(
    client, model, edition, start, end, resume, delay, base_dir, languages,
):
    """Fallback: translate from page-level split files (no sutra directory)."""
    p2_dir = work_dir(base_dir, edition, "pass2-split")
    pages = sorted([int(f.stem.split("-")[1]) for f in p2_dir.glob("page-*.txt")])
    total = max(pages)
    end = min(end, total)

    langs = [l.strip() for l in languages.split(",")]

    for lang in langs:
        if lang == "en":
            system_prompt = PASS3_PROMPT
            suffix = "pass3"
            label = "English"
        elif lang == "he":
            system_prompt = PASS3_HEBREW
            suffix = "pass3-he"
            label = "Hebrew"
        else:
            continue

        out_dir = work_dir(base_dir, edition, suffix)
        print(f"Pass 3 (translate-{label}, page-level fallback): pages {start}–{end}")

        system = [{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }]

        ok, fail = 0, 0
        for pn in range(start, end + 1):
            pfx = f"[P3-{lang}:{pn}/{end}]"
            out_file = page_file(out_dir, pn)
            if resume and out_file.exists():
                ok += 1
                continue
            source_file = page_file(p2_dir, pn)
            if not source_file.exists():
                continue
            source_text = source_file.read_text(encoding="utf-8")
            try:
                msg = client.messages.create(
                    model=model, max_tokens=8192,
                    system=system,
                    messages=[{"role": "user", "content": source_text}],
                )
                result = msg.content[0].text
                out_file.write_text(result, encoding="utf-8")
                print(f"{pfx} saved ({len(result)} chars)")
                ok += 1
            except Exception as e:
                print(f"{pfx} ERROR — {e}", file=sys.stderr)
                fail += 1
            time.sleep(delay)
        # Update DB with translations (page-level fallback)
        db_file = db_path(base_dir, edition)
        if db_file.exists():
            db_update_translations(db_file, lang, out_dir)
        print(f"Pass 3 ({label}) done — {ok} ok, {fail} failed\n")

    return work_dir(base_dir, edition, "pass3")


# ── Pass 4: Glossary extraction + footnote annotation ────────────────────────

def run_pass4(
    client: Anthropic,
    model: str,
    edition: str,
    resume: bool,
    delay: float,
    base_dir: Path,
):
    """Extract glossary terms from Pass 3 English text, then annotate first
    occurrences with footnote markers on each page."""
    p3_dir = work_dir(base_dir, edition, "pass3")
    glossary_path = base_dir / "glossary.json"
    out_dir = work_dir(base_dir, edition, "pass3-annotated")

    pages = sorted(p3_dir.glob("page-*.txt"))
    if not pages:
        print("Pass 4: no Pass 3 output found. Run Pass 3 first.")
        return

    total = len(pages)
    print(f"Pass 4 (annotate): {edition} — {total} pages")

    # Step 1: Build glossary from full text (or use cached)
    if resume and glossary_path.exists():
        print("  glossary.json exists, loading cached...")
        glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
    else:
        full_text = ""
        for pf in pages:
            full_text += pf.read_text(encoding="utf-8") + "\n\n"

        print(f"  extracting terms from full text ({len(full_text)} chars)...")
        prompt = PASS35_GLOSSARY.format(full_text=full_text)
        try:
            result = call_text(client, model, prompt)
            # Strip markdown code fences if present
            result = result.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1]
                if result.endswith("```"):
                    result = result.rsplit("\n", 1)[0]
            glossary = json.loads(result)
            glossary_path.write_text(json.dumps(glossary, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  saved glossary.json ({len(glossary)} terms)")
        except Exception as e:
            print(f"  glossary extraction ERROR — {e}", file=sys.stderr)
            return
        time.sleep(delay)

    if not glossary:
        print("  no terms extracted, skipping annotation")
        return

    # Step 2: Build seen-terms tracker and annotate each page
    seen_terms = set()  # terms already footnoted on earlier pages
    ok, fail = 0, 0

    for pf in pages:
        page_num = int(pf.stem.split("-")[1])
        out_file = page_file(out_dir, page_num)

        if resume and out_file.exists():
            # Need to still track seen terms from this page for downstream pages
            text = out_file.read_text(encoding="utf-8")
            # Re-derive seen terms from annotated text
            for term in glossary:
                if f"«{term['term']}»" in text:
                    seen_terms.add(term["term"])
            ok += 1
            continue

        text = pf.read_text(encoding="utf-8")
        annotated = text

        for entry in glossary:
            term = entry["term"]
            if term in seen_terms:
                continue
            # Match as whole word (not part of another word), case sensitive
            import re
            pattern = re.compile(r'\b' + re.escape(term) + r'\b')
            match = pattern.search(annotated)
            if match:
                seen_terms.add(term)
                # Replace only the first occurrence on this page
                annotated = pattern.sub(f"«{term}»", annotated, count=1)

        out_file.write_text(annotated, encoding="utf-8")
        new_this_page = sum(1 for e in glossary if f"«{e['term']}»" in annotated and e["term"] not in seen_terms)
        print(f"  page {page_num}: annotated ({new_this_page} new terms)")
        ok += 1

    print(f"Pass 4 done —{ok} pages annotated, {len(seen_terms)}/{len(glossary)} terms used\n")
    return out_dir, glossary


# ── Pass 5: Typst PDF assembly ──────────────────────────────────────────────

TYPST_HEADER = r"""// Kama Sutra — trilingual edition (Devanagari + English + Hebrew, 3-column landscape)
#set document(title: "Kama Sutra", author: "Vatsyayana")

#set page(
  paper: "us-landscape",
  margin: (top: 0.7in, bottom: 0.7in, left: 0.6in, right: 0.6in),
  numbering: "1",
)

#set text(font: ("Noto Serif Devanagari", "Noto Serif"), size: 9pt)

#let deva-font = ("Noto Serif Devanagari", "Noto Sans Devanagari")
#let eng-font = ("Noto Serif", "Linux Libertine")
#let he-font = ("Noto Serif Hebrew", "David CLM", "SBL Hebrew")

#set page(header: context [
  #set text(size: 8pt)
  #align(center)[*Kama Sutra* — Vatsyayana · #counter(page).display()]
])

// ── Glossary ──────────────────────────────────────
#let glossary = (GLOSSARY_DICT)

#let glos(term) = footnote[#glossary.at(term)]

// ── Page layout: 3-column grid ────────────────────
// Each sutra/unit gets one row. Sutras are centered (like an epigraph);
// commentary is set as indented body text.
// No rules between rows — whitespace and centering are enough.
#let tricol(deva, eng, heb) = {
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 14pt,
    row-gutter: 6pt,

    // Column 1 — Sanskrit
    {
      set text(font: deva-font, size: 9pt, lang: "sa")
      set par(leading: 0.65em, first-line-indent: 0pt)
      deva
    },

    // Column 2 — English
    {
      set text(font: eng-font, size: 8.5pt, lang: "en")
      set par(leading: 0.55em, first-line-indent: 1.2em)
      eng
    },

    // Column 3 — Hebrew (RTL)
    {
      set text(font: he-font, size: 8.5pt, lang: "he", dir: rtl)
      set par(leading: 0.55em, first-line-indent: 0pt)
      heb
    },
  )
}

// Sutra block — centered, like an epigraph or blockquote
#let sutra-block(body) = {
  align(center)[
    #set par(first-line-indent: 0pt)
    #body
  ]
}

// Commentary block — normal body text, slightly indented
#let commentary-block(body) = {
  block(inset: (left: 1em), spacing: 0.4em)[
    #body
  ]
}

// ── Title page ────────────────────────────────────
#align(center + horizon)[
  #v(3cm)
  #text(size: 28pt, weight: "bold")[Kama Sutra]
  #v(0.5cm)
  #text(size: 16pt)[Vatsyayana]
  #v(1.5cm)
  #text(size: 13pt)[Trilingual Edition]
  #text(size: 11pt)[Sanskrit · English · Hebrew]
  #v(2cm)
  #text(size: 10pt)[2001 Printed Edition · Corrected against 1929 Edition]
]

// ── Content begins ─────────────────────────────────
"""

TYPST_GLOSSARY_HEADER = r"""
// ── Appendix: Glossary ────────────────────────────
#pagebreak()
#set page(numbering: "A-1")
#align(center)[
  #text(size: 18pt, weight: "bold")[Glossary]
  #v(1em)
  #text(size: 10pt)[Geographical names, ethnic groups, and technical terms]
]
#v(2em)

#set par(first-line-indent: 0pt, leading: 1em)

#let glossary-entry(term, def, category) = {
  let cat-label = if category == "place" {
    "[Place]"
  } else if category == "people" {
    "[People]"
  } else {
    "[Term]"
  }
  block(spacing: 0.6em)[
    #text(weight: "bold")[#term] #text(size: 9pt, fill: gray)[#cat-label]
    #def
  ]
}

"""


def escape_typst(text: str) -> str:
    """Escape Typst markup characters."""
    return text.replace("\\", "\\\\")


def strip_marker(text: str) -> tuple:
    """Strip [S], [C], [T] etc. marker from start of text. Returns (clean_text, marker)."""
    m = re.match(r'^\[([A-Z]+)\]\s*', text)
    if m:
        return text[m.end():], m.group(1)
    return text, "?"


# ── SQLite database ─────────────────────────────────────────────────────────

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS rows (
    rowid INTEGER PRIMARY KEY,
    marker TEXT NOT NULL DEFAULT '?',
    sanskrit TEXT NOT NULL DEFAULT '',
    english TEXT DEFAULT '',
    hebrew TEXT DEFAULT '',
    section TEXT DEFAULT ''
);
"""

def db_path(base_dir: Path, edition: str) -> Path:
    return base_dir / "work" / edition / "kama-sutra.db"

def init_db(db_file: Path):
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.execute(DB_SCHEMA)
    conn.commit()
    return conn

def db_populate_from_sutras(db_file: Path, sutras_dir: Path):
    """Load all sutra files into the DB, detecting markers."""
    conn = sqlite3.connect(str(db_file))
    conn.execute("DELETE FROM rows")  # fresh start
    sutra_files = sorted(sutras_dir.glob("sutra-*.txt"))
    for sf in sutra_files:
        text = sf.read_text(encoding="utf-8")
        clean, marker = strip_marker(text)
        conn.execute(
            "INSERT INTO rows (marker, sanskrit) VALUES (?, ?)",
            (marker.lower(), clean)
        )
    conn.commit()
    conn.close()
    return len(sutra_files)

def db_update_translations(db_file: Path, lang: str, translations_dir: Path):
    """Update English or Hebrew column from per-sutra translation files."""
    col = "english" if lang == "en" else "hebrew"
    conn = sqlite3.connect(str(db_file))
    trans_files = sorted(translations_dir.glob("sutra-*.txt"))
    for tf in trans_files:
        sutra_id = int(tf.stem.split("-")[1])
        text = tf.read_text(encoding="utf-8")
        clean, _ = strip_marker(text)
        conn.execute(
            f"UPDATE rows SET {col} = ? WHERE rowid = ?",
            (clean, sutra_id)
        )
    conn.commit()
    conn.close()
    return len(trans_files)

def db_section_labels(db_file: Path):
    """Detect section/chapter boundaries (heuristic: short rows, marker='sutra'
    followed by a pattern change). This is a post-processing step that the
    user can refine manually in the DB."""
    conn = sqlite3.connect(str(db_file))
    # Simple heuristic: rows that are just a number or a short label
    # are likely section markers. Let the user refine.
    # For now, just ensure the column exists.
    conn.execute("UPDATE rows SET section = '' WHERE section IS NULL")
    conn.commit()
    conn.close()


def convert_footnotes(text: str, glossary: list) -> str:
    """Convert «term» markers to Typst footnote calls using glossary."""
    # Build lookup: term → definition
    lookup = {entry["term"]: entry["definition"] for entry in glossary}
    # We'll replace «X» with X#glos("X") inline
    import re
    def replacer(match):
        term = match.group(1)
        return f'{term}#glos("{term}")'
    return re.sub(r'«([^»]+)»', replacer, text)


def build_glossary_dict_string(glossary: list) -> str:
    """Build the Typst dictionary literal for the glossary."""
    entries = []
    for entry in glossary:
        term = entry["term"].replace('"', '\\"')
        definition = entry["definition"].replace('"', '\\"')
        entries.append(f'  "{term}": "{definition}",')
    return "(\n" + "\n".join(sorted(entries)) + "\n)"


def run_pass5(
    edition: str,
    start: int,
    end: int,
    base_dir: Path,
):
    """Build a Typst file from the SQLite database.

    Each row becomes one 3-column grid. Marker type determines formatting:
      - sutra: centered (like an epigraph)
      - commentary: indented body text
      - title, section, chapter: larger, centered, with extra space
    """
    db_file = db_path(base_dir, edition)
    glossary_path = base_dir / "glossary.json"

    if not db_file.exists():
        # Fall back to file-based generation
        print("Pass 5: no database found. Run Pass 2 and 3 first.")
        return

    conn = sqlite3.connect(str(db_file))
    rows = conn.execute(
        "SELECT rowid, marker, sanskrit, english, hebrew, section FROM rows ORDER BY rowid"
    ).fetchall()
    conn.close()

    if not rows:
        print("Pass 5: database is empty.")
        return

    total = len(rows)
    has_hebrew = any(r[4] for r in rows if r[4])

    # Load glossary if available
    glossary = []
    if glossary_path.exists():
        glossary = json.loads(glossary_path.read_text(encoding="utf-8"))

    output_path = base_dir / f"kama-sutra-{edition}.typ"
    cols = "Sanskrit + English + Hebrew" if has_hebrew else "Sanskrit + English"
    print(f"Pass 5 (build): {output_path} — {total} rows — {cols}")

    glos_dict = build_glossary_dict_string(glossary) if glossary else "(:)"
    header = TYPST_HEADER.replace("GLOSSARY_DICT", glos_dict)
    lines = [header]

    prev_section = None
    for rowid, marker, sanskrit, english, hebrew, section in rows:
        sanskrit = sanskrit or ""
        english = english or ""
        hebrew = hebrew or ""

        # Section break: emit a section header
        if section and section != prev_section:
            prev_section = section
            lines.append("#v(16pt)")
            lines.append(f"// Section: {section}")
            lines.append(
                f"#align(center)[#text(size: 14pt, weight: \\\"bold\\\")[{escape_typst(section)}]]"
            )
            lines.append("#v(12pt)")

        # Determine block function by marker type
        if marker in ("sutra", "S"):
            block_fn = "sutra-block"
        elif marker in ("title", "chapter", "section", "T"):
            # Section headers handled above; skip row-level titles for sutra flow
            block_fn = "sutra-block"
        else:
            block_fn = "commentary-block"

        # Add vertical space between units
        if rowid > 1:
            lines.append("#v(8pt)")

        lines.append(f"// Row {rowid} [{marker}]")
        lines.append(f"#{block_fn}[")
        lines.append("#tricol[")
        for para in sanskrit.split("\n\n"):
            para = escape_typst(para.strip())
            if para:
                lines.append(f"  {para}\n")
        lines.append("][")
        for para in english.split("\n\n"):
            para = escape_typst(para.strip())
            if para:
                lines.append(f"  {para}\n")
        lines.append("][")
        for para in hebrew.split("\n\n"):
            para = escape_typst(para.strip())
            if para:
                lines.append(f"  {para}\n")
        lines.append("]")
        lines.append("]")  # close block_fn

    # ── Glossary appendix ─────────────────────────────────────────────────
    if glossary:
        lines.append(TYPST_GLOSSARY_HEADER)
        for cat in ["place", "people", "term"]:
            cat_entries = [e for e in glossary if e.get("category") == cat]
            if not cat_entries:
                continue
            cat_label = {"place": "Geographical Names", "people": "Ethnic & Tribal Groups", "term": "Technical Terms"}[cat]
            lines.append(f"// {cat_label}")
            lines.append(f"#text(size: 14pt, weight: \\\"bold\\\")[{cat_label}]")
            lines.append("#v(0.5em)")
            for entry in sorted(cat_entries, key=lambda e: e["term"].lower()):
                definition = escape_typst(entry["definition"])
                term = escape_typst(entry["term"])
                lines.append(f"#glossary-entry(\"{term}\", \"{definition}\", \"{cat}\")")
            lines.append("#v(1em)")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Pass 5 done — {output_path}")
    print(f"Compile: typst compile {output_path.name}")


# ── Status ──────────────────────────────────────────────────────────────────

def print_status(base_dir: Path, edition: str, total_pages: int):
    for p in ["pass1", "pass2", "pass3"]:
        d = work_dir(base_dir, edition, p)
        count = len(list(d.glob("page-*.txt")))
        print(f"  {edition}/{p}: {count}/{total_pages} pages")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Multi-edition OCR + translation pipeline for Kama Sutra"
    )
    parser.add_argument(
        "-p", "--passes", default="1",
        help="Passes to run: 1=OCR, 2=compare, 3=translate, 4=annotate, 5=build (default: 1)"
    )
    parser.add_argument(
        "--pdf", default="kama-sutra-2001.pdf",
        help="PDF to process (default: kama-sutra-2001.pdf)"
    )
    parser.add_argument(
        "--edition", default="",
        help="Edition label for output dirs (default: derived from PDF filename)"
    )
    parser.add_argument(
        "--secondary", default="kama-sutra-1929.pdf",
        help="Secondary PDF for Pass 2 comparison (default: kama-sutra-1929.pdf)"
    )
    parser.add_argument(
        "-m", "--model", default=os.environ.get("ANTHROPIC_MODEL", "deepseek-v4-pro"),
        help="Model name"
    )
    parser.add_argument(
        "--start", type=int, default=1,
        help="First page to process (1-based)"
    )
    parser.add_argument(
        "--end", type=int, default=0,
        help="Last page to process (1-based, 0 = all)"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Seconds between API calls"
    )
    parser.add_argument(
        "--no-resume", action="store_true",
        help="Re-process pages even if output exists"
    )
    parser.add_argument(
        "--languages", default="en",
        help="Target languages for Pass 3: en, he, or en,he (default: en)"
    )
    parser.add_argument(
        "--english-pages", default="",
        help="English front/back matter page ranges, e.g. '1-20,240-248'"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Print status and exit"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would happen without API calls"
    )
    parser.add_argument(
        "--anthropic", action="store_true",
        help="Use Anthropic API (~/.anthropic_api_key) instead of DeepSeek"
    )
    args = parser.parse_args()

    base_dir = Path(args.pdf).resolve().parent
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        # Try relative to base_dir
        pdf_path = base_dir / args.pdf
        if not pdf_path.exists():
            print(f"Error: '{args.pdf}' not found", file=sys.stderr)
            sys.exit(1)

    # Derive edition label from filename (e.g. "kama-sutra-2001.pdf" → "2001")
    _stem = pdf_path.stem
    _parts = _stem.rsplit("-", 1)
    edition = args.edition or (_parts[1] if len(_parts) == 2 and _parts[1].isdigit() else _stem)
    english_pages = set()
    if args.english_pages:
        for part in args.english_pages.split(","):
            part = part.strip()
            if "-" in part:
                lo, hi = part.split("-", 1)
                english_pages.update(range(int(lo), int(hi) + 1))
            else:
                english_pages.add(int(part))

    total = pdf_page_count(pdf_path)
    end_page = args.end if args.end > 0 else total
    end_page = min(end_page, total)

    passes = set()
    for p in args.passes.split(","):
        p = p.strip()
        if p in ("1", "2", "3", "4", "5"):
            passes.add(p)

    if args.status:
        print(f"Status for {edition}:")
        print_status(base_dir, edition, total)
        return

    print(f"PDF: {pdf_path.name} ({total} pages)")
    print(f"Edition: {edition}")
    print(f"Range: pages {args.start}–{end_page}")
    print(f"Passes: {', '.join(sorted(passes))}")
    print(f"Model: {args.model}")
    if "2" in passes:
        print(f"Secondary: {args.secondary}")
    if "3" in passes:
        print(f"Languages: {args.languages}")
    if english_pages:
        print(f"English pages: {sorted(english_pages)}")
    print(f"Resume: {not args.no_resume}")
    if args.dry_run:
        print("[DRY RUN]")
    print()

    if args.dry_run:
        return

    client = make_client(use_anthropic=args.anthropic)
    if args.anthropic:
        args.model = args.model if args.model != "deepseek-v4-pro" else "claude-sonnet-4-6"
        print(f"Provider: Anthropic (model: {args.model})")
    else:
        print(f"Provider: DeepSeek (model: {args.model})")
    resume = not args.no_resume

    # ── Pass 1: OCR ─────────────────────────────────────────────────────
    if "1" in passes:
        run_pass1(
            client, args.model, pdf_path,
            args.start, end_page, english_pages, resume, args.delay, base_dir,
        )

    # ── Pass 2: Compare ─────────────────────────────────────────────────
    if "2" in passes:
        # Derive secondary edition name
        sec_path = Path(args.secondary)
        if not sec_path.exists():
            sec_path = base_dir / args.secondary
        _sec_stem = sec_path.stem
        _sec_parts = _sec_stem.rsplit("-", 1)
        sec_edition = _sec_parts[1] if len(_sec_parts) == 2 and _sec_parts[1].isdigit() else _sec_stem

        run_pass2(
            client, args.model, edition, sec_edition,
            args.start, end_page, resume, args.delay, base_dir,
        )

    # ── Pass 3: Translate ───────────────────────────────────────────────
    if "3" in passes:
        run_pass3(
            client, args.model, edition,
            args.start, end_page, resume, args.delay, base_dir,
            languages=args.languages,
        )

    # ── Pass 4: Annotate ────────────────────────────────────────────────
    if "4" in passes:
        run_pass4(
            client, args.model, edition,
            resume, args.delay, base_dir,
        )

    # ── Pass 5: Build ───────────────────────────────────────────────────
    if "5" in passes:
        run_pass5(edition, args.start, end_page, base_dir)


if __name__ == "__main__":
    main()
