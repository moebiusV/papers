# papers/viking-poets/Makefile — build config + file inventory
# Add or comment out entries below to control what gets built and listed.
SLUG := viking-poets
ROOT ?= $(abspath ../..)

# ── Manifest ──────────────────────────────────────────────────────────
#   Format:  sources... -> output  :engine
#   sources -> output   build PDF+DOCX from one or more source files
#   file                listed in README as-is (no PDF/DOCX generated)
#   engine:  typst (default) or pandoc
#
OUTPUT := $(SLUG)
ENGINE := typst

CHAPTERS := \
	chapters/00_introduction_the_wrong_question.md \
	chapters/01_chapter_1_intelligence_needs_bodies.md \
	chapters/02_chapter_2_the_scroll_that_doesnt_change.md \
	chapters/03_chapter_3_what_the_controllers_knew.md \
	chapters/04_chapter_4_what_the_viking_poets_knew.md \
	chapters/04a_interlude_on_beauty.md \
	chapters/05_chapter_5_the_room_that_remembers.md \
	chapters/06_chapter_6_the_adversarial_problem.md \
	chapters/07_chapter_7_what_the_meditators_knew.md \
	chapters/08_conclusion_the_incorruptible_manuscript.md \
	chapters/09_appendix_the_recovered_word.md \
	chapters/10_appendix_2_building_the_stack_in_silicon.md \
	chapters/blurb_jacket_copy.md \

BOOK_TYP := book.typ

# ── Build ─────────────────────────────────────────────────────────────
TYPST  := typst
PANDOC := pandoc

PDF  := $(OUTPUT).pdf
DOCX := $(OUTPUT).docx

.PHONY: build pdf docx readme clean

build: pdf docx

pdf: $(PDF)

docx: $(DOCX)

$(PDF): $(BOOK_TYP) $(CHAPTERS)
	@echo "  TYPST $(SLUG)"
	@$(TYPST) compile $(BOOK_TYP) $@

$(DOCX): $(CHAPTERS)
	@echo "  DOCX $(SLUG)"
	@cat $(CHAPTERS) | $(PANDOC) -o $@

readme:
	@SOURCES="$(CHAPTERS)" \
	 PDFS="$(PDF)" \
	 DOCXS="$(DOCX)" \
	 $(ROOT)/build/scripts/generate-readme.sh "$(CURDIR)" "$(SLUG)" "$(ROOT)"

clean:
	rm -f $(PDF) $(DOCX)
