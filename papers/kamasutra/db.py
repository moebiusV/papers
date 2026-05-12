#!/usr/bin/env python3
"""SQLite database for the Kama Sutra three-way edition.

Schema: one row per TITUS sentence, with columns for all three witnesses,
per-model repairs, commentary (future), translations (future), and audit trail.
"""

import sqlite3
import re
from pathlib import Path
from typing import Optional

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "work" / "kamasutra.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sentences (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    book            INTEGER NOT NULL,
    chapter         INTEGER NOT NULL,
    sentence        INTEGER NOT NULL,

    -- TITUS digital edition
    titus_roman     TEXT,           -- Roman transliteration with diacritics
    titus_deva      TEXT,           -- Devanagari transliteration (rule-based)
    titus_page      INTEGER,        -- printed edition page number from TITUS

    -- 2001 edition (Hindi commentary)
    text_2001_raw   TEXT,           -- raw OCR Devanagari
    page_2001       INTEGER,        -- PDF page number
    text_2001_grok      TEXT,       -- Grok de-artifacted Devanagari
    text_2001_deepseek  TEXT,       -- DeepSeek de-artifacted Devanagari

    -- 1929 edition (Jayamangala Sanskrit commentary)
    text_1929_raw   TEXT,           -- raw OCR Devanagari
    page_1929       INTEGER,        -- PDF page number
    text_1929_grok      TEXT,       -- Grok de-artifacted Devanagari
    text_1929_deepseek  TEXT,       -- DeepSeek de-artifacted Devanagari

    -- Alignment metadata
    confidence      REAL,           -- 0.0–1.0 alignment confidence
    flags           TEXT,           -- comma-separated discrepancy flags

    -- Per-model repair outputs (for comparison)
    repair_deepseek         TEXT,   -- DeepSeek corrected Devanagari
    repair_deepseek_reason  TEXT,   -- DeepSeek reasoning
    repair_sonnet           TEXT,   -- Sonnet corrected Devanagari
    repair_sonnet_reason    TEXT,   -- Sonnet reasoning
    repair_opus             TEXT,   -- Opus corrected Devanagari
    repair_opus_reason      TEXT,   -- Opus reasoning

    -- Final selected reading
    corrected_deva   TEXT,          -- best Devanagari after review
    repair_model     TEXT,          -- which model's reading was selected
    repair_reasoning TEXT,          -- why this reading was chosen

    -- Commentary (extracted from OCR, separated from root sutra — future)
    commentary_2001  TEXT,          -- Hindi commentary from 2001 edition
    commentary_1929  TEXT,          -- Jayamangala Sanskrit from 1929 edition

    -- Translations (future)
    translation_2001_en TEXT,       -- English of 2001 edition
    translation_1929_en TEXT,       -- English of 1929 edition

    -- Audit trail
    reviewed_by      TEXT,          -- human review marker
    review_notes     TEXT,          -- human review notes

    UNIQUE(book, chapter, sentence)
);

CREATE INDEX IF NOT EXISTS idx_sentences_ref
    ON sentences(book, chapter, sentence);

CREATE INDEX IF NOT EXISTS idx_sentences_flags
    ON sentences(flags)
    WHERE flags IS NOT NULL AND flags != 'clean';

-- View: rows needing repair by DeepSeek (flagged, not yet processed)
CREATE VIEW IF NOT EXISTS needs_repair_deepseek AS
    SELECT id, book, chapter, sentence, titus_roman,
           text_2001_raw, text_1929_raw, flags, confidence
    FROM sentences
    WHERE flags IS NOT NULL
      AND flags != 'clean'
      AND repair_deepseek IS NULL
      AND (text_2001_raw IS NOT NULL OR text_1929_raw IS NOT NULL);

-- View: rows needing repair by Sonnet (DeepSeek done, Sonnet not yet)
CREATE VIEW IF NOT EXISTS needs_repair_sonnet AS
    SELECT id, book, chapter, sentence, titus_roman,
           text_2001_raw, text_1929_raw, flags, confidence
    FROM sentences
    WHERE flags IS NOT NULL
      AND flags != 'clean'
      AND repair_deepseek IS NOT NULL
      AND repair_sonnet IS NULL
      AND (text_2001_raw IS NOT NULL OR text_1929_raw IS NOT NULL);

