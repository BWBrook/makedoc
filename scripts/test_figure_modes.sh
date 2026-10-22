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

assert_pattern_between() {
	local file=$1
	local pattern=$2
	local start_pattern=$3
	local end_pattern=$4
	local start_line
	local end_line
	start_line="$(first_match_line "$file" "$start_pattern")"
	end_line="$(first_match_line "$file" "$end_pattern")"
	if [ -z "$start_line" ] || [ -z "$end_line" ]; then
		echo "ASSERTION FAILED: missing boundary patterns in $file ($start_pattern, $end_pattern)" >&2
		exit 1
	fi
	if [ "$start_line" -ge "$end_line" ]; then
		echo "ASSERTION FAILED: boundary patterns in unexpected order for $file" >&2
		exit 1
	fi
	if ! grep -nF -- "$pattern" "$file" | awk -F: -v start="$start_line" -v end="$end_line" '$1 > start && $1 < end {found=1} END{exit(found?0:1)}'; then
		echo "ASSERTION FAILED: expected pattern '$pattern' between '$start_pattern' and '$end_pattern' in $file" >&2
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

assert_line_count_exact() {
	local file=$1
	local pattern=$2
	local expected=$3
	local count
	count="$(grep -cF -- "$pattern" "$file" || true)"
	if [ "$count" -ne "$expected" ]; then
		echo "ASSERTION FAILED: expected exactly $expected occurrences of '$pattern' in $file, found $count" >&2
		exit 1
	fi
}

prepare_fixture_repo() {
	local repo_dir=$1
	mkdir -p "$repo_dir/settings" "$repo_dir/manuscript/text" "$repo_dir/manuscript/figures" "$repo_dir/references" "$repo_dir/csl"
	cp "$REPO_ROOT/testbed/manuscript/figures/fig1_dummy.png" "$repo_dir/manuscript/figures/fig1_dummy.png"
	cp "$REPO_ROOT/testbed/manuscript/figures/fig2_dummy.png" "$repo_dir/manuscript/figures/fig2_dummy.png"
	cp "$REPO_ROOT/testbed/manuscript/figures/figS1_dummy.png" "$repo_dir/manuscript/figures/figS1_dummy.png"
	cp "$REPO_ROOT/testbed/references/fixture_refs.yaml" "$repo_dir/references/fixture_refs.yaml"
	cp "$REPO_ROOT/testbed/csl/fixture_style.csl" "$repo_dir/csl/fixture_style.csl"
}

run_pages_mode_check() {
	local tmp_dir=$1
	local repo_dir="$tmp_dir/pages-repo"
	local cfg="$repo_dir/settings/build.yaml"
	local main_file="$repo_dir/manuscript/text/pages-main.md"
	local figure_file="$repo_dir/manuscript/text/pages-figures.md"
	local prepared="$tmp_dir/pages-prepared.md"

	prepare_fixture_repo "$repo_dir"

	cat > "$main_file" <<'EOF'
# Figure Mode Regression: pages

This manuscript section has no figure placeholder.

## References

Dummy reference list placeholder.
EOF

	cat > "$figure_file" <<EOF
![Fixture main figure used for CI layout and rendering checks.](../figures/fig1_dummy.png){#fig-fixture-main width=95%}
![Fixture richness figure used for CI cross-reference and image embedding checks.](../figures/fig2_dummy.png){#fig-fixture-richness width=85%}
![Fixture supplementary figure used for supplementary material rendering checks.](../figures/figS1_dummy.png){#fig-fixture-s1 width=85%}
EOF

	cat > "$cfg" <<EOF
default_profile: pages
profiles:
  pages:
    manuscript_sources:
      - ../manuscript/text/pages-main.md
      - ../manuscript/text/pages-figures.md
    lint_sources:
      - ../manuscript/text/pages-main.md
      - ../manuscript/text/pages-figures.md
    bibliography: ../references/fixture_refs.yaml
    csl: ../csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - ../csl
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
	assert_line_count_at_least "$prepared" "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>" 4
	assert_not_contains "$prepared" "<div id=\"figures\"></div>"
}

run_inline_bottom_check() {
	local tmp_dir=$1
	local repo_dir="$tmp_dir/inline-repo"
	local cfg="$repo_dir/settings/build.yaml"
	local main_file="$repo_dir/manuscript/text/inline-main.md"
	local figure_file="$repo_dir/manuscript/text/inline-figures.md"
	local prepared="$tmp_dir/inline-prepared.md"

	prepare_fixture_repo "$repo_dir"

	cat > "$main_file" <<'EOF'
# Figure Mode Regression: inline

Text before inserted figures.

<div id="figures"></div>

More text after placeholder.

## References

Dummy reference list placeholder.
EOF

	cat > "$figure_file" <<EOF
![Fixture main figure used for CI layout and rendering checks.](../figures/fig1_dummy.png){#fig-fixture-main width=95%}
EOF

	cat > "$cfg" <<EOF
default_profile: inline
profiles:
  inline:
    manuscript_sources:
      - ../manuscript/text/inline-main.md
      - ../manuscript/text/inline-figures.md
    lint_sources:
      - ../manuscript/text/inline-main.md
      - ../manuscript/text/inline-figures.md
    bibliography: ../references/fixture_refs.yaml
    csl: ../csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - ../csl
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
	assert_line_count_exact "$prepared" "\\clearpage" 1
	assert_line_count_exact "$prepared" "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>" 1
	assert_pattern_between "$prepared" "\\clearpage" "More text after placeholder." "## References"
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

run_inline_empty_alt_suppresses_auto_caption_check() {
	local tmp_dir=$1
	local repo_dir="$tmp_dir/inline-empty-alt-repo"
	local cfg="$repo_dir/settings/build.yaml"
	local main_file="$repo_dir/manuscript/text/inline-main.md"
	local figure_file="$repo_dir/manuscript/text/inline-figures.md"
	local prepared="$tmp_dir/inline-empty-alt-prepared.md"
	local fig1_path="$repo_dir/manuscript/figures/fig1_dummy.png"

	prepare_fixture_repo "$repo_dir"
	fig1_path="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve().as_posix())' "$fig1_path")"

	cat > "$main_file" <<'EOF'
# Figure Mode Regression: inline empty alt

Text before inserted figure.

<div id="figures"></div>

Custom caption text after figure.

## References

Dummy reference list placeholder.
EOF

	cat > "$figure_file" <<EOF
![](../figures/fig1_dummy.png){#fig-fixture-main width=95%}
EOF

	cat > "$cfg" <<EOF
default_profile: inline
profiles:
  inline:
    manuscript_sources:
      - ../manuscript/text/inline-main.md
      - ../manuscript/text/inline-figures.md
    lint_sources:
      - ../manuscript/text/inline-main.md
      - ../manuscript/text/inline-figures.md
    bibliography: ../references/fixture_refs.yaml
    csl: ../csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - ../csl
    output_dir: dist/figures-check
    output_stem: fixture
    page_numbers: lower_right
    line_spacing: single
    line_numbering: continuous
    figures:
      placement: inline
      caption_position: top
      placeholder_id: figures
EOF

	python3 scripts/prepare_markdown_sources.py --config "$cfg" --profile inline --output "$prepared"
	assert_file_exists "$prepared"

	assert_not_contains "$prepared" "<div id=\"figures\"></div>"
	assert_contains "$prepared" "![]($fig1_path){#fig-fixture-main width=95%}"
	assert_not_contains "$prepared" "**Fig. 1.**"
}

run_captions_page_check() {
	local tmp_dir=$1
	local repo_dir="$tmp_dir/captions-repo"
	local cfg="$repo_dir/settings/build.yaml"
	local main_file="$repo_dir/manuscript/text/captions-main.md"
	local figure_file="$repo_dir/manuscript/text/captions-figures.md"
	local prepared="$tmp_dir/captions-prepared.md"
	local fig1_path="$repo_dir/manuscript/figures/fig1_dummy.png"
	local fig2_path="$repo_dir/manuscript/figures/fig2_dummy.png"
	local figS1_path="$repo_dir/manuscript/figures/figS1_dummy.png"

	prepare_fixture_repo "$repo_dir"
	fig1_path="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve().as_posix())' "$fig1_path")"
	fig2_path="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve().as_posix())' "$fig2_path")"
	figS1_path="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve().as_posix())' "$figS1_path")"

	cat > "$main_file" <<'EOF'
# Figure Mode Regression: captions page

This manuscript section has a references placeholder and no inline figure slot.

## References

Dummy reference list placeholder.
EOF

	cat > "$figure_file" <<EOF
![Fixture main figure used for CI layout and rendering checks.](../figures/fig1_dummy.png){#fig-fixture-main width=95%}
![Fixture richness figure used for CI cross-reference and image embedding checks.](../figures/fig2_dummy.png){#fig-fixture-richness width=85%}
![Fixture supplementary figure used for supplementary material rendering checks.](../figures/figS1_dummy.png){#fig-fixture-s1 width=85%}
EOF

	cat > "$cfg" <<EOF
default_profile: captions
profiles:
  captions:
    manuscript_sources:
      - ../manuscript/text/captions-main.md
      - ../manuscript/text/captions-figures.md
    lint_sources:
      - ../manuscript/text/captions-main.md
      - ../manuscript/text/captions-figures.md
    bibliography: ../references/fixture_refs.yaml
    csl: ../csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - ../csl
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
	assert_line_count_at_least "$prepared" "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>" 5
	assert_contains "$prepared" "![Fixture main figure used for CI layout and rendering checks.]($fig1_path){#fig-fixture-main width=95%}"
	assert_contains "$prepared" "![Fixture richness figure used for CI cross-reference and image embedding checks.]($fig2_path){#fig-fixture-richness width=85%}"
	assert_contains "$prepared" "![Fixture supplementary figure used for supplementary material rendering checks.]($figS1_path){#fig-fixture-s1 width=85%}"
	assert_exact_line "$prepared" "**Fig. 1.**"
	assert_exact_line "$prepared" "**Fig. 2.**"
	assert_exact_line "$prepared" "**Fig. S1.**"
}

main() {
	local tmp_dir
	tmp_dir="$(mktemp -d)"
	TMP_DIR="$tmp_dir"
	trap cleanup_tmpdir EXIT

	run_pages_mode_check "$tmp_dir"
	run_inline_bottom_check "$tmp_dir"
	run_inline_empty_alt_suppresses_auto_caption_check "$tmp_dir"
	run_captions_page_check "$tmp_dir"
	echo "PASS: figure mode regression checks passed."
}

main "$@"
