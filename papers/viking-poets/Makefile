# papers/viking-poets/Makefile — build config + file inventory
# Pipeline: markdown -> buildabook -> typst -> PDF
SLUG := viking-poets
ROOT ?= $(abspath ../..)

OUTPUT := $(SLUG)
ENGINE := typst

# ── Manifest ──────────────────────────────────────────────────────────
#   Format:  sources... -> output  :engine
#   sources -> output   build the PDF from one or more source files
#   file                listed in README as-is (no PDF generated)
#   engine:  typst
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

BOOK_TYP := book.header.typ
BOOK_HTML_TYP := book.html.typ

# ── Build ─────────────────────────────────────────────────────────────
TYPST := typst

PDF := $(OUTPUT).pdf
HTML := $(OUTPUT).html

.PHONY: build pdf html cover readme clean

build: pdf html cover

pdf: $(PDF)

html: $(HTML)

$(PDF): $(BOOK_TYP) $(CHAPTERS) outline.txt filemap.txt book.conf
	@echo "  BUILDABOOK $(SLUG)"
	@buildabook pdf

$(HTML): $(BOOK_HTML_TYP) $(CHAPTERS) outline.txt filemap.txt book.conf
	@echo "  BUILDABOOK HTML $(SLUG)"
	@buildabook html

cover: $(PDF)
	@echo "  BUILDABOOK COVER $(SLUG)"
	@buildabook cover

readme:
	@echo "  BUILDABOOK README $(SLUG)"
	@buildabook readme

clean:
	rm -f $(PDF) $(HTML)
