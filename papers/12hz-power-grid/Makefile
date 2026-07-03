# papers/12hz-power-grid/Makefile — build config
# Engine: Pandoc (PDF + DOCX) for all .md and .html sources
SLUG := 12hz-power-grid
ROOT ?= $(abspath ../..)

PANDOC      := pandoc
PDF_ENGINE  := lualatex
HEADER      := $(ROOT)/build/templates/header.tex

PANDOC_PDF_FLAGS := \
	--pdf-engine=$(PDF_ENGINE) \
	--include-in-header=$(HEADER) \
	-V mainfont="Liberation Serif" \
	-V sansfont="Liberation Sans" \
	-V monofont="Liberation Mono" \
	--variable=geometry:margin=1in \
	--variable=fontsize:12pt \
	--variable=linestretch:1.3 \
	--variable=colorlinks:true \
	--variable=linkcolor:NavyBlue \
	--toc --toc-depth=3 --number-sections

PANDOC_HTML_FLAGS := \
	--pdf-engine=$(PDF_ENGINE) \
	--include-in-header=$(HEADER) \
	--variable=geometry:margin=1in \
	--variable=fontsize:11pt \
	--variable=linestretch:1.4 \
	-V mainfont="Liberation Serif" \
	-V sansfont="Liberation Sans" \
	-V monofont="Liberation Mono"

# paper.md → dist/<slug>.pdf + .docx
PAPER_MD  := paper.md
INDEX_PDF  := $(ROOT)/dist/$(SLUG).pdf
INDEX_DOCX := $(ROOT)/dist/$(SLUG).docx

# Named .md files (not paper.md, not README.md)
NAMED_MD := $(filter-out paper.md README.md,$(wildcard *.md))
MD_PDF   := $(patsubst %.md,$(ROOT)/dist/$(SLUG)/%.pdf,$(NAMED_MD))
MD_DOCX  := $(patsubst %.md,$(ROOT)/dist/$(SLUG)/%.docx,$(NAMED_MD))

# Named .html files
HTML_SRC := $(wildcard *.html)
HTML_PDF := $(patsubst %.html,$(ROOT)/dist/$(SLUG)/%.pdf,$(HTML_SRC))
HTML_DOCX := $(patsubst %.html,$(ROOT)/dist/$(SLUG)/%.docx,$(HTML_SRC))

# Pre-built files (frozen revisions with no source, just copy to dist/)
PREBUILT := $(wildcard *.docx *.pdf)

ALL_PDF  := $(INDEX_PDF)  $(MD_PDF)  $(HTML_PDF)
ALL_DOCX := $(INDEX_DOCX) $(MD_DOCX) $(HTML_DOCX)

.PHONY: build pdf docx clean readme

build: pdf docx sync-prebuilt

pdf: $(ALL_PDF)

docx: $(ALL_DOCX)

# paper.md → dist/<slug>.pdf + .docx
$(INDEX_PDF): $(PAPER_MD) $(HEADER)
	@mkdir -p $(dir $@)
	@echo "  PDF  $(SLUG)"
	@$(PANDOC) $< $(PANDOC_PDF_FLAGS) -o $@

$(INDEX_DOCX): $(PAPER_MD)
	@mkdir -p $(dir $@)
	@echo "  DOCX $(SLUG)"
	@$(PANDOC) $< -o $@

# Named .md → dist/<slug>/<name>.pdf + .docx
$(ROOT)/dist/$(SLUG)/%.pdf: %.md $(HEADER)
	@mkdir -p $(dir $@)
	@echo "  PDF  $(SLUG)/$*"
	@$(PANDOC) $< $(PANDOC_PDF_FLAGS) -o $@

$(ROOT)/dist/$(SLUG)/%.docx: %.md
	@mkdir -p $(dir $@)
	@echo "  DOCX $(SLUG)/$*"
	@$(PANDOC) $< -o $@

# Named .html → dist/<slug>/<name>.pdf + .docx
$(ROOT)/dist/$(SLUG)/%.pdf: %.html $(HEADER)
	@mkdir -p $(dir $@)
	@echo "  PDF  $(SLUG)/$*"
	@$(PANDOC) $< $(PANDOC_HTML_FLAGS) -o $@

$(ROOT)/dist/$(SLUG)/%.docx: %.html
	@mkdir -p $(dir $@)
	@echo "  DOCX $(SLUG)/$*"
	@$(PANDOC) $< -o $@

# Pre-built files — copy to dist/
sync-prebuilt: $(PREBUILT)
	@for f in $(PREBUILT); do \
		dest="$(ROOT)/dist/$(SLUG)/$$f"; \
		mkdir -p $$(dirname $$dest); \
		cp -u $$f $$dest && echo "  COPY $(SLUG)/$$f"; \
	done

clean:
	rm -rf $(ROOT)/dist/$(SLUG)/ $(INDEX_PDF) $(INDEX_DOCX)

readme:
	@echo "  SKIP $(SLUG) — README not yet auto-generated"
