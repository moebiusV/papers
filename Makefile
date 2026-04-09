TARGETS := all pdf docx named-docs list clean publish check \
           abstract abstract-force abstract-private backup

.PHONY: $(TARGETS)
$(TARGETS):
	$(MAKE) -C build ROOT=$(CURDIR) $@
