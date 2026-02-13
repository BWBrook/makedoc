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
LINT_SCRIPT ?= scripts/lint_manuscript.py

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
EDGECASE_DIR ?= testbed/edgecases
EDGECASE_UNKNOWN_SRC ?= $(EDGECASE_DIR)/unknown_cite_main.md
EDGECASE_MANUAL_SRC ?= $(EDGECASE_DIR)/manual_cite_main.md
EDGECASE_TABLE_SRC ?= $(EDGECASE_DIR)/malformed_table_main.md

PANDOC_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(BIB) --csl $(CSL)
FIXTURE_PANDOC_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(FIXTURE_BIB) --csl $(FIXTURE_CSL)

.PHONY: all pdf docx fixture-all fixture-pdf fixture-docx check-tools lint-manuscript refs-audit fixture-lint fixture-refs-audit check-fixture-guards check check-fixture clean

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

$(PDF_OUT): $(SRC_FILES) $(BIB) $(CSL) $(REFS_AUDIT) $(LINT_SCRIPT) | $(DIST)
	$(PANDOC) $(SRC_FILES) $(PANDOC_COMMON) --pdf-engine=$(PDF_ENGINE) -o $@

$(DOCX_OUT): $(SRC_FILES) $(BIB) $(CSL) $(REFS_AUDIT) $(LINT_SCRIPT) | $(DIST)
	$(PANDOC) $(SRC_FILES) $(PANDOC_COMMON) -o $@

$(FIXTURE_PDF_OUT): $(FIXTURE_SRC_FILES) $(FIXTURE_BIB) $(FIXTURE_CSL) $(REFS_AUDIT) $(LINT_SCRIPT) | $(FIXTURE_DIST)
	$(PANDOC) $(FIXTURE_SRC_FILES) $(FIXTURE_PANDOC_COMMON) --pdf-engine=$(PDF_ENGINE) -o $@

$(FIXTURE_DOCX_OUT): $(FIXTURE_SRC_FILES) $(FIXTURE_BIB) $(FIXTURE_CSL) $(REFS_AUDIT) $(LINT_SCRIPT) | $(FIXTURE_DIST)
	$(PANDOC) $(FIXTURE_SRC_FILES) $(FIXTURE_PANDOC_COMMON) -o $@

check-tools:
	@for cmd in "$(PANDOC)" "$(PDF_ENGINE)"; do \
		command -v "$$cmd" >/dev/null 2>&1 || { echo "Missing required tool: $$cmd"; exit 1; }; \
	done
	@echo "Tool check passed."

lint-manuscript:
	@echo "Running manuscript lint checks..."
	@args=(); \
	for src in $(LINT_SRCS); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(LINT_SCRIPT)" "$${args[@]}"

refs-audit:
	@echo "Running reference audit..."
	@args=(); \
	for src in $(SRC_FILES); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(REFS_AUDIT)" --bibliography "$(BIB)" "$${args[@]}"

fixture-lint:
	@echo "Running fixture manuscript lint checks..."
	@args=(); \
	for src in $(FIXTURE_LINT_SRCS); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(LINT_SCRIPT)" "$${args[@]}"

fixture-refs-audit:
	@echo "Running fixture reference audit..."
	@args=(); \
	for src in $(FIXTURE_SRC_FILES); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(REFS_AUDIT)" --bibliography "$(FIXTURE_BIB)" "$${args[@]}"

check-fixture-guards:
	@echo "Running fixture guard regression tests..."
	@status=0; \
	expect_fail() { \
		label="$$1"; \
		shift; \
		if "$$@"; then \
			echo "Error: guard test unexpectedly passed: $$label"; \
			status=1; \
		else \
			echo "Expected failure observed: $$label"; \
		fi; \
	}; \
	expect_fail "refs audit catches unknown citation key" \
		python3 "$(REFS_AUDIT)" --bibliography "$(FIXTURE_BIB)" --source "$(EDGECASE_UNKNOWN_SRC)" --source "$(FIXTURE_SRC_FIGS)"; \
	expect_fail "lint catches manual author-year citation" \
		python3 "$(LINT_SCRIPT)" --source "$(EDGECASE_MANUAL_SRC)" --source "$(FIXTURE_SRC_FIGS)"; \
	expect_fail "lint catches malformed markdown table" \
		python3 "$(LINT_SCRIPT)" --source "$(EDGECASE_TABLE_SRC)" --source "$(FIXTURE_SRC_FIGS)"; \
	if [ "$$status" -eq 0 ]; then \
		echo "Fixture guard regression tests passed."; \
	fi; \
	exit "$$status"

check: check-tools lint-manuscript refs-audit
	@$(MAKE) --no-print-directory all
	@echo "Build check passed."

check-fixture: check-tools fixture-lint fixture-refs-audit
	@$(MAKE) --no-print-directory fixture-all
	@echo "Fixture build check passed."

clean:
	rm -rf $(DIST)
