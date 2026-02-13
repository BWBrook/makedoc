SHELL := /bin/bash

PANDOC ?= pandoc
PDF_ENGINE ?= xelatex
PDF_ENGINE_OUTPUT_DIR ?= .cache/latex
PANDOC_FROM ?= markdown+tex_math_dollars+tex_math_single_backslash

CONFIG ?= settings/build.yaml
PROFILE ?=
FIXTURE_CONFIG ?= settings/fixture.yaml
FIXTURE_PROFILE ?= fixture

CONFIG_SCRIPT ?= scripts/build_profile.py
VALIDATE_CONFIG ?= scripts/validate_build_config.py
PROFILE_SCAFFOLD ?= scripts/profile_scaffold.py
LINT_SCRIPT ?= scripts/lint_manuscript.py
REFS_AUDIT ?= scripts/refs_audit.py
CSL_RESOLVER ?= scripts/csl_resolver.py
GOLDEN_CHECK ?= scripts/fixture_golden_check.py
MANIFEST_SCRIPT ?= scripts/build_manifest.py
DIAGNOSE_SCRIPT ?= scripts/diagnose_build.py
INSTALLER ?= scripts/install_ubuntu_deps.sh
LAYOUT_RENDER ?= scripts/render_pdf_layout.py
SOURCE_RENDER ?= scripts/prepare_markdown_sources.py

CSL_DEST_DIR ?= csl
JOURNAL ?=

ifneq ($(filter xelatex pdflatex lualatex,$(PDF_ENGINE)),)
PDF_ENGINE_OPTS := --pdf-engine-opt=-output-directory=$(PDF_ENGINE_OUTPUT_DIR)
PDF_RENDER_MULTI_PASS := 1
else
PDF_ENGINE_OPTS :=
PDF_RENDER_MULTI_PASS := 0
endif

PROFILE_NAME ?=
PROFILE_MAIN ?=
PROFILE_FIGS ?=
PROFILE_BIB ?=
PROFILE_CSL ?=
PROFILE_JOURNAL ?=Journal Name
PROFILE_OUTPUT_DIR ?=dist
PROFILE_OUTPUT_STEM ?=manuscript
PROFILE_PAGE_NUMBERS ?= lower_right
PROFILE_LINE_SPACING ?= single
PROFILE_LINE_NUMBERING ?= continuous
PROFILE_PAPER_SIZE ?= a4
PROFILE_MARGIN_UNIT ?= cm
PROFILE_MARGIN_TOP ?= 1.5
PROFILE_MARGIN_RIGHT ?= 1.5
PROFILE_MARGIN_BOTTOM ?= 1.5
PROFILE_MARGIN_LEFT ?= 1.5
PROFILE_FIGURE_PLACEMENT ?= pages
PROFILE_FIGURE_CAPTION_POSITION ?= top
PROFILE_FIGURE_PLACEHOLDER_ID ?= figures
PROFILE_APPEND ?=0
PROFILE_SET_DEFAULT ?=0
PROFILE_OVERWRITE ?=0
DIAG_OUTPUT_ROOT ?=dist/diagnostics

PROFILE_ARG := $(if $(strip $(PROFILE)),--profile $(PROFILE),)
FIXTURE_PROFILE_ARG := $(if $(strip $(FIXTURE_PROFILE)),--profile $(FIXTURE_PROFILE),)
SAME_ACTIVE_AND_FIXTURE := $(and $(filter $(abspath $(CONFIG)),$(abspath $(FIXTURE_CONFIG))),$(filter $(strip $(ACTIVE_PROFILE)),$(strip $(FIXTURE_PROFILE))))

PROFILE_CACHE_DIR := .cache
ACTIVE_VARS_FILE := $(PROFILE_CACHE_DIR)/active_profile.mk
FIXTURE_VARS_FILE := $(PROFILE_CACHE_DIR)/fixture_profile.mk
ACTIVE_LAYOUT_TEX := $(PROFILE_CACHE_DIR)/active_layout.tex
FIXTURE_LAYOUT_TEX := $(PROFILE_CACHE_DIR)/fixture_layout.tex
ACTIVE_SOURCE_MD := $(PROFILE_CACHE_DIR)/active_sources.md
FIXTURE_SOURCE_MD := $(PROFILE_CACHE_DIR)/fixture_sources.md

