#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR=""

cleanup_tmpdir() {
	if [ -n "${TMP_DIR}" ]; then
		rm -rf "${TMP_DIR}" >/dev/null 2>&1 || true
	fi
	make -C "$REPO_ROOT" clean >/dev/null 2>&1 || true
}

assert_file_exists() {
	local path=$1
	if [ ! -f "$path" ]; then
		echo "ASSERTION FAILED: expected file missing: $path" >&2
		exit 1
	fi
}

main() {
	TMP_DIR="$(mktemp -d)"
	trap cleanup_tmpdir EXIT

	local external_repo="$TMP_DIR/external-paper"
	local settings_dir="$external_repo/settings"
	local manuscript_text_dir="$external_repo/manuscript/text"
	local manuscript_figures_dir="$external_repo/manuscript/figures"
	local references_dir="$external_repo/references"
	local csl_dir="$external_repo/csl"
	local output_dir="dist/external-paper"
	local config_path="$settings_dir/build.yaml"

	mkdir -p "$settings_dir" "$manuscript_text_dir" "$manuscript_figures_dir" "$references_dir" "$csl_dir"
	cp "$REPO_ROOT/testbed/manuscript/figures/fig1_dummy.png" "$manuscript_figures_dir/fig1_dummy.png"
	cp "$REPO_ROOT/testbed/manuscript/figures/fig2_dummy.png" "$manuscript_figures_dir/fig2_dummy.png"
	cp "$REPO_ROOT/testbed/manuscript/authors.yaml" "$external_repo/manuscript/authors.yaml"
	cp "$REPO_ROOT/testbed/references/fixture_refs.yaml" "$references_dir/refs.yaml"
	cp "$REPO_ROOT/testbed/csl/fixture_style.csl" "$csl_dir/fixture_style.csl"

	cat > "$manuscript_text_dir/main.md" <<'EOF'
# External Relative Path Regression

<div id="authors"></div>

## Abstract

This synthetic external manuscript exercises config-relative inputs and source-relative figure resources [@alpha2020SyntheticWorkflow].

## Results

Figure content is referenced in Fig. [1](#fig-external-main).

## References
EOF

	cat > "$manuscript_text_dir/figures.md" <<'EOF'
![External regression figure one.](../figures/fig1_dummy.png){#fig-external-main width=95%}
![External regression figure two.](../figures/fig2_dummy.png){#fig-external-two width=85%}
EOF

	cat > "$config_path" <<'EOF'
default_profile: ext

profiles:
  ext:
    manuscript_sources:
      - ../manuscript/text/main.md
      - ../manuscript/text/figures.md
    lint_sources:
      - ../manuscript/text/main.md
      - ../manuscript/text/figures.md
    author_metadata: ../manuscript/authors.yaml
    bibliography: ../references/refs.yaml
    csl: ../csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - ../csl
    output_dir: dist
    output_stem: manuscript
    page_numbers: lower_right
    line_spacing: single
    line_numbering: continuous
    figures:
      placement: pages
      caption_position: top
      placeholder_id: figures
EOF

	make -C "$REPO_ROOT" clean >/dev/null
	CONFIG="$config_path" make -C "$REPO_ROOT" validate-config
	CONFIG="$config_path" make -C "$REPO_ROOT" check
	CONFIG="$config_path" make -C "$REPO_ROOT" all

	assert_file_exists "$REPO_ROOT/$output_dir/manuscript.pdf"
	assert_file_exists "$REPO_ROOT/$output_dir/manuscript.docx"
	assert_file_exists "$REPO_ROOT/$output_dir/manuscript_build_manifest.json"

	echo "PASS: external relative-path regression checks passed."
}

main "$@"
