#!/usr/bin/env python3
"""Three-way walk-forward sentence alignment: 2001 OCR vs 1929 OCR vs TITUS.

TITUS is an independent witness, not ground truth. Discrepancies are flagged
for human reasoning — they are not automatically resolved toward any source.

Algorithm: sliding-window content matching across three sentence streams.
Suitable for OCR'd Devanagari (both editions) and TITUS Roman transliteration.

Usage:
    python align.py                          # align all available pages
    python align.py --book 2                 # align a specific book only
    python align.py --dump-titus             # extract TITUS sentences to stdout
"""

import re
import sys
from pathlib import Path
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from typing import Optional
from collections import deque

# ── Paths ────────────────────────────────────────────────────────────────────

BASE = Path(__file__).resolve().parent
TITUS_DIR = BASE / "kama-sutra-titus"
WORK_2001 = BASE / "work" / "2001" / "pass1"
WORK_1929 = BASE / "work" / "1929" / "pass1"
OUT_DIR = BASE / "work" / "alignment"


# ── Devanagari → IAST-like ASCII (lossy, for matching only) ───────────────────
#
# Both sides land on lowercase ASCII with no diacritics, so trigram overlap
# can find matching sentence pairs despite OCR errors and encoding differences.
#
# TITUS                           Devanagari          Both normalize to
# ─────────────────────────────   ─────────────────   ────────────────
# dʰarma^artha-kāmebʰyo namaḥ     धर्मार्थकामेभ्यो नमः  dharmarthakamebhyo namah

import unicodedata

# Character categories for Devanagari processing
import unicodedata

def _is_deva_consonant(ch: str) -> bool:
    """True if ch is a Devanagari consonant (has inherent 'a')."""
    return 0x0915 <= ord(ch) <= 0x0939

def _is_deva_vowel_sign(ch: str) -> bool:
    """True if ch is a dependent vowel sign (matra)."""
    return 0x093E <= ord(ch) <= 0x094C

def _is_deva_virama(ch: str) -> bool:
    """True if ch is virama (halant)."""
    return ord(ch) == 0x094D

def _is_deva_independent_vowel(ch: str) -> bool:
    """True if ch is an independent vowel character."""
    return (0x0904 <= ord(ch) <= 0x0914) or (0x0960 <= ord(ch) <= 0x0963)

def _is_deva_anunasika(ch: str) -> bool:
    """True if ch is anusvara, visarga, or candrabindu."""
    return ord(ch) in (0x0902, 0x0901, 0x0903)  # anusvara, candrabindu, visarga

# Consonant map (base consonant without inherent 'a')
_CONSONANT_MAP = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'N',
    'च': 'c', 'छ': 'ch', 'ज': 'j', 'झ': 'jh', 'ञ': 'Y',
    'ट': 'T', 'ठ': 'Th', 'ड': 'D', 'ढ': 'Dh', 'ण': 'N',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'S', 'ष': 's', 'स': 's', 'ह': 'h',
}

_VOWEL_SIGN_MAP = {
    'ा': 'A', 'ि': 'i', 'ी': 'I', 'ु': 'u', 'ू': 'U',
    'ृ': 'R', 'ॄ': 'RR', 'े': 'e', 'ै': 'E', 'ो': 'o', 'ौ': 'O',
}

_INDEPENDENT_VOWEL_MAP = {
    'अ': 'a', 'आ': 'A', 'इ': 'i', 'ई': 'I', 'उ': 'u', 'ऊ': 'U',
    'ऋ': 'R', 'ॠ': 'RR', 'ऌ': 'lR', 'ए': 'e', 'ऐ': 'E', 'ओ': 'o', 'औ': 'O',
}

_MISC_MAP = {
    'ं': 'M', 'ः': 'H', 'ँ': 'm', 'ऽ': "'", 'ॐ': 'OM',
    '।': ' . ', '॥': ' . ',
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    '‌': '', '‍': '',  # ZWNJ, ZWJ
}