-- View: rows ready for translation (aligned + at least one repair)
CREATE VIEW IF NOT EXISTS ready_for_translation AS
    SELECT id, book, chapter, sentence, titus_roman,
           COALESCE(corrected_deva, repair_deepseek, text_2001_raw) AS text_2001_final,
           COALESCE(corrected_deva, repair_deepseek, text_1929_raw) AS text_1929_final,
           confidence
    FROM sentences
    WHERE titus_roman IS NOT NULL;

-- View: clean matches (all three witnesses agree, no flags)
CREATE VIEW IF NOT EXISTS clean_matches AS
    SELECT id, book, chapter, sentence, titus_roman,
           text_2001_raw, text_1929_raw, confidence
    FROM sentences
    WHERE flags IS NULL OR flags = 'clean';
"""


def get_db(path: Optional[Path] = None) -> sqlite3.Connection:
    """Open the database, creating it with schema if needed."""
    db_path = path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)

    # ── Migrations: add columns that may not exist in older DBs ──
    migrations = [
        "ALTER TABLE sentences ADD COLUMN text_2001_grok TEXT",
        "ALTER TABLE sentences ADD COLUMN text_2001_deepseek TEXT",
        "ALTER TABLE sentences ADD COLUMN text_1929_grok TEXT",
        "ALTER TABLE sentences ADD COLUMN text_1929_deepseek TEXT",
        "ALTER TABLE sentences ADD COLUMN titus_deva TEXT",
    ]
    for m in migrations:
        try:
            conn.execute(m)
        except sqlite3.OperationalError:
            pass  # column already exists

    conn.commit()
    return conn


def upsert_sentence(conn: sqlite3.Connection, row: dict) -> None:
    """Insert or update a sentence row. 'row' is a dict with column keys."""
    col_map = {
        "book": "book",
        "chapter": "chapter",
        "sentence": "sentence",
        "titus_roman": "titus_roman",
        "titus_deva": "titus_deva",
        "titus_page": "titus_page",
        "text_2001_raw": "text_2001_raw",
        "page_2001": "page_2001",
        "text_2001_grok": "text_2001_grok",
        "text_2001_deepseek": "text_2001_deepseek",
        "text_1929_raw": "text_1929_raw",
        "page_1929": "page_1929",
        "text_1929_grok": "text_1929_grok",
        "text_1929_deepseek": "text_1929_deepseek",
        "confidence": "confidence",
        "flags": "flags",
        "corrected_deva": "corrected_deva",
        "repair_model": "repair_model",
        "repair_reasoning": "repair_reasoning",
        "repair_deepseek": "repair_deepseek",
        "repair_deepseek_reason": "repair_deepseek_reason",
        "repair_sonnet": "repair_sonnet",
        "repair_sonnet_reason": "repair_sonnet_reason",
        "repair_opus": "repair_opus",
        "repair_opus_reason": "repair_opus_reason",
        "commentary_2001": "commentary_2001",
        "commentary_1929": "commentary_1929",
        "translation_2001_en": "translation_2001_en",
        "translation_1929_en": "translation_1929_en",
        "reviewed_by": "reviewed_by",
        "review_notes": "review_notes",
    }

    db_cols = {}
    for src_key, db_key in col_map.items():
        if src_key in row and row[src_key] is not None:
            db_cols[db_key] = row[src_key]

    if not db_cols:
        return

    # Extract book/chapter/sentence from titus_ref if not present
    if "book" not in db_cols and "titus_ref" in row:
        ref = row["titus_ref"]
        m = re.match(r"(\d+)\.(\d+)\.(\d+)", str(ref))
        if m:
            db_cols["book"] = int(m.group(1))
            db_cols["chapter"] = int(m.group(2))
            db_cols["sentence"] = int(m.group(3))

    if "book" not in db_cols:
        return

    columns = ", ".join(db_cols.keys())
    placeholders = ", ".join("?" for _ in db_cols)
    values = list(db_cols.values())

    sql = f"""
        INSERT INTO sentences ({columns})
        VALUES ({placeholders})
        ON CONFLICT(book, chapter, sentence) DO UPDATE SET
            {", ".join(f"{k}=excluded.{k}" for k in db_cols if k not in ('book', 'chapter', 'sentence'))}
    """
    conn.execute(sql, values)
    conn.commit()


def insert_alignment_rows(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """Insert all alignment rows into the database. Returns count inserted."""
    count = 0
    for row in rows:
        db_row = {
            "titus_ref": row.get("titus_ref", ""),
            "titus_roman": row.get("titus_text", ""),
            "titus_page": int(row.get("titus_page", 0)),
            "text_2001_raw": row.get("text_2001", ""),
            "page_2001": int(row.get("page_2001", 0)),
            "text_1929_raw": row.get("text_1929", ""),
            "page_1929": int(row.get("page_1929", 0)),
            "confidence": float(row.get("confidence", row.get("conf", 0))),
            "flags": row.get("flags", ""),
        }
        upsert_sentence(conn, db_row)
        count += 1
    return count


# ── Query helpers ───────────────────────────────────────────────────────────

def count_flagged(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM sentences WHERE flags IS NOT NULL AND flags != 'clean'"
    ).fetchone()[0]


def count_clean(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM sentences WHERE flags IS NULL OR flags = 'clean'"
    ).fetchone()[0]


def summary(conn: sqlite3.Connection) -> dict:
    """Return a summary dict of the database state."""
    return {
        "total_sentences": conn.execute("SELECT COUNT(*) FROM sentences").fetchone()[0],
        "clean": count_clean(conn),
        "flagged": count_flagged(conn),
        "needs_repair_ds": conn.execute("SELECT COUNT(*) FROM needs_repair_deepseek").fetchone()[0],
        "needs_repair_sonnet": conn.execute("SELECT COUNT(*) FROM needs_repair_sonnet").fetchone()[0],
        "repaired_ds": conn.execute(
            "SELECT COUNT(*) FROM sentences WHERE repair_deepseek IS NOT NULL"
        ).fetchone()[0],
        "repaired_sonnet": conn.execute(
            "SELECT COUNT(*) FROM sentences WHERE repair_sonnet IS NOT NULL"
        ).fetchone()[0],
        "repaired_opus": conn.execute(
            "SELECT COUNT(*) FROM sentences WHERE repair_opus IS NOT NULL"
        ).fetchone()[0],
        "books": [row[0] for row in conn.execute(
            "SELECT DISTINCT book FROM sentences ORDER BY book"
        ).fetchall()],
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Kama Sutra SQLite database management")
    ap.add_argument("--init", action="store_true", help="Initialize the database")
    ap.add_argument("--summary", action="store_true", help="Print database summary")
    ap.add_argument("--import-tsv", type=str, help="Import alignment TSV into database")
    args = ap.parse_args()

    conn = get_db()

    if args.init:
        print(f"Database initialized: {DB_PATH}")

    if args.import_tsv:
        tsv_path = Path(args.import_tsv)
        if not tsv_path.exists():
            print(f"TSV not found: {tsv_path}")
            return

        with open(tsv_path, encoding="utf-8") as f:
            header = f.readline().rstrip("\n").split("\t")
            rows = []
            for line in f:
                if not line.strip():
                    continue
                fields = line.rstrip("\n").split("\t")
                rows.append(dict(zip(header, fields)))

        count = insert_alignment_rows(conn, rows)
        print(f"Imported {count} rows from {tsv_path}")

    if args.summary:
        s = summary(conn)
        print(f"Database: {DB_PATH}")
        print(f"Total sentences: {s['total_sentences']}")
        print(f"Clean (all agree): {s['clean']}")
        print(f"Flagged (discrepancy): {s['flagged']}")
        print(f"Needs repair (DeepSeek): {s['needs_repair_ds']}")
        print(f"Needs repair (Sonnet): {s['needs_repair_sonnet']}")
        print(f"Repaired (DeepSeek): {s['repaired_ds']}")
        print(f"Repaired (Sonnet): {s['repaired_sonnet']}")
        print(f"Repaired (Opus): {s['repaired_opus']}")
        print(f"Books: {s['books']}")

    conn.close()


if __name__ == "__main__":
    main()
