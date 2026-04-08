# Papers for Publication — Build System
# Usage:
#   make              — build all PDFs and DOCX
#   make pdf          — build PDFs only
#   make docx         — build DOCX only
#   make list         — show all papers
#   make clean        — remove dist/
#   make publish      — build, commit, and push

PAPERS   := $(shell find papers -maxdepth 2 -name 'paper.md' | sort)
SLUGS    := $(patsubst papers/%/paper.md,%,$(PAPERS))
PDFS     := $(patsubst %,dist/%.pdf,$(SLUGS))
DOCXS    := $(patsubst %,dist/%.docx,$(SLUGS))

# Source files (existing DOCX/PDF not built from markdown) — copied verbatim
SRC_DOCX := $(shell find papers -name '*.docx' -not -name 'paper.md' 2>/dev/null)
SRC_PDF  := $(shell find papers -name '*.pdf' 2>/dev/null)

PANDOC        := pandoc
PDF_ENGINE    := xelatex
REFERENCE_DOC := templates/reference.docx

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

.PHONY: all pdf docx list clean publish check abstract

all: pdf docx sync-sources

# Copy existing source DOCX/PDF files into dist/ preserving subdirectory structure
sync-sources: | dist
	@for f in $(SRC_DOCX) $(SRC_PDF); do \
		dest="dist/$${f#papers/}"; \
		mkdir -p "$$(dirname $$dest)"; \
		cp -u "$$f" "$$dest" && echo "  COPY $$f"; \
	done

pdf: $(PDFS)

docx: $(DOCXS)

dist/%.pdf: papers/%/paper.md $(REFERENCE_DOC) | dist
	@echo "  PDF  $*"
	@$(PANDOC) "$<" $(PANDOC_PDF_FLAGS) -o "$@"

dist/%.docx: papers/%/paper.md $(REFERENCE_DOC) | dist
	@echo "  DOCX $*"
	@$(PANDOC) "$<" $(PANDOC_DOCX_FLAGS) -o "$@"

dist:
	@mkdir -p dist

list:
	@echo "Papers:"
	@for slug in $(SLUGS); do echo "  $$slug"; done

check:
	@which pandoc   > /dev/null 2>&1 || (echo "ERROR: pandoc not found" && exit 1)
	@which xelatex  > /dev/null 2>&1 || (echo "ERROR: xelatex not found" && exit 1)
	@echo "Build tools OK"

abstract:
	@newlisp scripts/generate-abstract.lsp $(ABSTRACT_FLAGS)

abstract-force:
	@newlisp scripts/generate-abstract.lsp --force $(ABSTRACT_FLAGS)

abstract-private:
	@newlisp scripts/generate-abstract.lsp --private $(ABSTRACT_FLAGS)

clean:
	rm -rf dist/

# Build, commit everything (source + dist), and push public repo
publish: all
	@git add papers/ restricted/ dist/ templates/ Makefile .gitignore README scripts/
	@git diff --cached --quiet && echo "Nothing to publish." || \
		(git commit -m "Publish: $$(date '+%Y-%m-%d')" && \
		 git push origin main && \
		 echo "Published.")

# Commit and push the private repo
backup:
	@cd private && \
		git add -A && \
		git diff --cached --quiet && echo "Private: nothing to backup." || \
		(git commit -m "Backup: $$(date '+%Y-%m-%d')" && \
		 git push private main && \
		 echo "Private papers backed up.")