def deva_to_roman(text: str) -> str:
    """Transliterate Devanagari to a lossy IAST-like ASCII form for fuzzy matching.

    Handles the inherent 'a' vowel correctly:
    - Consonant at end of word or before space/punctuation → C + 'a'
    - Consonant + virama → C (no vowel)
    - Consonant + another consonant (implicit conjunct) → C (no vowel)
    - Consonant + vowel sign → C + vowel
    - Consonant + anunasika (anusvara/visarga) → C + 'a' + mark
    """
    result = []
    chars = list(text)
    n = len(chars)

    for i, ch in enumerate(chars):
        if _is_deva_virama(ch):
            continue  # skip virama; it already suppressed the previous consonant's 'a'

        if _is_deva_consonant(ch):
            base = _CONSONANT_MAP.get(ch, ch)
            result.append(base)

            # Determine the vowel for this consonant
            if i + 1 < n:
                nxt = chars[i + 1]
                if _is_deva_vowel_sign(nxt):
                    # vowel sign replaces inherent 'a'
                    result.append(_VOWEL_SIGN_MAP.get(nxt, nxt))
                elif _is_deva_virama(nxt):
                    # explicit virama: no vowel
                    pass
                elif _is_deva_consonant(nxt):
                    # consonant + consonant without virama: first gets inherent 'a'
                    # (true conjuncts always use explicit virama in Unicode Devanagari)
                    result.append('a')
                elif _is_deva_anunasika(nxt):
                    # anunasika after consonant: inherent 'a' + mark
                    result.append('a')
                    result.append(_MISC_MAP.get(nxt, nxt))
                elif nxt in (' ', '\t', '\n', '.', '।', '॥') or nxt in _MISC_MAP:
                    # word boundary: inherent 'a'
                    result.append('a')
                    if nxt in _MISC_MAP:
                        result.append(_MISC_MAP.get(nxt, nxt))
                else:
                    # other (e.g., independent vowel after consonant is unusual)
                    result.append('a')
            else:
                # end of text: inherent 'a'
                result.append('a')

        elif _is_deva_vowel_sign(nxt_ch := ch):
            # vowel signs are handled above with their consonant; skip here
            # (but if one appears without a consonant, render it anyway)
            if i == 0 or not _is_deva_consonant(chars[i - 1]):
                result.append(_VOWEL_SIGN_MAP.get(ch, ch))

        elif _is_deva_independent_vowel(ch):
            result.append(_INDEPENDENT_VOWEL_MAP.get(ch, ch))

        elif _is_deva_anunasika(ch):
            # Already handled above with consonant; standalone (rare)
            result.append(_MISC_MAP.get(ch, ch))

        elif ch in _MISC_MAP:
            result.append(_MISC_MAP[ch])

        elif ch in (' ', '\t', '\n'):
            result.append(' ')

        else:
            # Non-Devanagari character (e.g., Latin in mixed text): keep as-is
            result.append(ch)

    return ''.join(result)


# ── TITUS Roman normalization ────────────────────────────────────────────────

def normalize_titus_token(token: str) -> str:
    """Reduce a TITUS roman token to lowercase ASCII for matching.

    TITUS uses Unicode diacritics: dʰ (aspiration superscript h), r̥ (ring below),
    ś/ṣ (accented sibilants), ṇ/ṭ/ḍ (dot-below retroflex), ā/ī/ū (macron vowels).
    We strip all diacritics and lowercase, leaving bare ASCII that matches
    the lossy deva→roman output.
    """
    # Decompose: e.g., ā → a + combining macron
    nfkd = unicodedata.normalize('NFKD', token)
    # Strip combining characters
    ascii_chars = [c for c in nfkd if not unicodedata.combining(c)]
    ascii_str = ''.join(ascii_chars)
    # Remove TITUS markers
    ascii_str = ascii_str.replace('^', '').replace('-', '').replace('+', '')
    return ascii_str.lower()


def normalize_ocr_token(token: str) -> str:
    """Reduce an OCR roman token (from deva_to_roman) to lowercase for matching."""
    return token.lower()


# ── TITUS parsing ────────────────────────────────────────────────────────────

@dataclass
class TitusSentence:
    """A single sentence from the TITUS digital edition."""
    book: int
    chapter: int          # TITUS chapter numbering (1-based within book)
    sentence_num: int     # 1-based within chapter
    page: int             # printed edition page number
    text: str             # raw text from ioskps16 span
    tokens: list[str] = field(default_factory=list)
    norm: str = ""        # normalized for matching


