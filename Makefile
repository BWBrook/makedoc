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

FIXTURE_SRC_MAIN ?= testbed/manuscript/text/fixture_main.md
FIXTURE_SRC_FIGS ?= testbed/manuscript/text/fixture_figures.md
FIXTURE_SRC_FILES ?= $(FIXTURE_SRC_MAIN) $(FIXTURE_SRC_FIGS)
FIXTURE_LINT_SRCS ?= $(FIXTURE_SRC_FILES)
FIXTURE_BIB ?= testbed/references/fixture_refs.yaml
FIXTURE_CSL ?= testbed/csl/fixture_style.csl
FIXTURE_DIST ?= $(DIST)/testbed
FIXTURE_PDF_OUT ?= $(FIXTURE_DIST)/fixture_manuscript.pdf
FIXTURE_DOCX_OUT ?= $(FIXTURE_DIST)/fixture_manuscript.docx

PANDOC_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(BIB) --csl $(CSL)
FIXTURE_PANDOC_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(FIXTURE_BIB) --csl $(FIXTURE_CSL)

.PHONY: all pdf docx fixture-all fixture-pdf fixture-docx check-tools lint-manuscript refs-audit fixture-lint fixture-refs-audit check check-fixture clean

all: pdf docx

pdf: $(PDF_OUT)

docx: $(DOCX_OUT)

fixture-all: fixture-pdf fixture-docx

fixture-pdf: $(FIXTURE_PDF_OUT)

fixture-docx: $(FIXTURE_DOCX_OUT)

$(DIST):
	mkdir -p $(DIST)

$(FIXTURE_DIST):
	mkdir -p $(FIXTURE_DIST)

$(PDF_OUT): $(SRC_FILES) $(BIB) $(CSL) $(REFS_AUDIT) | $(DIST)
	$(PANDOC) $(SRC_FILES) $(PANDOC_COMMON) --pdf-engine=$(PDF_ENGINE) -o $@

$(DOCX_OUT): $(SRC_FILES) $(BIB) $(CSL) $(REFS_AUDIT) | $(DIST)
	$(PANDOC) $(SRC_FILES) $(PANDOC_COMMON) -o $@

$(FIXTURE_PDF_OUT): $(FIXTURE_SRC_FILES) $(FIXTURE_BIB) $(FIXTURE_CSL) $(REFS_AUDIT) | $(FIXTURE_DIST)
	$(PANDOC) $(FIXTURE_SRC_FILES) $(FIXTURE_PANDOC_COMMON) --pdf-engine=$(PDF_ENGINE) -o $@

$(FIXTURE_DOCX_OUT): $(FIXTURE_SRC_FILES) $(FIXTURE_BIB) $(FIXTURE_CSL) $(REFS_AUDIT) | $(FIXTURE_DIST)
	$(PANDOC) $(FIXTURE_SRC_FILES) $(FIXTURE_PANDOC_COMMON) -o $@

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

fixture-lint:
	@status=0; \
	echo "Running fixture manuscript lint checks..."; \
	if rg -n '\[REF\]' $(FIXTURE_LINT_SRCS); then \
		echo "Error: unresolved placeholder [REF] found in fixture."; \
		status=1; \
	fi; \
	tmp_manual="$$(mktemp)"; \
	rg -n '\([^)]*(19|20)[0-9]{2}[a-z]?[^)]*\)' $(FIXTURE_LINT_SRCS) | rg -v '\[@' > "$$tmp_manual" || true; \
	if [ -s "$$tmp_manual" ]; then \
		echo "Error: possible manual author-year citations remain in fixture."; \
		cat "$$tmp_manual"; \
		status=1; \
	fi; \
	rm -f "$$tmp_manual"; \
	if [ "$$status" -eq 0 ]; then \
		echo "Fixture manuscript lint passed."; \
	fi; \
	exit "$$status"

fixture-refs-audit:
	@echo "Running fixture reference audit..."
	@args=(); \
	for src in $(FIXTURE_SRC_FILES); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(REFS_AUDIT)" --bibliography "$(FIXTURE_BIB)" "$${args[@]}"

check: check-tools lint-manuscript refs-audit
	@$(MAKE) --no-print-directory all
	@echo "Build check passed."

check-fixture: check-tools fixture-lint fixture-refs-audit
	@$(MAKE) --no-print-directory fixture-all
	@echo "Fixture build check passed."

clean:
	rm -rf $(DIST)
