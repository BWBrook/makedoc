SHELL := /bin/bash

PANDOC ?= pandoc
PDF_ENGINE ?= xelatex
PANDOC_FROM ?= markdown+tex_math_dollars+tex_math_single_backslash

SRC ?= manuscript/text/draft_ms_v2.md
BIB ?= references/ih_references.yaml
CSL ?= csl/oikos.csl

DIST ?= dist
PDF_OUT ?= $(DIST)/manuscript.pdf
DOCX_OUT ?= $(DIST)/manuscript.docx

PANDOC_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(BIB) --csl $(CSL)

.PHONY: all pdf docx check-tools check clean

all: pdf docx

pdf: $(PDF_OUT)

docx: $(DOCX_OUT)

$(DIST):
	mkdir -p $(DIST)

$(PDF_OUT): $(SRC) $(BIB) $(CSL) | $(DIST)
	$(PANDOC) $(SRC) $(PANDOC_COMMON) --pdf-engine=$(PDF_ENGINE) -o $@

$(DOCX_OUT): $(SRC) $(BIB) $(CSL) | $(DIST)
	$(PANDOC) $(SRC) $(PANDOC_COMMON) -o $@

check-tools:
	@for cmd in "$(PANDOC)" "$(PDF_ENGINE)"; do \
		command -v "$$cmd" >/dev/null 2>&1 || { echo "Missing required tool: $$cmd"; exit 1; }; \
	done
	@echo "Tool check passed."

check: check-tools
	@$(MAKE) --no-print-directory all
	@echo "Build check passed."

clean:
	rm -rf $(DIST)