def parse_titus() -> list[TitusSentence]:
    """Parse all TITUS HTML files, extract sentences from ioskps16 spans."""
    sentences = []
    for book in range(1, 8):
        html_path = TITUS_DIR / f"kamas{book:03d}.htm"
        if not html_path.exists():
            continue
        html = html_path.read_text(encoding="utf-8")

        # Extract sentences with their metadata
        # Pattern: Level 5 sentence marker, then ioskps16 span text
        # Each sentence may span multiple lines but is bounded by </span>

        # Find all sentence blocks
        sent_pattern = re.compile(
            r'<span id=h5>.*?Sentence:\s*(\d+).*?</sPAN>\s*'
            r'(.*?)'
            r'(?=<span id=h5>|<span id=h6>|<BR>\s*<BR>\s*<span id=h[34]>)',
            re.DOTALL
        )

        # Simpler approach: find all ioskps16 spans and associate them with
        # the preceding h5 sentence marker
        blocks = re.split(r'(<span id=h5>.*?</sPAN>)', html)

        current_sent_num = None
        current_page = None
        current_chapter = 1

        for block in blocks:
            # Track chapter changes
            chap_match = re.search(r'Chapter:\s*(\d+)', block)
            if chap_match:
                current_chapter = int(chap_match.group(1))

            # Track page changes
            page_match = re.search(r'Page of edition:\s*(\d+)', block)
            if page_match:
                current_page = int(page_match.group(1))

            # Track sentence markers
            sent_match = re.search(r'Sentence:\s*(\d+)', block)
            if sent_match:
                current_sent_num = int(sent_match.group(1))

            # Extract ioskps16 text
            ioskps_match = re.findall(
                r'<span id=ioskps16>(.*?)</span>',
                block
            )
            if ioskps_match and current_sent_num is not None:
                # Join all ioskps16 spans in this block
                tokens = []
                for span in ioskps_match:
                    # Extract text from <a> tags
                    toks = re.findall(r'<a[^>]*>([^<]*)</a>', span)
                    tokens.extend(toks)

                raw_text = ' '.join(tokens)
                norm_text = normalize_titus_token(raw_text)

                sentences.append(TitusSentence(
                    book=book,
                    chapter=current_chapter,
                    sentence_num=current_sent_num,
                    page=current_page or 0,
                    text=raw_text,
                    tokens=tokens,
                    norm=norm_text,
                ))

    return sentences


# ── OCR text parsing ─────────────────────────────────────────────────────────

@dataclass
class OcrSentence:
    """A single sentence from OCR output."""
    edition: str           # "2001" or "1929"
    page: int
    sentence_idx: int      # 0-based within the page
    text: str              # original Devanagari text
    norm: str = ""         # normalized for matching


def parse_ocr(edition: str, work_dir: Path) -> list[OcrSentence]:
    """Parse all OCR output for an edition into sentences."""
    sentences = []
    page_files = sorted(work_dir.glob("page-*.txt"))

    for pf in page_files:
        page_num = int(pf.stem.split("-")[1])
        text = pf.read_text(encoding="utf-8").strip()

        # Skip non-Sanskrit pages (English summaries, blank pages)
        if _is_non_sanskrit(text):
            continue

        # Split on newlines first (headings, titles, sutras are on separate lines),
        # then split each line on dandas for multi-sentence lines.
        lines = text.split('\n')
        seq = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = re.split(r'(?<=[।॥])', line)
            for part in parts:
                part = part.strip()
                if not part or len(part) < 3:
                    continue

                norm = deva_to_roman(part)
                sentences.append(OcrSentence(
                    edition=edition,
                    page=page_num,
                    sentence_idx=seq,
                    text=part,
                    norm=normalize_ocr_token(norm),
                ))
                seq += 1

    return sentences


def _is_non_sanskrit(text: str) -> bool:
    """Heuristic: detect pages that are English/Hindi summaries, not Sanskrit text."""
    # Count Devanagari characters
    deva_chars = sum(1 for c in text if 'ऀ' <= c <= 'ॿ')
    total_chars = len(text.strip())
    if total_chars == 0:
        return True
    # If less than 30% Devanagari, probably not a Sanskrit page
    if deva_chars / max(total_chars, 1) < 0.3:
        return True
    return False


# ── Similarity computation ───────────────────────────────────────────────────

