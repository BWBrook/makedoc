SHELL := /bin/bash

PANDOC ?= pandoc
PDF_ENGINE ?= xelatex
PANDOC_FROM ?= markdown+tex_math_dollars+tex_math_single_backslash

SRC_MAIN ?= manuscript/text/draft_ms_v2.md
SRC_FIGS ?= manuscript/text/figure_captions_v2.md
SRC_FILES ?= $(SRC_MAIN) $(SRC_FIGS)
LINT_SRCS ?= $(SRC_FILES)
BIB ?= references/ih_references.yaml
CSL ?= csl/oikos.csl
REFS_AUDIT ?= scripts/refs_audit.py

DIST ?= dist
PDF_OUT ?= $(DIST)/manuscript.pdf
DOCX_OUT ?= $(DIST)/manuscript.docx

PANDOC_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(BIB) --csl $(CSL)

.PHONY: all pdf docx check-tools lint-manuscript refs-audit check clean

all: pdf docx

pdf: $(PDF_OUT)

docx: $(DOCX_OUT)

$(DIST):
	mkdir -p $(DIST)

$(PDF_OUT): $(SRC_FILES) $(BIB) $(CSL) $(REFS_AUDIT) | $(DIST)
	$(PANDOC) $(SRC_FILES) $(PANDOC_COMMON) --pdf-engine=$(PDF_ENGINE) -o $@

$(DOCX_OUT): $(SRC_FILES) $(BIB) $(CSL) $(REFS_AUDIT) | $(DIST)
	$(PANDOC) $(SRC_FILES) $(PANDOC_COMMON) -o $@

check-tools:
	@for cmd in "$(PANDOC)" "$(PDF_ENGINE)"; do \
		command -v "$$cmd" >/dev/null 2>&1 || { echo "Missing required tool: $$cmd"; exit 1; }; \
	done
	@echo "Tool check passed."

lint-manuscript:
	@status=0; \
	echo "Running manuscript lint checks..."; \
	if rg -n '\[REF\]' $(LINT_SRCS); then \
		echo "Error: unresolved placeholder [REF] found."; \
		status=1; \
	fi; \
	tmp_manual="$$(mktemp)"; \
	rg -n '\([^)]*(19|20)[0-9]{2}[a-z]?[^)]*\)' $(LINT_SRCS) | rg -v '\[@' > "$$tmp_manual" || true; \
	if [ -s "$$tmp_manual" ]; then \
		echo "Error: possible manual author-year citations remain (convert to Pandoc citekeys)."; \
		cat "$$tmp_manual"; \
		status=1; \
	fi; \
	rm -f "$$tmp_manual"; \
	if [ "$$status" -eq 0 ]; then \
		echo "Manuscript lint passed."; \
	fi; \
	exit "$$status"

refs-audit:
	@echo "Running reference audit..."
	@args=(); \
	for src in $(SRC_FILES); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(REFS_AUDIT)" --bibliography "$(BIB)" "$${args[@]}"

check: check-tools lint-manuscript refs-audit
	@$(MAKE) --no-print-directory all
	@echo "Build check passed."

clean:
	rm -rf $(DIST)
