# papers/viking-poets/Makefile
# Each entry in the lists below appears in README.
# Files not listed here are not built and not linked.
SLUG := viking-poets
ROOT ?= $(abspath ../..)

# ── Publication outputs ───────────────────────────────────────────────
#     name:     basename in dist/ (without extension)
#     formats:  pdf docx — both always generated together
OUTPUT        := $(SLUG)
OUTPUT_FORMATS := pdf docx

PDF  := $(ROOT)/dist/$(OUTPUT).pdf
DOCX := $(ROOT)/dist/$(OUTPUT).docx

# ── Source files ──────────────────────────────────────────────────────
#     Each file is a master source listed in README.
#     Title is taken from the file's H1 heading.
CHAPTERS := \
	chapters/00_introduction_the_wrong_question.md \
	chapters/01_chapter_1_intelligence_needs_bodies.md \
	chapters/02_chapter_2_the_scroll_that_doesnt_change.md \
	chapters/03_chapter_3_what_the_viking_poets_knew.md \
	chapters/04_chapter_4_the_room_that_remembers.md \
	chapters/05_chapter_5_the_adversarial_problem.md \
	chapters/06_chapter_6_what_the_meditators_knew.md \
	chapters/07_conclusion_the_incorruptible_manuscript.md \

# ── Build tools (listed in README but not built themselves) ──────────
BOOK_TYP := book.typ

# ── Build ─────────────────────────────────────────────────────────────
TYPST  := typst
PANDOC := pandoc

.PHONY: build pdf docx readme clean

build: pdf docx

pdf: $(PDF)

docx: $(DOCX)

$(PDF): $(BOOK_TYP) $(CHAPTERS)
	@mkdir -p $(dir $@)
	@echo "  TYPST $(SLUG)"
	@$(TYPST) compile $(BOOK_TYP) $@

$(DOCX): $(CHAPTERS)
	@mkdir -p $(dir $@)
	@echo "  DOCX $(SLUG)"
	@cat $(CHAPTERS) | $(PANDOC) -o $@

readme:
	@SOURCES="$(CHAPTERS)" \
	 PDFS="$(PDF)" \
	 DOCXS="$(DOCX)" \
	 BUILDS="$(BOOK_TYP) Makefile build.sh" \
	 $(ROOT)/build/scripts/generate-readme.sh "$(CURDIR)" "$(SLUG)" "$(ROOT)"

clean:
	rm -f $(PDF) $(DOCX)