define render_pdf
	@tmp="$$(mktemp)"; \
	$(1) > "$$tmp" 2>&1; status=$$?; \
	if [ $$status -ne 0 ]; then \
		cat "$$tmp"; \
		rm -f "$$tmp"; \
		exit $$status; \
	fi; \
	if [ "$(PDF_RENDER_MULTI_PASS)" = "1" ]; then \
		$(1) > "$$tmp" 2>&1; status=$$?; \
		if [ $$status -ne 0 ]; then \
			cat "$$tmp"; \
			rm -f "$$tmp"; \
			exit $$status; \
		fi; \
	fi; \
	rm -f "$$tmp"
endef

$(shell mkdir -p "$(PROFILE_CACHE_DIR)" "$(PDF_ENGINE_OUTPUT_DIR)")
$(shell rm -f "$(ACTIVE_VARS_FILE)" "$(FIXTURE_VARS_FILE)")
$(shell set -e; tmp="$(ACTIVE_VARS_FILE).tmp.$$$$"; python3 "$(CONFIG_SCRIPT)" --config "$(CONFIG)" $(PROFILE_ARG) make-vars --prefix ACTIVE > "$$tmp" && mv "$$tmp" "$(ACTIVE_VARS_FILE)")
$(shell set -e; tmp="$(FIXTURE_VARS_FILE).tmp.$$$$"; python3 "$(CONFIG_SCRIPT)" --config "$(FIXTURE_CONFIG)" $(FIXTURE_PROFILE_ARG) make-vars --prefix FIXTURE > "$$tmp" && mv "$$tmp" "$(FIXTURE_VARS_FILE)")
$(shell set -e; tmp="$(ACTIVE_LAYOUT_TEX).tmp.$$$$"; python3 "$(LAYOUT_RENDER)" --config "$(CONFIG)" $(PROFILE_ARG) --output "$$tmp" && mv "$$tmp" "$(ACTIVE_LAYOUT_TEX)")
$(shell set -e; tmp="$(FIXTURE_LAYOUT_TEX).tmp.$$$$"; python3 "$(LAYOUT_RENDER)" --config "$(FIXTURE_CONFIG)" $(FIXTURE_PROFILE_ARG) --output "$$tmp" && mv "$$tmp" "$(FIXTURE_LAYOUT_TEX)")
$(shell set -e; tmp="$(ACTIVE_SOURCE_MD).tmp.$$$$"; python3 "$(SOURCE_RENDER)" --config "$(CONFIG)" $(PROFILE_ARG) --output "$$tmp" && mv "$$tmp" "$(ACTIVE_SOURCE_MD)")
$(shell set -e; tmp="$(FIXTURE_SOURCE_MD).tmp.$$$$"; python3 "$(SOURCE_RENDER)" --config "$(FIXTURE_CONFIG)" $(FIXTURE_PROFILE_ARG) --output "$$tmp" && mv "$$tmp" "$(FIXTURE_SOURCE_MD)")

include $(ACTIVE_VARS_FILE)
include $(FIXTURE_VARS_FILE)

ifeq ($(strip $(ACTIVE_MANUSCRIPT_SOURCES)),)
$(error Failed to load active build profile from $(CONFIG))
endif
ifeq ($(strip $(FIXTURE_MANUSCRIPT_SOURCES)),)
$(error Failed to load fixture profile '$(FIXTURE_PROFILE)' from $(FIXTURE_CONFIG))
endif

ACTIVE_PDF_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(ACTIVE_BIBLIOGRAPHY) --csl $(ACTIVE_CSL) --include-in-header="$(ACTIVE_LAYOUT_TEX)"
ACTIVE_DOCX_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(ACTIVE_BIBLIOGRAPHY) --csl $(ACTIVE_CSL)
FIXTURE_PDF_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(FIXTURE_BIBLIOGRAPHY) --csl $(FIXTURE_CSL) --include-in-header="$(FIXTURE_LAYOUT_TEX)"
FIXTURE_DOCX_COMMON = --from $(PANDOC_FROM) --citeproc --bibliography $(FIXTURE_BIBLIOGRAPHY) --csl $(FIXTURE_CSL)
ACTIVE_MANIFEST_OUT := $(ACTIVE_OUTPUT_DIR)/$(ACTIVE_OUTPUT_STEM)_build_manifest.json
FIXTURE_MANIFEST_OUT := $(FIXTURE_OUTPUT_DIR)/$(FIXTURE_OUTPUT_STEM)_build_manifest.json
FIXTURE_CONTRACT_PATH := $(if $(strip $(FIXTURE_GOLDEN_CONTRACT)),$(FIXTURE_GOLDEN_CONTRACT),testbed/expected/golden_contract.yaml)