def token_similarity(a: str, b: str) -> float:
    """Compute similarity between two normalized strings.

    Uses character trigram Jaccard overlap. Jaccard (intersection/union)
    correctly penalizes length mismatches: a short sutra matching against
    a long commentary passage gets a low score because the commentary
    contributes many unmatched trigrams to the union.

    Whitespace is stripped: TITUS joins tokens with spaces but OCR
    Devanagari runs compounds together, so space-based trigrams like
    "a n" vs "an" would otherwise inflate the union for no benefit.
    """
    if not a or not b:
        return 0.0

    def trigrams(s):
        return set(s[i:i+3] for i in range(len(s) - 2))

    # Strip whitespace so spacing differences between TITUS (word-separated)
    # and OCR Devanagari (compounds without spaces) don't degrade matching.
    ta = trigrams(a.replace(' ', ''))
    tb = trigrams(b.replace(' ', ''))

    if not ta or not tb:
        return 0.0

    intersection = len(ta & tb)
    union = len(ta | tb)
    return intersection / union if union > 0 else 0.0


# ── Walk-forward alignment ───────────────────────────────────────────────────

@dataclass
class AlignedRow:
    """One row in the walk-forward alignment output."""
    position: int
    titus_ref: str           # e.g., "2.1.3" (book.chapter.sentence)
    titus_text: str
    text_2001: str
    text_1929: str
    confidence: float         # 0.0–1.0
    flags: list[str]          # "2001_diverges", "1929_diverges", "all_diverge", etc.
    titus_page: int = 0
    page_2001: int = 0
    page_1929: int = 0


def walk_forward_align(
    titus_sentences: list[TitusSentence],
    ocr_2001: list[OcrSentence],
    ocr_1929: list[OcrSentence],
    window: int = 5,
    min_similarity: float = 0.25,
) -> list[AlignedRow]:
    """Three-way walk-forward sentence alignment.

    Synchronizes each OCR stream to TITUS by finding the first strong match
    (scanning past front matter), then walks forward. Re-syncs at every
    chapter boundary so commentary gaps in one chapter don't poison the next.
    Search is unbounded — always scans the full remaining OCR stream.
    """
    result = []
    i = _synchronize(titus_sentences, ocr_2001, min_similarity) if ocr_2001 else 0
    j = _synchronize(titus_sentences, ocr_1929, min_similarity) if ocr_1929 else 0

    pos_2001, pos_1929 = None, None
    prev_chapter = None

    for ts in titus_sentences:
        titus_norm = ts.norm

        # Re-sync at chapter boundaries: build a fingerprint from this
        # chapter's first few sentences and find it in the remaining OCR.
        current_chapter = (ts.book, ts.chapter)
        if current_chapter != prev_chapter and prev_chapter is not None:
            chap_sents = [t for t in titus_sentences
                          if t.book == ts.book and t.chapter == ts.chapter][:3]
            if chap_sents and i < len(ocr_2001):
                offset = _synchronize(chap_sents, ocr_2001[i:], min_similarity)
                if offset > 0:
                    i = i + offset
            if chap_sents and j < len(ocr_1929):
                offset = _synchronize(chap_sents, ocr_1929[j:], min_similarity)
                if offset > 0:
                    j = j + offset
        prev_chapter = current_chapter

        remaining_2001 = len(ocr_2001) - i if i < len(ocr_2001) else 0
        remaining_1929 = len(ocr_1929) - j if j < len(ocr_1929) else 0

        # Progressive threshold: matches near the cursor (within the tight
        # window) use min_similarity.  Matches found further away require
        # progressively higher similarity to prevent spurious long-range
        # matches on commentary/colophons that happen to share trigrams.
        best_2001 = _best_match(titus_norm, ocr_2001, i,
                                min(window, remaining_2001),
                                min_similarity) if remaining_2001 else None
        if best_2001 is None and remaining_2001 > window:
            # Scan remainder, but require higher threshold to avoid false matches
            best_2001 = _best_match(titus_norm, ocr_2001, i,
                                    remaining_2001,
                                    max(min_similarity, 0.35))
        if best_2001 is not None:
            i = ocr_2001.index(best_2001) + 1
            pos_2001 = best_2001
        else:
            if remaining_2001:
                i += 1
            pos_2001 = None

        best_1929 = _best_match(titus_norm, ocr_1929, j,
                                min(window, remaining_1929),
                                min_similarity) if remaining_1929 else None
        if best_1929 is None and remaining_1929 > window:
            best_1929 = _best_match(titus_norm, ocr_1929, j,
                                    remaining_1929,
                                    max(min_similarity, 0.35))
        if best_1929 is not None:
            j = ocr_1929.index(best_1929) + 1
            pos_1929 = best_1929
        else:
            if remaining_1929:
                j += 1
            pos_1929 = None

        # Compute confidence and flags
        flags = []
        conf = 1.0

        text_2001 = pos_2001.text if pos_2001 else ""
        text_1929 = pos_1929.text if pos_1929 else ""

        if pos_2001 is None and pos_1929 is None:
            flags.append("both_missing")
            conf = 0.0
        elif pos_2001 is None:
            flags.append("2001_missing")
            conf = 0.4
        elif pos_1929 is None:
            flags.append("1929_missing")
            conf = 0.4
        else:
            sim_12 = token_similarity(pos_2001.norm, pos_1929.norm)
            sim_1t = token_similarity(pos_2001.norm, titus_norm)
            sim_2t = token_similarity(pos_1929.norm, titus_norm)

            conf = (sim_1t + sim_2t + sim_12) / 3

            if sim_12 < 0.5:
                flags.append("editions_diverge")
            if sim_1t < 0.4 and sim_2t >= 0.4:
                flags.append("2001_diverges")
            if sim_2t < 0.4 and sim_1t >= 0.4:
                flags.append("1929_diverges")
            if sim_1t < 0.4 and sim_2t < 0.4:
                flags.append("all_diverge_from_titus")

        titus_ref = f"{ts.book}.{ts.chapter}.{ts.sentence_num}"

        result.append(AlignedRow(
            position=len(result),
            titus_ref=titus_ref,
            titus_text=ts.text,
            text_2001=text_2001,
            text_1929=text_1929,
            confidence=round(conf, 3),
            flags=flags,
            titus_page=ts.page,
            page_2001=pos_2001.page if pos_2001 else 0,
            page_1929=pos_1929.page if pos_1929 else 0,
        ))

    return result


