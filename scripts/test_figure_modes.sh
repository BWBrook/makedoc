#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR=""

cleanup_tmpdir() {
	if [ -n "${TMP_DIR}" ]; then
		rm -rf "${TMP_DIR}" >/dev/null 2>&1 || true
	fi
}

assert_file_exists() {
	local path=$1
	if [ ! -f "$path" ]; then
		echo "ASSERTION FAILED: expected file missing: $path" >&2
		exit 1
	fi
}

assert_contains() {
	local file=$1
	local pattern=$2
	if ! grep -Fq -- "$pattern" "$file"; then
		echo "ASSERTION FAILED: expected pattern not found in $file: $pattern" >&2
		exit 1
	fi
}

assert_exact_line() {
	local file=$1
	local pattern=$2
	if ! grep -Fxq -- "$pattern" "$file"; then
		echo "ASSERTION FAILED: expected exact line not found in $file: $pattern" >&2
		exit 1
	fi
}

assert_not_contains() {
	local file=$1
	local pattern=$2
	if grep -Fq -- "$pattern" "$file"; then
		echo "ASSERTION FAILED: unexpected pattern found in $file: $pattern" >&2
		exit 1
	fi
}

first_match_line() {
	local file=$1
	local pattern=$2
	local value
	value="$(grep -nF -- "$pattern" "$file" | head -n 1 | cut -d: -f1 || true)"
	if [ -z "$value" ]; then
		echo ""
		return 1
	fi
	echo "$value"
	return 0
}

assert_ordered_lines() {
	local file=$1
	local first=$2
	local second=$3
	local third=$4
	local first_line
	local second_line
	local third_line

	first_line="$(first_match_line "$file" "$first")"
	second_line="$(first_match_line "$file" "$second")"
	third_line="$(first_match_line "$file" "$third")"

	if [ -z "$first_line" ] || [ -z "$second_line" ] || [ -z "$third_line" ]; then
		echo "ASSERTION FAILED: unable to find expected ordered labels in $file" >&2
		exit 1
	fi

	if [ "$first_line" -ge "$second_line" ] || [ "$second_line" -ge "$third_line" ]; then
		echo "ASSERTION FAILED: labels are not in expected order in $file" >&2
		echo "  $first at line $first_line" >&2
		echo "  $second at line $second_line" >&2
		echo "  $third at line $third_line" >&2
		exit 1
	fi
}

assert_line_count_at_least() {
	local file=$1
	local pattern=$2
	local minimum=$3
	local count
	count="$(grep -cF -- "$pattern" "$file" || true)"
	if [ "$count" -lt "$minimum" ]; then
		echo "ASSERTION FAILED: expected at least $minimum occurrences of '$pattern' in $file, found $count" >&2
		exit 1
	fi
}

