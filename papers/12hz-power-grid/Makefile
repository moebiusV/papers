# papers/12hz-power-grid/Makefile — build config + file inventory
# Add or comment out files below to control what gets built and listed in README.
SLUG := 12hz-power-grid
ROOT ?= $(abspath ../..)

# ── Sources ───────────────────────────────────────────────────────────
#   Each .md or .html builds to same-name .pdf + .docx
SOURCES := \
	12Hz_AC_vs_DC_Grid_Technical_Annex_Rev11.md \
	12Hz_Commodity_Steel_Transformers_White_Paper_Rev5.md \
	12Hz_Executive_Summary_EN.md \
	12Hz_Field_Guide_Electricians.html \
	12Hz_Grid_Transition_Plan_Rev2.md \
	12Hz_Large_Transformer_Architecture_Rev2.md \

SOURCES_MD   := $(filter %.md,$(SOURCES))
SOURCES_HTML := $(filter %.html,$(SOURCES))
PDFS  := $(patsubst %.md,%.pdf,$(SOURCES_MD)) \
         $(patsubst %.html,%.pdf,$(SOURCES_HTML))
DOCXS := $(patsubst %.md,%.docx,$(SOURCES_MD)) \
         $(patsubst %.html,%.docx,$(SOURCES_HTML))

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

.PHONY: build pdf docx readme clean

build: pdf docx

pdf: $(PDFS)

docx: $(DOCXS)

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

readme:
	@SOURCES="$(SOURCES)" \
	 PDFS="$(PDFS)" \
	 DOCXS="$(DOCXS)" \
	 $(ROOT)/build/scripts/generate-readme.sh "$(CURDIR)" "$(SLUG)" "$(ROOT)"

clean:
	rm -f $(PDFS) $(DOCXS)