def _synchronize(
    titus_first: list[TitusSentence],
    candidates: list[OcrSentence],
    min_sim: float,
    max_scan: int = 500,
) -> int:
    """Find where the TITUS text stream begins in the OCR stream.

    Uses a fingerprint of the first few TITUS sentences (concatenated) to
    find a specific match, avoiding false positives from short matches.
    Returns the index of the first matching OCR sentence, or 0 if none found.
    """
    if not candidates or not titus_first:
        return 0

    # Build a fingerprint from the first N TITUS sentences
    fingerprint = ' '.join(ts.norm for ts in titus_first[:3])

    best_idx = 0
    best_sim = min_sim

    # Also try single-sentence matching for short TITUS sentences
    first_norm = titus_first[0].norm

    first_len = len(first_norm)
    end = min(max_scan, len(candidates))
    for idx in range(end):
        cand_norm = candidates[idx].norm
        cand_len = len(cand_norm)

        # Length filter: skip candidates wildly different in size from the
        # first TITUS sentence (filters commentary/colophons during sync).
        if first_len > 0 and cand_len > 0:
            if cand_len > first_len * 4 or first_len > cand_len * 4:
                continue

        # Score: max of fingerprint match and single-sentence match
        fp_sim = token_similarity(fingerprint, cand_norm)
        s1_sim = token_similarity(first_norm, cand_norm)
        sim = max(fp_sim, s1_sim * 0.9)  # slightly discount single-sentence matches

        if sim > best_sim:
            best_sim = sim
            best_idx = idx

    return best_idx


def _best_match(
    target_norm: str,
    candidates: list[OcrSentence],
    cursor: int,
    window: int,
    min_sim: float,
) -> Optional[OcrSentence]:
    """Find the best-matching sentence within [cursor, cursor+window).

    Skips candidates whose normalized length differs from the target by more
    than 4x — this filters out commentary and colophons, which are typically
    much longer than root sutras.
    """
    if cursor >= len(candidates):
        return None

    end = min(cursor + window, len(candidates))
    best = None
    best_sim = min_sim
    target_len = len(target_norm)

    for idx in range(cursor, end):
        cand_norm = candidates[idx].norm
        cand_len = len(cand_norm)

        # Length filter: skip candidates >4x longer or shorter than target.
        # Commentary/colophons can be 200-500+ chars vs a 25-char sutra.
        if target_len > 0 and cand_len > 0:
            if cand_len > target_len * 4 or target_len > cand_len * 4:
                continue

        sim = token_similarity(target_norm, cand_norm)
        if sim > best_sim:
            best_sim = sim
            best = candidates[idx]

    return best


# ── Output formatting ────────────────────────────────────────────────────────

