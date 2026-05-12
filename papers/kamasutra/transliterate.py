#!/usr/bin/env python3
"""TITUS Roman (IAST with diacritics) → Devanagari transliterator.

Deterministic — Roman with diacritics → Devanagari is unambiguous because
every vowel is explicit (no inherent-'a' guessing).

TITUS conventions handled:
    ^  → avagraha (ऽ)
    -  → compound boundary (removed — Devanagari doesn't space compounds)
    *  → uncertain reading marker (removed)
    +  → interpolation marker (removed)
    ʰ  → superscript h marks aspirated consonant (kʰ→ख vs kh→क्ह)

Strategy: first convert all TITUS-specific sequences to unique ASCII tokens,
NFKD-normalize to decompose precomposed diacritics, then walk through the
clean ASCII string building Devanagari with consonant/vowel context.
"""

import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent

# ── Step 1: TITUS-specific sequences → unique ASCII tokens ──────────────────

# Aspirated consonants (superscript h U+02B0).  Map to capital letters so
# the state machine treats them as single Devanagari consonants.
SUPERSCRIPT_TO_TOKEN = {
    "kʰ": "K",   # ख
    "gʰ": "G",   # घ
    "cʰ": "C",   # छ
    "jʰ": "J",   # झ
    "ṭʰ": "W",   # ठ
    "ḍʰ": "Z",   # ढ
    "tʰ": "T",   # थ
    "dʰ": "D",   # ध
    "pʰ": "P",   # फ
    "bʰ": "B",   # भ
    "mʰ": "mh",  # म्ह (rare — usually it's just regular m+h)
    "nʰ": "nh",  # न्ह
    "lʰ": "lh",  # ल्ह
    "vʰ": "vh",  # व्ह
    "rʰ": "rh",  # र्ह
    "sʰ": "sh",  # स्ह
    "hʰ": "hh",  # ह्ह
}

# Precomposed diacritic chars → tokens.  These are simpler than their
# NFKD-decomposed equivalents and are unambiguous in TITUS context.
PRECOMPOSED_TO_TOKEN = {
    "ś": "x",    # ś → श  (palatal sibilant)
    "ṣ": "X",    # ṣ → ष  (retroflex sibilant)
    "ṇ": "N",    # ṇ → ण  (retroflex n)
    "ṭ": "w",    # ṭ → ट  (retroflex t)
    "ḍ": "q",    # ḍ → ड  (retroflex d)
    "ṃ": "M",    # ṃ → ं  (anusvara)
    "ḥ": "H",    # ḥ → ः  (visarga)
    "ṅ": "Q",    # ṅ → ङ  (velar nasal)
    "ñ": "F",    # ñ → ञ  (palatal nasal)
}

# ── Step 3: Token → Devanagari ──────────────────────────────────────────────

# Note: these are applied AFTER NFKD which decomposes ā→a+macron etc.
# The state machine handles vowel context (independent vs matra).

# Consonants (including our token replacements)
CONSONANT_MAP = {
    # Plain stops
    "k": "क", "g": "ग",
    "c": "च", "j": "ज",
    "t": "त", "d": "द",
    "p": "प", "b": "ब",
    # Nasals
    "n": "न", "m": "म",
    # Semivowels + sibilants + ha
    "y": "य", "r": "र", "l": "ल", "v": "व",
    "s": "स", "h": "ह",
    # Aspirated (from superscript h → token)
    "K": "ख", "G": "घ",
    "C": "छ", "J": "झ",
    "W": "ठ", "Z": "ढ",
    "T": "थ", "D": "ध",
    "P": "फ", "B": "भ",
    # Diacritic consonants (from precomposed → token)
    "x": "श",   # ś
    "X": "ष",   # ṣ
    "N": "ण",   # ṇ
    "w": "ट",   # ṭ
    "q": "ड",   # ḍ
    "M": "ं",   # ṃ (anusvara) — attaches to previous, no vowel
    "H": "ः",   # ḥ (visarga) — attaches to previous, no vowel
    "Q": "ङ",   # ṅ
    "F": "ञ",   # ñ
}