.PHONY: all pdf docx manifest fixture-manifest show-manifest diagnose fixture-diagnose fixture-all fixture-pdf fixture-docx testbed testbed/ testbed-all test-output-routing test-figure-modes check-tools validate-config lint-manuscript refs-audit fixture-lint fixture-refs-audit fixture-contract-check fixture-golden-check check-fixture-guards check check-fixture wsl-smoke clean clean-all tidy profiles profile-show profile-scaffold csl-search csl-source deps-estimate-minimal deps-estimate-full deps-dry-run-minimal deps-dry-run-full deps-install-minimal deps-install-full

all: pdf docx manifest

testbed testbed/ testbed-all: fixture-all

pdf: $(ACTIVE_PDF_OUT)

docx: $(ACTIVE_DOCX_OUT)

fixture-all: fixture-pdf fixture-docx fixture-manifest

OUTPUT_DIRS := $(sort $(ACTIVE_OUTPUT_DIR) $(FIXTURE_OUTPUT_DIR))

$(OUTPUT_DIRS):
	mkdir -p "$@"

ifneq ($(strip $(SAME_ACTIVE_AND_FIXTURE)),)
fixture-pdf: $(ACTIVE_PDF_OUT)
fixture-docx: $(ACTIVE_DOCX_OUT)
fixture-manifest: $(ACTIVE_MANIFEST_OUT)
else
fixture-pdf: $(FIXTURE_PDF_OUT)
fixture-docx: $(FIXTURE_DOCX_OUT)
fixture-manifest: $(FIXTURE_MANIFEST_OUT)
endif

$(ACTIVE_PDF_OUT): $(ACTIVE_MANUSCRIPT_SOURCES) $(ACTIVE_SOURCE_MD) $(ACTIVE_BIBLIOGRAPHY) $(ACTIVE_CSL) $(REFS_AUDIT) $(LINT_SCRIPT) | $(ACTIVE_OUTPUT_DIR)
	$(call render_pdf, $(PANDOC) $(ACTIVE_SOURCE_MD) $(ACTIVE_PDF_COMMON) $(PDF_ENGINE_OPTS) --pdf-engine=$(PDF_ENGINE) -o $@)

$(ACTIVE_DOCX_OUT): $(ACTIVE_MANUSCRIPT_SOURCES) $(ACTIVE_SOURCE_MD) $(ACTIVE_BIBLIOGRAPHY) $(ACTIVE_CSL) $(REFS_AUDIT) $(LINT_SCRIPT) | $(ACTIVE_OUTPUT_DIR)
	$(PANDOC) $(ACTIVE_SOURCE_MD) $(ACTIVE_DOCX_COMMON) -o $@

ifneq ($(strip $(SAME_ACTIVE_AND_FIXTURE)),)
else
$(FIXTURE_PDF_OUT): $(FIXTURE_MANUSCRIPT_SOURCES) $(FIXTURE_SOURCE_MD) $(FIXTURE_BIBLIOGRAPHY) $(FIXTURE_CSL) $(REFS_AUDIT) $(LINT_SCRIPT) | $(FIXTURE_OUTPUT_DIR)
		$(call render_pdf, $(PANDOC) $(FIXTURE_SOURCE_MD) $(FIXTURE_PDF_COMMON) $(PDF_ENGINE_OPTS) --pdf-engine=$(PDF_ENGINE) -o $@)

$(FIXTURE_DOCX_OUT): $(FIXTURE_MANUSCRIPT_SOURCES) $(FIXTURE_SOURCE_MD) $(FIXTURE_BIBLIOGRAPHY) $(FIXTURE_CSL) $(REFS_AUDIT) $(LINT_SCRIPT) | $(FIXTURE_OUTPUT_DIR)
		$(PANDOC) $(FIXTURE_SOURCE_MD) $(FIXTURE_DOCX_COMMON) -o $@
endif

