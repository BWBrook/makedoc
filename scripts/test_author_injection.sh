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

assert_not_contains() {
	local file=$1
	local pattern=$2
	if grep -Fq -- "$pattern" "$file"; then
		echo "ASSERTION FAILED: unexpected pattern found in $file: $pattern" >&2
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

assert_two_blank_lines_before() {
	local file=$1
	local heading_pattern=$2
	local heading_line
	heading_line="$(first_match_line "$file" "$heading_pattern")"
	if [ -z "$heading_line" ] || [ "$heading_line" -lt 3 ]; then
		echo "ASSERTION FAILED: heading not found or too early for blank-line check in $file: $heading_pattern" >&2
		exit 1
	fi
	local prev1 prev2
	prev1="$(sed -n "$((heading_line - 1))p" "$file")"
	prev2="$(sed -n "$((heading_line - 2))p" "$file")"
	if [ -n "${prev1//[[:space:]]/}" ] || [ -n "${prev2//[[:space:]]/}" ]; then
		echo "ASSERTION FAILED: expected two blank lines before '$heading_pattern' in $file" >&2
		exit 1
	fi
}

write_authors_yaml() {
	local path=$1
	cat > "$path" <<'EOF'
title_note: Synthetic author metadata block
authors:
  - name: Ava K. Morgan
    affiliations: [aff1, aff2]
    corresponding: true
    email: ava.morgan@example.org
  - name: Theo J. Patel
    affiliations: [aff2]
affiliations:
  aff1: Department of Synthetic Ecology, Harborview University
  aff2: Centre for Reproducible Workflows, Southern Institute of Systems Science
EOF
}

run_placeholder_replacement_check() {
	local tmp_dir=$1
	local cfg=$2

	local main_file="$tmp_dir/placeholder-main.md"
	local prepared="$tmp_dir/placeholder-prepared.md"
	local author_file="$tmp_dir/authors.yaml"

	write_authors_yaml "$author_file"

	cat > "$main_file" <<'EOF'
# Author Injection Placeholder Check

<div id="authors"></div>

## Abstract

Synthetic abstract body.

## Keywords

workflow; fixtures

## Introduction

Body starts here.

## References

Dummy reference list placeholder.
EOF

	cat > "$cfg" <<EOF
default_profile: placeholder
profiles:
  placeholder:
    manuscript_sources:
      - $main_file
    bibliography: $REPO_ROOT/testbed/references/fixture_refs.yaml
    csl: $REPO_ROOT/testbed/csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - $REPO_ROOT/testbed/csl
    output_dir: dist/authors-check
    output_stem: authors
    author_metadata: $author_file
    page_numbers: lower_right
    line_spacing: single
    line_numbering: none
EOF

	python3 scripts/prepare_markdown_sources.py --config "$cfg" --profile placeholder --output "$prepared"
	assert_file_exists "$prepared"

	assert_not_contains "$prepared" "<div id=\"authors\"></div>"
	assert_contains "$prepared" "Ava K. Morgan*^1,2^, Theo J. Patel^2^"
	assert_contains "$prepared" "1. Department of Synthetic Ecology, Harborview University"
	assert_contains "$prepared" "2. Centre for Reproducible Workflows, Southern Institute of Systems Science"
	assert_contains "$prepared" "**Corresponding author:** Ava K. Morgan (ava.morgan@example.org)"
	assert_ordered_lines "$prepared" "# Author Injection Placeholder Check" "Ava K. Morgan*^1,2^, Theo J. Patel^2^" "## Abstract"
	assert_pattern_between "$prepared" "\\clearpage" "Ava K. Morgan*^1,2^, Theo J. Patel^2^" "## Abstract"
	assert_pattern_between "$prepared" "\\clearpage" "## Keywords" "## Introduction"
	assert_pattern_between "$prepared" "\\clearpage" "## Introduction" "## References"
	assert_line_count_at_least "$prepared" "\\clearpage" 3
	assert_line_count_at_least "$prepared" "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>" 3
	assert_two_blank_lines_before "$prepared" "## Keywords"
}

run_after_title_fallback_check() {
	local tmp_dir=$1
	local cfg=$2

	local main_file="$tmp_dir/fallback-main.md"
	local prepared="$tmp_dir/fallback-prepared.md"
	local author_file="$tmp_dir/authors-fallback.yaml"

	write_authors_yaml "$author_file"

	cat > "$main_file" <<'EOF'
# Author Injection Fallback Check

Body starts here.

## References

Dummy reference list placeholder.
EOF

	cat > "$cfg" <<EOF
default_profile: fallback
profiles:
  fallback:
    manuscript_sources:
      - $main_file
    bibliography: $REPO_ROOT/testbed/references/fixture_refs.yaml
    csl: $REPO_ROOT/testbed/csl/fixture_style.csl
    journal: Oikos
    csl_search_dirs:
      - $REPO_ROOT/testbed/csl
    output_dir: dist/authors-check
    output_stem: authors_fallback
    author_metadata: $author_file
    page_numbers: lower_right
    line_spacing: single
    line_numbering: none
EOF

	python3 scripts/prepare_markdown_sources.py --config "$cfg" --profile fallback --output "$prepared"
	assert_file_exists "$prepared"
	assert_ordered_lines "$prepared" "# Author Injection Fallback Check" "Ava K. Morgan*^1,2^, Theo J. Patel^2^" "Body starts here."
}

main() {
	local tmp_dir
	tmp_dir="$(mktemp -d)"
	local cfg
	cfg="$tmp_dir/test-config.yaml"
	TMP_DIR="$tmp_dir"
	trap cleanup_tmpdir EXIT

	run_placeholder_replacement_check "$tmp_dir" "$cfg"
	run_after_title_fallback_check "$tmp_dir" "$cfg"
	echo "PASS: author metadata injection checks passed."
}

main "$@"