def write_alignment(rows: list[AlignedRow], out_path: Path) -> None:
    """Write alignment as TSV with clear discrepancy markers."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    header = [
        "pos", "titus_ref", "titus_page",
        "conf", "flags",
        "titus_text",
        "text_2001", "page_2001",
        "text_1929", "page_1929",
    ]

    def _clean(s: str) -> str:
        """Collapse whitespace so each row is exactly one TSV line."""
        return " ".join(s.split())

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join([
                str(r.position),
                r.titus_ref,
                str(r.titus_page),
                f"{r.confidence:.3f}",
                ",".join(r.flags) if r.flags else "clean",
                _clean(r.titus_text),
                _clean(r.text_2001), str(r.page_2001),
                _clean(r.text_1929), str(r.page_1929),
            ]) + "\n")

    print(f"Alignment written: {out_path} ({len(rows)} rows)")


def print_summary(rows: list[AlignedRow]) -> None:
    """Print a human-readable summary of the alignment."""
    total = len(rows)
    clean = sum(1 for r in rows if not r.flags)
    flagged = total - clean

    flag_counts = {}
    for r in rows:
        for f in r.flags:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    avg_conf = sum(r.confidence for r in rows) / max(total, 1)

    print(f"\n{'='*60}")
    print(f"Walk-Forward Alignment Summary")
    print(f"{'='*60}")
    print(f"Total TITUS sentences: {total:>5}")
    print(f"Clean (all agree):     {clean:>5}  ({clean/max(total,1)*100:.1f}%)")
    print(f"Flagged (discrepancy): {flagged:>5}  ({flagged/max(total,1)*100:.1f}%)")
    print(f"Avg confidence:        {avg_conf:.3f}")
    print(f"\nFlag breakdown:")
    for flag, count in sorted(flag_counts.items(), key=lambda x: -x[1]):
        print(f"  {flag}: {count}")
    print()

    # Show first few discrepancies
    if flagged > 0:
        print("First 10 flagged rows:")
        shown = 0
        for r in rows:
            if r.flags and shown < 10:
                print(f"\n  [{r.titus_ref}] flags={r.flags} conf={r.confidence:.3f}")
                print(f"    TITUS:  {r.titus_text[:120]}")
                if r.text_2001:
                    print(f"    2001:   {r.text_2001[:120]}")
                else:
                    print(f"    2001:   (missing)")
                if r.text_1929:
                    print(f"    1929:   {r.text_1929[:120]}")
                else:
                    print(f"    1929:   (missing)")
                shown += 1
        print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Three-way walk-forward sentence alignment")
    ap.add_argument("--book", type=int, help="Align a specific TITUS book (1-7)")
    ap.add_argument("--window", type=int, default=5, help="Search window size (default 5)")
    ap.add_argument("--min-sim", type=float, default=0.25, help="Minimum similarity threshold")
    ap.add_argument("--dump-titus", action="store_true", help="Dump parsed TITUS sentences to stdout")
    ap.add_argument("--out", type=str, help="Output TSV path")
    args = ap.parse_args()

    print("Parsing TITUS...")
    titus_all = parse_titus()
    print(f"  {len(titus_all)} sentences across {len(set(s.book for s in titus_all))} books")

    if args.book:
        titus_all = [s for s in titus_all if s.book == args.book]
        print(f"  Filtered to book {args.book}: {len(titus_all)} sentences")

    if args.dump_titus:
        for s in titus_all:
            print(f"[{s.book}.{s.chapter}.{s.sentence_num}] (p.{s.page}) {s.text}")
        return

    print("Parsing 2001 OCR...")
    ocr_2001 = parse_ocr("2001", WORK_2001)
    print(f"  {len(ocr_2001)} sentences from {len(set(s.page for s in ocr_2001))} pages")

    print("Parsing 1929 OCR...")
    ocr_1929 = parse_ocr("1929", WORK_1929)
    print(f"  {len(ocr_1929)} sentences from {len(set(s.page for s in ocr_1929))} pages")

    if not ocr_2001 and not ocr_1929:
        print("No OCR data found. Run Pass 1 first.")
        return

    print(f"\nAligning (window={args.window}, min_sim={args.min_sim})...")
    rows = walk_forward_align(
        titus_all, ocr_2001, ocr_1929,
        window=args.window,
        min_similarity=args.min_sim,
    )

    print_summary(rows)

    out_path = Path(args.out) if args.out else OUT_DIR / "alignment.tsv"
    write_alignment(rows, out_path)


if __name__ == "__main__":
    main()