# Vowels (independent forms — used at start of word or after vowel)
INDEPENDENT_VOWEL = {
    "a": "अ", "ā": "आ",
    "i": "इ", "ī": "ई",
    "u": "उ", "ū": "ऊ",
    "e": "ए", "ai": "ऐ",
    "o": "ओ", "au": "औ",
}

# Vowel matras (attach to preceding consonant)
MATRA = {
    "a": "",     # inherent — no explicit mark
    "ā": "ा",
    "i": "ि",
    "ī": "ी",
    "u": "ु",
    "ū": "ू",
    "e": "े",
    "ai": "ै",
    "o": "ो",
    "au": "ौ",
}

# Characters that are inherently vowel-less (they don't take vowel matras
# and don't need virama before a following consonant)
_VOWELLESS = set("MH")  # anusvara, visarga


def _is_vowel(c: str) -> bool:
    return c in "aiueo"


def titus_to_devanagari(text: str) -> str:
    """Transliterate TITUS Roman text to Devanagari."""

    # ── Pass 1: map TITUS-specific sequences to clean ASCII tokens ──
    for titus_seq, token in SUPERSCRIPT_TO_TOKEN.items():
        text = text.replace(titus_seq, token)
    for titus_seq, token in PRECOMPOSED_TO_TOKEN.items():
        text = text.replace(titus_seq, token)

    # ── Pass 2: NFKD normalize to decompose remaining precomposed chars ──
    text = unicodedata.normalize("NFKD", text)

    # ── Pass 3: walk through building Devanagari ──
    result = []
    i = 0
    n = len(text)

    def _take_combining(pos: int) -> tuple[str, int]:
        """Collect combining marks starting at pos. Returns (marks, new_pos)."""
        marks = ""
        while pos < n and unicodedata.combining(text[pos]):
            marks += text[pos]
            pos += 1
        return marks, pos

    # What kind of thing did we last output?  Tracks whether the next vowel
    # should be independent (after space/start/another vowel) or a matra
    # (after a consonant).
    # Values: "start", "consonant", "vowelless", "vowel"
    last = "start"

    while i < n:
        c = text[i]

        # ── TITUS markers ──
        if c == "^":
            result.append("ऽ")
            last = "vowel"  # avagraha is vowel-like for context
            i += 1
            continue
        elif c in "-+*":
            i += 1
            continue
        elif c in "[]()/":
            result.append(c)
            last = "start"  # bracket resets context
            i += 1
            continue
        elif c == ".":
            result.append("।")
            last = "start"
            i += 1
            continue
        elif c == " ":
            result.append(" ")
            last = "start"
            i += 1
            continue
        elif c.isdigit():
            result.append(c)
            i += 1
            continue

        # ── Collect combining marks after c ──
        combining, j = _take_combining(i + 1)

        macron = "̄" in combining   #  ̄ → long vowel
        ring   = "̥" in combining   # ̥ → syllabic r
        acute  = "́" in combining   #  ́ → acute accent (appears on í)

        # ── r̥ (r + ring below) → ऋ (independent) or ृ (matra) ──
        if c == "r" and ring:
            if last == "consonant":
                result.append("ृ")   # matra: कृ, पृ, गृ, etc.
            else:
                result.append("ऋ")   # independent: ऋग्वेद, etc.
            last = "vowel"           # r̥ is a vowel for sandhi/context
            i = j
            continue

        # ── Vowel (possibly with macron) ──
        if c in "aiueo":
            # Build the vowel key (e.g., "a" or "ā" via macron)
            vowel_long = macron
            if c == "a" and vowel_long:
                vkey = "ā"
            elif c == "i" and vowel_long:
                vkey = "ī"
            elif c == "u" and vowel_long:
                vkey = "ū"
            else:
                vkey = c

            # Look ahead: if another vowel follows, it might form a diphthong
            nxt_c = text[j] if j < n else ""
            if c == "a" and nxt_c == "i" and not vowel_long:
                vkey = "ai"
                j += 1
                # consume combining marks after the 'i' too
                nxt_comb, j = _take_combining(j)
            elif c == "a" and nxt_c == "u" and not vowel_long:
                vkey = "au"
                j += 1
                nxt_comb, j = _take_combining(j)

            if last in ("start", "vowel"):
                # Independent vowel form
                result.append(INDEPENDENT_VOWEL.get(vkey, c))
            else:
                # Matra — attaches to previous consonant
                result.append(MATRA.get(vkey, ""))
            last = "vowel"
            i = j
            continue

        # ── Consonant ──
        if c in CONSONANT_MAP:
            deva = CONSONANT_MAP[c]
            is_vowelless = c in _VOWELLESS

            # Look ahead to determine vowel context
            nxt_c = text[j] if j < n else ""
            nxt_comb, nxt_j = _take_combining(j + 1) if j < n else ("", j)

            if is_vowelless:
                # Anusvara/visarga: output directly, no vowel handling
                result.append(deva)
                last = "vowelless"
                i = j  # skip combining marks (shouldn't be any)
                continue

            # Determine what vowel (if any) follows this consonant
            # nxt_c could be: vowel, consonant, marker, space, end
            if not nxt_c or nxt_c in " ^-+*[](). ":
                # End or marker — inherent 'a'
                result.append(deva)
                i = j
            elif nxt_c in "aiueo" or (nxt_c == "r" and "̥" in nxt_comb):
                # Vowel follows (including r̥ = syllabic r)
                if nxt_c == "r" and "̥" in nxt_comb:
                    result.append(deva + "ृ")  # syllabic r matra
                    i = nxt_j
                else:
                    vlong = "̄" in nxt_comb
                    if nxt_c == "a" and vlong:
                        vk = "ā"
                    elif nxt_c == "i" and vlong:
                        vk = "ī"
                    elif nxt_c == "u" and vlong:
                        vk = "ū"
                    else:
                        vk = nxt_c

                    # Check for diphthong
                    nxt2 = text[nxt_j] if nxt_j < n else ""
                    if nxt_c == "a" and nxt2 == "i" and not vlong:
                        vk = "ai"
                        nxt_j += 1
                    elif nxt_c == "a" and nxt2 == "u" and not vlong:
                        vk = "au"
                        nxt_j += 1

                    result.append(deva + MATRA.get(vk, ""))
                    i = nxt_j
            elif nxt_c in CONSONANT_MAP:
                # Consonant follows → virama (halant)
                # Exception: if nxt_c is anusvara/visarga, no virama needed
                # (anusvara/visarga can follow directly)
                if nxt_c in _VOWELLESS:
                    result.append(deva)
                else:
                    result.append(deva + "्")  # ् virama
                i = j
            else:
                # Unknown — assume inherent 'a'
                result.append(deva)
                i = j

            last = "consonant"
            continue

        # ── Fallback ──
        result.append(c)
        i += 1

    return "".join(result)


# ── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(BASE))
    from align import parse_titus

    titus = parse_titus()
    print(f"Transliterating {len(titus)} TITUS sentences...")

    ok = 0
    weird = 0
    for t in titus:
        deva = titus_to_devanagari(t.text)
        # Check for leftover Latin consonants
        latin = [c for c in deva if c.isascii() and c.isalpha()
                 and c.lower() not in "aiueo "]
        if latin:
            weird += 1
            if weird <= 8:
                print(f"\n  [{t.book}.{t.chapter}.{t.sentence_num}]")
                print(f"  TITUS: {t.text[:150]}")
                print(f"  DEVA:  {deva[:150]}")
                print(f"  Latin left: {latin}")
        else:
            ok += 1

    print(f"\n{ok} clean, {weird} with leftover Latin chars")