run_pages_mode_check() {
	local tmp_dir=$1
	local cfg=$2

	local main_file="$tmp_dir/pages-main.md"
	local figure_file="$tmp_dir/pages-figures.md"
	local prepared="$tmp_dir/pages-prepared.md"

	cat > "$main_file" <<'EOF'
# Figure Mode Regression: pages

This manuscript section has no figure placeholder.

## References

Dummy reference list placeholder.
EOF

cat > "$figure_file" <<EOF
![Fixture main figure used for CI layout and rendering checks.]($REPO_ROOT/testbed/manuscript/figures/fig1_dummy.png){#fig-fixture-main width=95%}
![Fixture richness figure used for CI cross-reference and image embedding checks.]($REPO_ROOT/testbed/manuscript/figures/fig2_dummy.png){#fig-fixture-richness width=85%}
![Fixture supplementary figure used for supplementary material rendering checks.]($REPO_ROOT/testbed/manuscript/figures/figS1_dummy.png){#fig-fixture-s1 width=85%}
EOF

	cat > "$cfg" <<EOF
default_profile: pages
profiles:
  pages:
    manuscript_sources:
      - $main_file
      - $figure_file
    lint_sources:
      - $main_file
      - $figure_file
    bibliography: $REPO_ROOT/testbed/references/fixture_refs.yaml
    csl: $REPO_ROOT/testbed/csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - $REPO_ROOT/testbed/csl
    output_dir: dist/figures-check
    output_stem: fixture
    page_numbers: lower_right
    line_spacing: single
    line_numbering: continuous
    figures:
      placement: pages
      caption_position: top
      placeholder_id: figures
EOF

	python3 scripts/prepare_markdown_sources.py --config "$cfg" --profile pages --output "$prepared"
	assert_file_exists "$prepared"

	assert_contains "$prepared" "**Fig. 1.**"
	assert_contains "$prepared" "**Fig. 2.**"
	assert_contains "$prepared" "**Fig. S1.**"
	assert_contains "$prepared" "## Supplementary Information"
	assert_ordered_lines "$prepared" "**Fig. 1.**" "**Fig. 2.**" "**Fig. S1.**"
	assert_ordered_lines "$prepared" "**Fig. 2.**" "## Supplementary Information" "**Fig. S1.**"
	assert_line_count_at_least "$prepared" "\\clearpage" 4
	assert_not_contains "$prepared" "<div id=\"figures\"></div>"
}

run_inline_bottom_check() {
	local tmp_dir=$1
	local cfg=$2

	local main_file="$tmp_dir/inline-main.md"
	local figure_file="$tmp_dir/inline-figures.md"
	local prepared="$tmp_dir/inline-prepared.md"

	cat > "$main_file" <<'EOF'
# Figure Mode Regression: inline

Text before inserted figures.

<div id="figures"></div>

More text after placeholder.

## References

Dummy reference list placeholder.
EOF

cat > "$figure_file" <<EOF
![Fixture main figure used for CI layout and rendering checks.]($REPO_ROOT/testbed/manuscript/figures/fig1_dummy.png){#fig-fixture-main width=95%}
EOF

	cat > "$cfg" <<EOF
default_profile: inline
profiles:
  inline:
    manuscript_sources:
      - $main_file
      - $figure_file
    lint_sources:
      - $main_file
      - $figure_file
    bibliography: $REPO_ROOT/testbed/references/fixture_refs.yaml
    csl: $REPO_ROOT/testbed/csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - $REPO_ROOT/testbed/csl
    output_dir: dist/figures-check
    output_stem: fixture
    page_numbers: lower_right
    line_spacing: single
    line_numbering: continuous
    figures:
      placement: inline
      caption_position: bottom
      placeholder_id: figures
EOF

	python3 scripts/prepare_markdown_sources.py --config "$cfg" --profile inline --output "$prepared"
	assert_file_exists "$prepared"

	assert_not_contains "$prepared" "<div id=\"figures\"></div>"
	assert_not_contains "$prepared" "\\clearpage"
	assert_contains "$prepared" "!["
	assert_contains "$prepared" "**Fig. 1.**"

	local image_line
	local caption_line
	image_line="$(first_match_line "$prepared" "![Fixture main figure used for CI layout and rendering checks.]")"
	caption_line="$(first_match_line "$prepared" "**Fig. 1.**")"
	if [ -z "$image_line" ] || [ -z "$caption_line" ]; then
		echo "ASSERTION FAILED: missing inline image/caption in $prepared" >&2
		exit 1
	fi
	if [ "$caption_line" -le "$image_line" ]; then
		echo "ASSERTION FAILED: inline caption appears before image in $prepared" >&2
		exit 1
	fi
}

run_captions_page_check() {
	local tmp_dir=$1
	local cfg=$2

	local main_file="$tmp_dir/captions-main.md"
	local figure_file="$tmp_dir/captions-figures.md"
	local prepared="$tmp_dir/captions-prepared.md"

	cat > "$main_file" <<'EOF'
# Figure Mode Regression: captions page

This manuscript section has a references placeholder and no inline figure slot.

## References

Dummy reference list placeholder.
EOF

cat > "$figure_file" <<EOF
![Fixture main figure used for CI layout and rendering checks.]($REPO_ROOT/testbed/manuscript/figures/fig1_dummy.png){#fig-fixture-main width=95%}
![Fixture richness figure used for CI cross-reference and image embedding checks.]($REPO_ROOT/testbed/manuscript/figures/fig2_dummy.png){#fig-fixture-richness width=85%}
![Fixture supplementary figure used for supplementary material rendering checks.]($REPO_ROOT/testbed/manuscript/figures/figS1_dummy.png){#fig-fixture-s1 width=85%}
EOF

	cat > "$cfg" <<EOF
default_profile: captions
profiles:
  captions:
    manuscript_sources:
      - $main_file
      - $figure_file
    lint_sources:
      - $main_file
      - $figure_file
    bibliography: $REPO_ROOT/testbed/references/fixture_refs.yaml
    csl: $REPO_ROOT/testbed/csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - $REPO_ROOT/testbed/csl
    output_dir: dist/figures-check
    output_stem: fixture
    page_numbers: lower_right
    line_spacing: single
    line_numbering: continuous
    figures:
      placement: captions_page
      caption_position: top
      placeholder_id: figures
EOF

	python3 scripts/prepare_markdown_sources.py --config "$cfg" --profile captions --output "$prepared"
	assert_file_exists "$prepared"

	assert_contains "$prepared" "## Figure Captions"
	assert_exact_line "$prepared" "**Fig. 1.** Fixture main figure used for CI layout and rendering checks."
	assert_exact_line "$prepared" "**Fig. 2.** Fixture richness figure used for CI cross-reference and image embedding checks."
	assert_exact_line "$prepared" "**Fig. S1.** Fixture supplementary figure used for supplementary material rendering checks."
	assert_not_contains "$prepared" "- **Fig. 1.**"
	assert_not_contains "$prepared" "- **Fig. 2.**"
	assert_not_contains "$prepared" "- **Fig. S1.**"
	assert_contains "$prepared" "## Supplementary Information"
	assert_ordered_lines "$prepared" "## Figure Captions" "**Fig. 1.** Fixture main figure used for CI layout and rendering checks." "**Fig. 2.** Fixture richness figure used for CI cross-reference and image embedding checks."
	assert_ordered_lines "$prepared" "## Figure Captions" "**Fig. 2.** Fixture richness figure used for CI cross-reference and image embedding checks." "## Supplementary Information"
	assert_line_count_at_least "$prepared" "\\clearpage" 5
	assert_contains "$prepared" "![]($REPO_ROOT/testbed/manuscript/figures/fig1_dummy.png){#fig-fixture-main width=95%}"
	assert_contains "$prepared" "![]($REPO_ROOT/testbed/manuscript/figures/fig2_dummy.png){#fig-fixture-richness width=85%}"
	assert_contains "$prepared" "![]($REPO_ROOT/testbed/manuscript/figures/figS1_dummy.png){#fig-fixture-s1 width=85%}"
	assert_not_contains "$prepared" "![Fixture main figure used for CI layout and rendering checks.]"
	assert_not_contains "$prepared" "![Fixture richness figure used for CI cross-reference and image embedding checks.]"
	assert_not_contains "$prepared" "![Fixture supplementary figure used for supplementary material rendering checks.]"
	assert_exact_line "$prepared" "**Fig. 1.**"
	assert_exact_line "$prepared" "**Fig. 2.**"
	assert_exact_line "$prepared" "**Fig. S1.**"
}

main() {
	local tmp_dir
	tmp_dir="$(mktemp -d)"
	local cfg
	cfg="$tmp_dir/test-config.yaml"
	TMP_DIR="$tmp_dir"
	trap cleanup_tmpdir EXIT

	run_pages_mode_check "$tmp_dir" "$cfg"
	run_inline_bottom_check "$tmp_dir" "$cfg"
	run_captions_page_check "$tmp_dir" "$cfg"
	echo "PASS: figure mode regression checks passed."
}

main "$@"
