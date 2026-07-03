# Papers for Publication — decentralized build
# Each papers/<slug>/Makefile defines its own build rules.
# Add or comment out directories below to control what gets built and published.
ROOT := $(abspath .)

SUBDIRS := \
	12hz-power-grid \
	entfesselt \
	viking-poets \

.PHONY: all pdf docx readme clean list publish check

all: pdf docx

pdf docx readme:
	@for dir in $(SUBDIRS); do \
		$(MAKE) -C papers/$$dir ROOT=$(ROOT) $@ 2>/dev/null || true; \
	done

list:
	@for dir in $(SUBDIRS); do echo "  $$dir"; done

check:
	@which typst  >/dev/null 2>&1 || echo "WARNING: typst not found (some papers need it)"
	@which pandoc >/dev/null 2>&1 || echo "WARNING: pandoc not found (some papers need it)"
	@echo "Build tools checked."

clean:
	@for dir in $(SUBDIRS); do \
		$(MAKE) -C papers/$$dir ROOT=$(ROOT) clean 2>/dev/null || true; \
	done

publish: all
	@git add $(patsubst %,papers/%,$(SUBDIRS)) \
	         .gitignore README.md
	@git diff --cached --quiet && echo "Nothing to publish." || \
		(git commit -m "Publish: $$(date '+%Y-%m-%d')" && \
		 git push origin main && \
		 echo "Published.")