$(ACTIVE_MANIFEST_OUT): $(ACTIVE_PDF_OUT) $(ACTIVE_DOCX_OUT) $(MANIFEST_SCRIPT) $(ACTIVE_MANUSCRIPT_SOURCES) $(ACTIVE_BIBLIOGRAPHY) $(ACTIVE_CSL) $(if $(strip $(ACTIVE_GOLDEN_CONTRACT)),$(ACTIVE_GOLDEN_CONTRACT),)
	@python3 "$(MANIFEST_SCRIPT)" --config "$(CONFIG)" --profile "$(ACTIVE_PROFILE)" --output "$@" --pdf "$(ACTIVE_PDF_OUT)" --docx "$(ACTIVE_DOCX_OUT)"

ifneq ($(strip $(SAME_ACTIVE_AND_FIXTURE)),)
else
$(FIXTURE_MANIFEST_OUT): $(FIXTURE_PDF_OUT) $(FIXTURE_DOCX_OUT) $(MANIFEST_SCRIPT) $(FIXTURE_MANUSCRIPT_SOURCES) $(FIXTURE_BIBLIOGRAPHY) $(FIXTURE_CSL) $(if $(strip $(FIXTURE_GOLDEN_CONTRACT)),$(FIXTURE_GOLDEN_CONTRACT),)
	@python3 "$(MANIFEST_SCRIPT)" --config "$(FIXTURE_CONFIG)" --profile "$(FIXTURE_PROFILE)" --output "$@" --pdf "$(FIXTURE_PDF_OUT)" --docx "$(FIXTURE_DOCX_OUT)"
endif

check-tools:
	@for cmd in "$(PANDOC)" "$(PDF_ENGINE)"; do \
		command -v "$$cmd" >/dev/null 2>&1 || { echo "Missing required tool: $$cmd"; exit 1; }; \
	done
	@echo "Tool check passed."

validate-config:
	@echo "Validating build profile config..."
	@python3 "$(VALIDATE_CONFIG)" --config "$(CONFIG)" --profile "$(ACTIVE_PROFILE)"
	@python3 "$(VALIDATE_CONFIG)" --config "$(FIXTURE_CONFIG)" --profile "$(FIXTURE_PROFILE)"

manifest: $(ACTIVE_MANIFEST_OUT)

fixture-manifest: $(FIXTURE_MANIFEST_OUT)

show-manifest: manifest
	@python3 -c 'import json, pathlib; p=pathlib.Path("$(ACTIVE_MANIFEST_OUT)"); print(json.dumps(json.loads(p.read_text(encoding="utf-8")), indent=2))'

diagnose:
	@python3 "$(DIAGNOSE_SCRIPT)" --config "$(CONFIG)" --profile "$(ACTIVE_PROFILE)" --output-root "$(DIAG_OUTPUT_ROOT)" --manifest "$(ACTIVE_MANIFEST_OUT)"

fixture-diagnose:
	@python3 "$(DIAGNOSE_SCRIPT)" --config "$(FIXTURE_CONFIG)" --profile "$(FIXTURE_PROFILE)" --output-root "$(DIAG_OUTPUT_ROOT)" --manifest "$(FIXTURE_MANIFEST_OUT)"

test-output-routing:
	@bash scripts/test_output_routing.sh

test-figure-modes:
	@bash scripts/test_figure_modes.sh

profiles:
	@python3 "$(CONFIG_SCRIPT)" --config "$(CONFIG)" list-profiles

profile-show:
	@python3 "$(CONFIG_SCRIPT)" --config "$(CONFIG)" $(PROFILE_ARG) show --format yaml

