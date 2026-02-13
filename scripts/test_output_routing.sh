#!/usr/bin/env bash
set -euo pipefail

assert_file_exists() {
	local path=$1
	if [ ! -f "$path" ]; then
		echo "ASSERTION FAILED: expected file missing: $path" >&2
		exit 1
	fi
}

assert_dir_exists() {
	local path=$1
	if [ ! -d "$path" ]; then
		echo "ASSERTION FAILED: expected directory missing: $path" >&2
		exit 1
	fi
}

assert_no_root_artifacts() {
	# allow only fixture directory when testing fixture-only flow
	local artifact_count
	artifact_count="$(find dist -mindepth 1 -maxdepth 1 -type f | wc -l)"
	if [ "$artifact_count" -ne 0 ]; then
		echo "ASSERTION FAILED: expected no root files in dist/, found:" >&2
		find dist -mindepth 1 -maxdepth 1 -type f >&2
		exit 1
	fi
}

assert_dist_only_has_testbed() {
	local top_dirs
	top_dirs="$(find dist -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
	if [ -n "$top_dirs" ] && [ "$top_dirs" != "testbed" ]; then
		echo "ASSERTION FAILED: expected only dist/testbed directory, found: $top_dirs" >&2
		exit 1
	fi
}

run_testbed_target() {
	make clean >/dev/null
	make testbed

	assert_dir_exists dist/testbed
	assert_file_exists dist/testbed/fixture_manuscript.pdf
	assert_file_exists dist/testbed/fixture_manuscript.docx
	assert_file_exists dist/testbed/build_manifest.json
	assert_no_root_artifacts
	assert_dist_only_has_testbed
}

run_fixture_profile_all() {
	make clean >/dev/null
	make PROFILE=fixture all

	assert_file_exists dist/testbed/fixture_manuscript.pdf
	assert_file_exists dist/testbed/fixture_manuscript.docx
	assert_file_exists dist/testbed/build_manifest.json
	assert_no_root_artifacts
	assert_dist_only_has_testbed
}

run_default_profile_all() {
	make clean >/dev/null
	make all

	assert_file_exists dist/manuscript.pdf
	assert_file_exists dist/manuscript.docx
	assert_file_exists dist/build_manifest.json
	if [ -f dist/testbed/build_manifest.json ] || [ -f dist/testbed/fixture_manuscript.pdf ] || [ -f dist/testbed/fixture_manuscript.docx ]; then
		echo "ASSERTION FAILED: default build unexpectedly created fixture artifacts" >&2
		exit 1
	fi
}

run_testbed_target
run_fixture_profile_all
run_default_profile_all

echo "PASS: output routing regression checks passed."
