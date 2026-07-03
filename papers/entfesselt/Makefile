# papers/entfesselt/Makefile — build config + file inventory
# Add or comment out files below to control what gets listed in README.
# All files served as-is (HTML/MD); no PDF/DOCX generation yet.
SLUG := entfesselt
ROOT ?= $(abspath ../..)

# ── Overview ──────────────────────────────────────────────────────────
OVERVIEW := paper.md

# ── Standard forms ────────────────────────────────────────────────────
STANDARD := \
	entfesselt-english.html \
	entfesselt-deutsch.html \

# ── Entfesselt (native-speaker restored forms) ────────────────────────
ENTFESSELT := \
	entfesselt-ent-english.html \
	entfesselt-ent-deutsch.html \
	entfesselt-ent-danish.html \
	entfesselt-ent-dutch.html \
	entfesselt-ent-icelandic.html \
	entfesselt-ent-nynorsk.html \
	entfesselt-ent-swedish.html \

# ── Specification sheets ──────────────────────────────────────────────
SPECS := \
	entfesselt-spec-three-column.html \
	entfesselt-spec-six-column.html \

# ── Demonstration texts ───────────────────────────────────────────────
DEMOS := \
	kafka-verwandlung.md \
	kafka-verwandlung-entfesselt.html \
	kleist-erdbeben.md \
	kleist-erdbeben-entfesselt.html \
	marx-manifest.md \
	marx-manifest-entfesselt.html \

# ── Supporting material ───────────────────────────────────────────────
SUPPORTING := \
	entfesselt-column.md \
	entfesselt-column.html \
	entfesselt-spec-english.md \
	entfesselt-state.md \
	dialogue-barcelona.md \
	dialogue-mozeson.md \

# ── All sources (concatenated in README order) ────────────────────────
SOURCES := \
	$(OVERVIEW) \
	$(STANDARD) \
	$(ENTFESSELT) \
	$(SPECS) \
	$(DEMOS) \
	$(SUPPORTING) \

# ── Build ─────────────────────────────────────────────────────────────
.PHONY: build pdf docx readme clean

build: pdf docx

pdf:
	@echo "  SKIP $(SLUG) — HTML/MD only, no PDF"

docx:
	@echo "  SKIP $(SLUG) — HTML/MD only, no DOCX"

readme:
	@SOURCES="$(STANDARD) $(ENTFESSELT) $(SPECS) $(DEMOS) $(SUPPORTING)" \
	 PDFS="" \
	 DOCXS="" \
	 $(ROOT)/build/scripts/generate-readme.sh "$(CURDIR)" "$(SLUG)" "$(ROOT)"

clean:
	@:
