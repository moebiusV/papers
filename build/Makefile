# Build system — run from repo root via root Makefile
# All paths relative to ROOT (passed in by root Makefile)

ROOT          ?= $(abspath ..)
PANDOC        := pandoc
PDF_ENGINE    := xelatex
REFERENCE_DOC := $(ROOT)/build/templates/reference.docx

# --- paper.md index pages (one per subdirectory) --------------------------
PAPERS        := $(shell find $(ROOT)/papers -maxdepth 2 -name 'paper.md' | sort)
SLUGS         := $(patsubst $(ROOT)/papers/%/paper.md,%,$(PAPERS))
PDFS          := $(patsubst %,$(ROOT)/dist/%.pdf,$(SLUGS))
DOCXS         := $(patsubst %,$(ROOT)/dist/%.docx,$(SLUGS))

# --- named documents (.md and .html, excluding paper.md / README.md) ------
# entfesselt/ serves .md and .html directly; only 12hz-power-grid needs conversion
NAMED_MDS     := $(shell find $(ROOT)/papers -name '*.md' \
                   ! -name 'paper.md' ! -name 'README.md' \
                   ! -path '*/entfesselt/*' 2>/dev/null | sort)
HTML_SOURCES  := $(shell find $(ROOT)/papers -name '*.html' \
                   ! -path '*/entfesselt/*' 2>/dev/null | sort)

NAMED_PDFS    := $(patsubst $(ROOT)/papers/%.md,$(ROOT)/dist/%.pdf,$(NAMED_MDS)) \
                 $(patsubst $(ROOT)/papers/%.html,$(ROOT)/dist/%.pdf,$(HTML_SOURCES))
NAMED_DOCXS   := $(patsubst $(ROOT)/papers/%.md,$(ROOT)/dist/%.docx,$(NAMED_MDS)) \
                 $(patsubst $(ROOT)/papers/%.html,$(ROOT)/dist/%.docx,$(HTML_SOURCES))

# --- pre-built files with no source (frozen historical revisions) ---------
SRC_DOCX      := $(shell find $(ROOT)/papers -name '*.docx' 2>/dev/null)
SRC_PDF       := $(shell find $(ROOT)/papers -name '*.pdf'  2>/dev/null)

# --- pandoc flags ---------------------------------------------------------
PANDOC_PDF_FLAGS := \
	--pdf-engine=$(PDF_ENGINE) \
	--variable=geometry:margin=1in \
	--variable=fontsize:12pt \
	--variable=linestretch:1.3 \
	--variable=colorlinks:true \
	--variable=linkcolor:NavyBlue \
	--toc \
	--toc-depth=3 \
	--number-sections

PANDOC_DOCX_FLAGS := \
	--reference-doc=$(REFERENCE_DOC)

PANDOC_HTML_PDF_FLAGS := \
	--pdf-engine=$(PDF_ENGINE) \
	--variable=geometry:margin=1in \
	--variable=fontsize:11pt \
	--variable=linestretch:1.4 \
	-V mainfont="Liberation Serif" \
	-V sansfont="Liberation Sans" \
	-V monofont="Liberation Mono"

# --- targets --------------------------------------------------------------
.PHONY: all pdf docx named-docs list clean publish check abstract abstract-force abstract-private backup

all: pdf docx named-docs sync-sources

pdf: $(PDFS)

docx: $(DOCXS)

named-docs: $(NAMED_PDFS) $(NAMED_DOCXS)

# paper.md index pages → dist/<slug>.{pdf,docx}
$(ROOT)/dist/%.pdf: $(ROOT)/papers/%/paper.md $(REFERENCE_DOC) | $(ROOT)/dist
	@echo "  PDF  $*"
	@$(PANDOC) "$<" $(PANDOC_PDF_FLAGS) -o "$@"

$(ROOT)/dist/%.docx: $(ROOT)/papers/%/paper.md $(REFERENCE_DOC) | $(ROOT)/dist
	@echo "  DOCX $*"
	@$(PANDOC) "$<" $(PANDOC_DOCX_FLAGS) -o "$@"

# Named .md documents → dist/<slug>/<name>.{pdf,docx}
$(ROOT)/dist/%.pdf: $(ROOT)/papers/%.md | $(ROOT)/dist
	@mkdir -p $(dir $@)
	@echo "  PDF  $*.md"
	@$(PANDOC) "$<" $(PANDOC_PDF_FLAGS) -o "$@"

$(ROOT)/dist/%.docx: $(ROOT)/papers/%.md | $(ROOT)/dist
	@mkdir -p $(dir $@)
	@echo "  DOCX $*.md"
	@$(PANDOC) "$<" $(PANDOC_DOCX_FLAGS) -o "$@"

# Named .html documents → dist/<slug>/<name>.{pdf,docx}
$(ROOT)/dist/%.pdf: $(ROOT)/papers/%.html | $(ROOT)/dist
	@mkdir -p $(dir $@)
	@echo "  PDF  $*.html"
	@$(PANDOC) "$<" $(PANDOC_HTML_PDF_FLAGS) -o "$@"

$(ROOT)/dist/%.docx: $(ROOT)/papers/%.html | $(ROOT)/dist
	@mkdir -p $(dir $@)
	@echo "  DOCX $*.html"
	@$(PANDOC) "$<" -o "$@"

# Pre-built files with no source (e.g. frozen historical revisions)
sync-sources: | $(ROOT)/dist
	@for f in $(SRC_DOCX) $(SRC_PDF); do \
		rel="$${f#$(ROOT)/papers/}"; \
		dest="$(ROOT)/dist/$$rel"; \
		mkdir -p "$$(dirname $$dest)"; \
		cp -u "$$f" "$$dest" && echo "  COPY $$rel"; \
	done

$(ROOT)/dist:
	@mkdir -p $(ROOT)/dist

list:
	@echo "Papers:"
	@for slug in $(SLUGS); do echo "  $$slug"; done

check:
	@which pandoc  > /dev/null 2>&1 || (echo "ERROR: pandoc not found" && exit 1)
	@which xelatex > /dev/null 2>&1 || (echo "ERROR: xelatex not found" && exit 1)
	@echo "Build tools OK"

abstract:
	@newlisp $(ROOT)/build/scripts/generate-abstract.lsp $(ABSTRACT_FLAGS)

abstract-force:
	@newlisp $(ROOT)/build/scripts/generate-abstract.lsp --force $(ABSTRACT_FLAGS)

abstract-private:
	@newlisp $(ROOT)/build/scripts/generate-abstract.lsp --private $(ABSTRACT_FLAGS)

clean:
	rm -rf $(ROOT)/dist/

publish: all
	@cd $(ROOT) && \
		git add papers/ restricted/ dist/ build/ .gitignore README.md && \
		git diff --cached --quiet && echo "Nothing to publish." || \
		(git commit -m "Publish: $$(date '+%Y-%m-%d')" && \
		 git push origin main && \
		 echo "Published.")

backup:
	@cd $(ROOT)/private && \
		git add -A && \
		git diff --cached --quiet && echo "Private: nothing to backup." || \
		(git commit -m "Backup: $$(date '+%Y-%m-%d')" && \
		 git push private main && \
		 echo "Private papers backed up.")
