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

assert_dist_only_has_dir() {
	local expected_dir=$1
	local top_dirs
	top_dirs="$(find dist -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)"
	if [ -n "$top_dirs" ] && [ "$top_dirs" != "$expected_dir" ]; then
		echo "ASSERTION FAILED: expected only dist/$expected_dir directory, found: $top_dirs" >&2
		exit 1
	fi
}

run_fallback_output_dir() {
	local tmp_dir
	local cfg
	local src
	local csl
	local bib
	local expected_output_dir
	local expected_stem

	tmp_dir="$(mktemp -d)"
	cfg="$tmp_dir/build.yaml"
	src="$tmp_dir/main.md"
	csl="$tmp_dir/fixture_style.csl"
	bib="$tmp_dir/fixture_refs.yaml"

	cat > "$src" <<'EOF'
# Fallback Profile Probe

This document has no repository context and no `manuscript/` path segment.
EOF

	cp "testbed/csl/fixture_style.csl" "$csl"
	cp "testbed/references/fixture_refs.yaml" "$bib"

	cat > "$cfg" <<EOF
default_profile: standalone

profiles:
  standalone:
    manuscript_sources:
      - $src
    lint_sources:
      - $src
    bibliography: $bib
    csl: $csl
    journal: Fallback
    csl_search_dirs:
      - $tmp_dir
    output_dir: dist
    output_stem: standalone
    page_numbers: lower_right
    line_spacing: single
    line_numbering: continuous
EOF

	expected_output_dir="$(python3 scripts/build_profile.py --config "$cfg" --profile standalone value --key output_dir)"
	expected_stem="$(python3 scripts/build_profile.py --config "$cfg" --profile standalone value --key output_stem)"

	make clean >/dev/null
	make CONFIG="$cfg" PROFILE=standalone all

	assert_dir_exists "$expected_output_dir"
	assert_file_exists "$expected_output_dir/$expected_stem.pdf"
	assert_file_exists "$expected_output_dir/$expected_stem.docx"
	assert_file_exists "$expected_output_dir/${expected_stem}_build_manifest.json"
	assert_no_root_artifacts
	case "$expected_output_dir" in
		dist/manuscript-*) ;;
		*)
			echo "ASSERTION FAILED: expected fallback output_dir dist/manuscript-*, got: $expected_output_dir" >&2
			exit 1
			;;
	esac

	make clean >/dev/null
	rm -rf "$tmp_dir"
}

run_testbed_target() {
	make clean >/dev/null
	make testbed

	assert_dir_exists dist/fixture
	assert_file_exists dist/fixture/fixture_manuscript.pdf
	assert_file_exists dist/fixture/fixture_manuscript.docx
	assert_file_exists dist/fixture/fixture_manuscript_build_manifest.json
	assert_no_root_artifacts
	assert_dist_only_has_dir fixture
}

run_fixture_profile_all() {
	make clean >/dev/null
	make fixture-all

	assert_file_exists dist/fixture/fixture_manuscript.pdf
	assert_file_exists dist/fixture/fixture_manuscript.docx
	assert_file_exists dist/fixture/fixture_manuscript_build_manifest.json
	assert_no_root_artifacts
	assert_dist_only_has_dir fixture
}

run_default_profile_all() {
	make clean >/dev/null
	make all

	assert_file_exists dist/testbed/manuscript.pdf
	assert_file_exists dist/testbed/manuscript.docx
	assert_file_exists dist/testbed/manuscript_build_manifest.json
	python3 - <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path("dist/testbed/manuscript_build_manifest.json").read_text(encoding="utf-8"))
input_paths = {Path(record["path"]).resolve() for record in manifest["inputs"]}
expected = {
    Path("settings/build.yaml").resolve(),
    Path("testbed/manuscript/authors.yaml").resolve(),
}
missing = expected - input_paths
if missing:
    print("ASSERTION FAILED: manifest missing provenance inputs:", file=sys.stderr)
    for path in sorted(missing):
        print(f"  - {path}", file=sys.stderr)
    raise SystemExit(1)
PY
	if [ -f dist/fixture/fixture_manuscript.pdf ] || [ -f dist/fixture/fixture_manuscript.docx ] || [ -f dist/fixture/golden_check.txt ]; then
		echo "ASSERTION FAILED: default build unexpectedly created fixture artifacts" >&2
		exit 1
	fi
}

run_config_change_rebuilds_docx() {
	local tmp_dir
	local cfg
	local src
	local csl
	local bib
	local docx_path
	local manifest_path
	local before_mtime
	local after_mtime

	tmp_dir="$(mktemp -d)"
	cfg="$tmp_dir/build.yaml"
	src="$tmp_dir/main.md"
	csl="$tmp_dir/fixture_style.csl"
	bib="$tmp_dir/fixture_refs.yaml"
	docx_path="dist/rebuild-probe/manuscript.docx"
	manifest_path="dist/rebuild-probe/manuscript_build_manifest.json"

	cat > "$src" <<'EOF'
# Config Rebuild Probe

Citation [@alpha2020SyntheticWorkflow].
EOF

	cp "testbed/csl/fixture_style.csl" "$csl"
	cp "testbed/references/fixture_refs.yaml" "$bib"

	cat > "$cfg" <<EOF
default_profile: rebuild

profiles:
  rebuild:
    manuscript_sources:
      - $src
    bibliography: $bib
    csl: $csl
    output_dir: dist/rebuild-probe
    output_stem: manuscript
    page_numbers: lower_right
    line_spacing: single
    line_numbering: none
EOF

	make clean >/dev/null
	make CONFIG="$cfg" PROFILE=rebuild all >/dev/null
	assert_file_exists "$docx_path"
	before_mtime="$(python3 - "$docx_path" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).stat().st_mtime_ns)
PY
)"

	sleep 1
	python3 - "$cfg" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
path.write_text(path.read_text(encoding="utf-8").replace("line_spacing: single", "line_spacing: 2"), encoding="utf-8")
PY
	make CONFIG="$cfg" PROFILE=rebuild all >/dev/null
	after_mtime="$(python3 - "$docx_path" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).stat().st_mtime_ns)
PY
)"

	if [ "$before_mtime" = "$after_mtime" ]; then
		echo "ASSERTION FAILED: DOCX was not rebuilt after profile line_spacing changed" >&2
		exit 1
	fi
	python3 - "$manifest_path" <<'PY'
import json
import sys
from pathlib import Path
manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if manifest["profile"]["line_spacing"] != "2":
    print("ASSERTION FAILED: manifest did not capture updated line_spacing", file=sys.stderr)
    raise SystemExit(1)
PY

	rm -rf "$tmp_dir" dist/rebuild-probe
}

run_testbed_target
run_fixture_profile_all
run_default_profile_all
run_fallback_output_dir
run_config_change_rebuilds_docx

echo "PASS: output routing regression checks passed."
