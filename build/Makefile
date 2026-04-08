# Build system — run from repo root via root Makefile
# All paths relative to ROOT (passed in by root Makefile)

ROOT          ?= $(abspath ..)
PAPERS        := $(shell find $(ROOT)/papers -maxdepth 2 -name 'paper.md' | sort)
SLUGS         := $(patsubst $(ROOT)/papers/%/paper.md,%,$(PAPERS))
PDFS          := $(patsubst %,$(ROOT)/dist/%.pdf,$(SLUGS))
DOCXS         := $(patsubst %,$(ROOT)/dist/%.docx,$(SLUGS))

SRC_DOCX      := $(shell find $(ROOT)/papers -name '*.docx' 2>/dev/null)
SRC_PDF       := $(shell find $(ROOT)/papers -name '*.pdf'  2>/dev/null)

PANDOC        := pandoc
PDF_ENGINE    := xelatex
REFERENCE_DOC := $(ROOT)/build/templates/reference.docx

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

.PHONY: all pdf docx list clean publish check abstract abstract-force abstract-private backup

all: pdf docx sync-sources

sync-sources: | $(ROOT)/dist
	@for f in $(SRC_DOCX) $(SRC_PDF); do \
		rel="$${f#$(ROOT)/papers/}"; \
		dest="$(ROOT)/dist/$$rel"; \
		mkdir -p "$$(dirname $$dest)"; \
		cp -u "$$f" "$$dest" && echo "  COPY $$rel"; \
	done

pdf: $(PDFS)

docx: $(DOCXS)

$(ROOT)/dist/%.pdf: $(ROOT)/papers/%/paper.md $(REFERENCE_DOC) | $(ROOT)/dist
	@echo "  PDF  $*"
	@$(PANDOC) "$<" $(PANDOC_PDF_FLAGS) -o "$@"

$(ROOT)/dist/%.docx: $(ROOT)/papers/%/paper.md $(REFERENCE_DOC) | $(ROOT)/dist
	@echo "  DOCX $*"
	@$(PANDOC) "$<" $(PANDOC_DOCX_FLAGS) -o "$@"

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