profile-scaffold:
	@test -n "$(PROFILE_NAME)" || { echo "Usage: make profile-scaffold PROFILE_NAME=<name> [PROFILE_MAIN=<path>] [PROFILE_FIGS=<path>] [PROFILE_BIB=<path>] [PROFILE_CSL=<path>] [PROFILE_PAGE_NUMBERS=lower_right] [PROFILE_LINE_SPACING=single] [PROFILE_LINE_NUMBERING=continuous] [PROFILE_FIGURE_PLACEMENT=pages] [PROFILE_FIGURE_CAPTION_POSITION=top] [PROFILE_FIGURE_PLACEHOLDER_ID=figures] [PROFILE_PAPER_SIZE=a4] [PROFILE_MARGIN_UNIT=cm] [PROFILE_MARGIN_TOP=1.5] [PROFILE_MARGIN_RIGHT=1.5] [PROFILE_MARGIN_BOTTOM=1.5] [PROFILE_MARGIN_LEFT=1.5] [PROFILE_APPEND=1] [PROFILE_SET_DEFAULT=1]"; exit 1; }
	@args=( \
		--name "$(PROFILE_NAME)" \
		--config "$(CONFIG)" \
		--journal "$(PROFILE_JOURNAL)" \
		--output-dir "$(PROFILE_OUTPUT_DIR)" \
		--output-stem "$(PROFILE_OUTPUT_STEM)" \
	); \
	if [ -n "$(PROFILE_MAIN)" ]; then args+=(--manuscript-source "$(PROFILE_MAIN)"); fi; \
	if [ -n "$(PROFILE_FIGS)" ]; then args+=(--manuscript-source "$(PROFILE_FIGS)"); fi; \
	if [ -n "$(PROFILE_BIB)" ]; then args+=(--bibliography "$(PROFILE_BIB)"); fi; \
	if [ -n "$(PROFILE_CSL)" ]; then args+=(--csl "$(PROFILE_CSL)"); fi; \
	args+=(--page-numbers "$(PROFILE_PAGE_NUMBERS)"); \
	args+=(--line-spacing "$(PROFILE_LINE_SPACING)"); \
	args+=(--line-numbering "$(PROFILE_LINE_NUMBERING)"); \
	args+=(--figure-placement "$(PROFILE_FIGURE_PLACEMENT)"); \
	args+=(--figure-caption-position "$(PROFILE_FIGURE_CAPTION_POSITION)"); \
	args+=(--figure-placeholder-id "$(PROFILE_FIGURE_PLACEHOLDER_ID)"); \
	args+=(--paper-size "$(PROFILE_PAPER_SIZE)"); \
	args+=(--margin-unit "$(PROFILE_MARGIN_UNIT)"); \
	args+=(--margin-top "$(PROFILE_MARGIN_TOP)"); \
	args+=(--margin-right "$(PROFILE_MARGIN_RIGHT)"); \
	args+=(--margin-bottom "$(PROFILE_MARGIN_BOTTOM)"); \
	args+=(--margin-left "$(PROFILE_MARGIN_LEFT)"); \
	if [ "$(PROFILE_APPEND)" = "1" ]; then args+=(--append); fi; \
	if [ "$(PROFILE_SET_DEFAULT)" = "1" ]; then args+=(--set-default); fi; \
	if [ "$(PROFILE_OVERWRITE)" = "1" ]; then args+=(--overwrite); fi; \
	python3 "$(PROFILE_SCAFFOLD)" "$${args[@]}"

lint-manuscript:
	@echo "Running manuscript lint checks..."
	@args=(); \
	for src in $(ACTIVE_LINT_SOURCES); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(LINT_SCRIPT)" "$${args[@]}"

refs-audit:
	@echo "Running reference audit..."
	@args=(); \
	for src in $(ACTIVE_MANUSCRIPT_SOURCES); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(REFS_AUDIT)" --bibliography "$(ACTIVE_BIBLIOGRAPHY)" "$${args[@]}"

fixture-lint:
	@echo "Running fixture manuscript lint checks..."
	@args=(); \
	for src in $(FIXTURE_LINT_SOURCES); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(LINT_SCRIPT)" "$${args[@]}"

fixture-refs-audit:
	@echo "Running fixture reference audit..."
	@args=(); \
	for src in $(FIXTURE_MANUSCRIPT_SOURCES); do \
		args+=(--source "$$src"); \
	done; \
	python3 "$(REFS_AUDIT)" --bibliography "$(FIXTURE_BIBLIOGRAPHY)" "$${args[@]}"

fixture-contract-check: $(FIXTURE_PDF_OUT) $(FIXTURE_DOCX_OUT)
	@echo "Running fixture contract checks..."
	@python3 "$(GOLDEN_CHECK)" --pdf "$(FIXTURE_PDF_OUT)" --docx "$(FIXTURE_DOCX_OUT)" --contract "$(FIXTURE_CONTRACT_PATH)"

fixture-golden-check: fixture-contract-check
	@:

