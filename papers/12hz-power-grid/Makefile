# papers/12hz-power-grid/Makefile — build config + file inventory
# Only latest revisions listed. Add or comment out files below.
SLUG := 12hz-power-grid
ROOT ?= $(abspath ../..)

# ── Outputs ───────────────────────────────────────────────────────────
#   paper.md builds to <slug>.pdf + .docx (the overview, in this directory)
OVERVIEW_PDF  := $(SLUG).pdf
OVERVIEW_DOCX := $(SLUG).docx

# ── Reports (latest revision only) ────────────────────────────────────
#   Each .md or .html builds to dist/<slug>/<name>.pdf + .docx
REPORTS := \
	12Hz_AC_vs_DC_Grid_Technical_Annex_Rev11.md \
	12Hz_Commodity_Steel_Transformers_White_Paper_Rev5.md \
	12Hz_Executive_Summary_EN.md \
	12Hz_Field_Guide_Electricians.html \
	12Hz_Grid_Transition_Plan_Rev2.md \
	12Hz_Large_Transformer_Architecture_Rev2.md \

REPORTS_MD   := $(filter %.md,$(REPORTS))
REPORTS_HTML := $(filter %.html,$(REPORTS))
REPORTS_PDF  := $(patsubst %.md,%.pdf,$(REPORTS_MD)) \
                $(patsubst %.html,%.pdf,$(REPORTS_HTML))
REPORTS_DOCX := $(patsubst %.md,%.docx,$(REPORTS_MD)) \
                $(patsubst %.html,%.docx,$(REPORTS_HTML))

# ── Frozen revisions (pre-built, no source — copy to dist/) ──────────
PREBUILT := \
	12Hz_Commodity_Steel_Transformers_White_Paper_Rev2.docx \
	12Hz_Commodity_Steel_Transformers_White_Paper_Rev2.pdf \

# ── Build ─────────────────────────────────────────────────────────────
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

ALL_PDF  := $(OVERVIEW_PDF)  $(REPORTS_PDF)
ALL_DOCX := $(OVERVIEW_DOCX) $(REPORTS_DOCX)

.PHONY: build pdf docx clean readme

build: pdf docx sync-prebuilt

pdf: $(ALL_PDF)

docx: $(ALL_DOCX)

# Overview: paper.md → <slug>.pdf + .docx
$(OVERVIEW_PDF): paper.md $(HEADER)
	@echo "  PDF  $(SLUG)"
	@$(PANDOC) $< $(PANDOC_PDF_FLAGS) -o $@

$(OVERVIEW_DOCX): paper.md
	@echo "  DOCX $(SLUG)"
	@$(PANDOC) $< -o $@

# Reports: each .md/.html → same-name .pdf + .docx (in this directory)
%.pdf: %.md $(HEADER)
	@echo "  PDF  $*"
	@$(PANDOC) $< $(PANDOC_PDF_FLAGS) -o $@

%.docx: %.md
	@echo "  DOCX $*"
	@$(PANDOC) $< -o $@

%.pdf: %.html $(HEADER)
	@echo "  PDF  $*"
	@$(PANDOC) $< $(PANDOC_HTML_FLAGS) -o $@

%.docx: %.html
	@echo "  DOCX $*"
	@$(PANDOC) $< -o $@

# Pre-built files (frozen revisions) — already in this directory
sync-prebuilt:
	@echo "  COPY $(SLUG) pre-built files already in place"

clean:
	rm -f $(OVERVIEW_PDF) $(OVERVIEW_DOCX) $(REPORTS_PDF) $(REPORTS_DOCX)

readme:
	@SOURCES="$(REPORTS)" \
	 PDFS="$(OVERVIEW_PDF) $(REPORTS_PDF)" \
	 DOCXS="$(OVERVIEW_DOCX) $(REPORTS_DOCX)" \
	 $(ROOT)/build/scripts/generate-readme.sh "$(CURDIR)" "$(SLUG)" "$(ROOT)"