check-fixture-guards:
	@echo "Running fixture guard regression tests..."
	@test -n "$(FIXTURE_EDGECASE_UNKNOWN_CITE)" || { echo "Missing fixture edgecase: unknown_cite"; exit 1; }
	@test -n "$(FIXTURE_EDGECASE_MANUAL_CITE)" || { echo "Missing fixture edgecase: manual_cite"; exit 1; }
	@test -n "$(FIXTURE_EDGECASE_MALFORMED_TABLE)" || { echo "Missing fixture edgecase: malformed_table"; exit 1; }
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
		env DISABLE_GHA_ANNOTATIONS=1 python3 "$(REFS_AUDIT)" --bibliography "$(FIXTURE_BIBLIOGRAPHY)" --source "$(FIXTURE_EDGECASE_UNKNOWN_CITE)"; \
	expect_fail "lint catches manual author-year citation" \
		env DISABLE_GHA_ANNOTATIONS=1 python3 "$(LINT_SCRIPT)" --source "$(FIXTURE_EDGECASE_MANUAL_CITE)"; \
	expect_fail "lint catches malformed markdown table" \
		env DISABLE_GHA_ANNOTATIONS=1 python3 "$(LINT_SCRIPT)" --source "$(FIXTURE_EDGECASE_MALFORMED_TABLE)"; \
	if [ "$$status" -eq 0 ]; then \
		echo "Fixture guard regression tests passed."; \
	fi; \
	exit "$$status"

csl-search:
	@test -n "$(JOURNAL)" || { echo "Usage: make csl-search JOURNAL='Journal Name'"; exit 1; }
	@args=(); \
	for dir in $(ACTIVE_CSL_SEARCH_DIRS); do \
		args+=(--search-dir "$$dir"); \
	done; \
	python3 "$(CSL_RESOLVER)" search --journal "$(JOURNAL)" "$${args[@]}"

csl-source:
	@test -n "$(JOURNAL)" || { echo "Usage: make csl-source JOURNAL='Journal Name'"; exit 1; }
	@args=(); \
	for dir in $(ACTIVE_CSL_SEARCH_DIRS); do \
		args+=(--search-dir "$$dir"); \
	done; \
	python3 "$(CSL_RESOLVER)" source --journal "$(JOURNAL)" --dest-dir "$(CSL_DEST_DIR)" "$${args[@]}"

check: check-tools validate-config lint-manuscript refs-audit
	@$(MAKE) --no-print-directory all
	@echo "Build check passed."

check-fixture: check-tools validate-config fixture-lint fixture-refs-audit test-figure-modes
	@$(MAKE) --no-print-directory fixture-all
	@$(MAKE) --no-print-directory fixture-contract-check
	@echo "Fixture build check passed."

wsl-smoke:
	@echo "Running WSL smoke checks..."
	@$(MAKE) --no-print-directory deps-dry-run-minimal
	@$(MAKE) --no-print-directory profiles
	@$(MAKE) --no-print-directory profile-show
	@args=(); \
	for dir in $(ACTIVE_CSL_SEARCH_DIRS); do \
		args+=(--search-dir "$$dir"); \
	done; \
	if [ -n "$(ACTIVE_JOURNAL)" ]; then \
		python3 "$(CSL_RESOLVER)" source --journal "$(ACTIVE_JOURNAL)" --local-only --path-only "$${args[@]}" >/dev/null; \
		echo "Local CSL resolver check passed for journal: $(ACTIVE_JOURNAL)"; \
	else \
		echo "Skipping local CSL resolver check (profile journal is empty)."; \
	fi
	@$(MAKE) --no-print-directory check
	@$(MAKE) --no-print-directory check-fixture
	@$(MAKE) --no-print-directory check-fixture-guards
	@echo "WSL smoke checks passed."

deps-estimate-minimal:
	@bash "$(INSTALLER)" --mode minimal --estimate-only

deps-estimate-full:
	@bash "$(INSTALLER)" --mode full --estimate-only

deps-dry-run-minimal:
	@bash "$(INSTALLER)" --mode minimal --dry-run

deps-dry-run-full:
	@bash "$(INSTALLER)" --mode full --dry-run

deps-install-minimal:
	@bash "$(INSTALLER)" --mode minimal

deps-install-full:
	@bash "$(INSTALLER)" --mode full

clean:
	rm -rf dist .cache
	rm -f texput.log test-*.log test-*.aux test-*.pdf test-*.out

clean-all: clean tidy

tidy:
	rm -f texput.log test-*.log test-*.aux test-*.pdf test-*.out test-*.fdb_latexmk test-*.fls
	rm -rf .cache/latex
