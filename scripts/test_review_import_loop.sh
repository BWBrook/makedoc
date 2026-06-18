#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

EVIDENCE_DIR="dist/review-import-loop"
ORIGINAL_MD="$TMP_DIR/review_import_original.md"
REVISED_DOCX="$TMP_DIR/review_import_revised.docx"
CONFIG_PATH="$TMP_DIR/review_import_loop.yaml"
PREPARED_MD="$TMP_DIR/review_import_prepared.md"
PDF_TEXT="$TMP_DIR/review_import_pdf.txt"
DOCX_XML="$TMP_DIR/review_import_docx.xml"

CANDIDATE_MD="$EVIDENCE_DIR/review_import_candidate.md"
PDF_OUT="$EVIDENCE_DIR/review_import_loop.pdf"
DOCX_OUT="$EVIDENCE_DIR/review_import_loop.docx"
MANIFEST_OUT="$EVIDENCE_DIR/review_import_loop_build_manifest.json"

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Missing required command for review-import loop proof: $command_name" >&2
    exit 1
  }
}

require_contains() {
  local path="$1"
  local needle="$2"
  local label="$3"
  if ! grep -Fq "$needle" "$path"; then
    echo "Missing expected review-import marker ($label): $needle" >&2
    echo "Inspected file: $path" >&2
    exit 1
  fi
}

require_not_contains() {
  local path="$1"
  local needle="$2"
  local label="$3"
  if grep -Fq "$needle" "$path"; then
    echo "Unexpected unrendered review-import token ($label): $needle" >&2
    echo "Inspected file: $path" >&2
    exit 1
  fi
}

require_command pdftotext
require_command unzip

rm -rf "$EVIDENCE_DIR"
mkdir -p "$EVIDENCE_DIR"

cat > "$ORIGINAL_MD" <<'EOF'
The baseline remove context old.

Second paragraph remains stable.
EOF

python3 - "$REVISED_DOCX" <<'PY'
import sys
import zipfile
from pathlib import Path

word_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
body_xml = (
    "<w:p><w:r><w:t>The inserted baseline context new.</w:t></w:r></w:p>"
    "<w:p><w:r><w:t>Second paragraph remains stable.</w:t></w:r></w:p>"
)
document_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:document xmlns:w="{word_ns}"><w:body>{body_xml}</w:body></w:document>'
)
with zipfile.ZipFile(Path(sys.argv[1]), "w") as archive:
    archive.writestr("word/document.xml", document_xml)
PY

python3 scripts/import_docx_review_markup.py revised-candidate \
  --original-path "$ORIGINAL_MD" \
  --revised-docx "$REVISED_DOCX" \
  --output "$CANDIDATE_MD"

require_contains "$CANDIDATE_MD" "{++ inserted ++}" "candidate addition token"
require_contains "$CANDIDATE_MD" "{-- remove --}" "candidate deletion token"
require_contains "$CANDIDATE_MD" "{~~ old. ~> new. ~~}" "candidate substitution token"

cat > "$CONFIG_PATH" <<EOF
default_profile: review_import_loop

profiles:
  review_import_loop:
    description: Synthetic end-to-end DOCX import to review-markup render proof.
    manuscript_sources:
      - $ROOT_DIR/$CANDIDATE_MD
    lint_sources:
      - $ROOT_DIR/$CANDIDATE_MD
    bibliography: $ROOT_DIR/testbed/references/fixture_refs.yaml
    csl: $ROOT_DIR/testbed/csl/fixture_style.csl
    journal: Synthetic
    output_dir: $ROOT_DIR/$EVIDENCE_DIR
    output_stem: review_import_loop
    page_numbers: none
    line_spacing: single
    line_numbering: none
    references_new_page: false
    review_markup:
      enabled: true
    figures:
      placement: pages
      caption_position: top
      placeholder_id: figures
    margins:
      unit: cm
      paper_size: a4
      top: 2.0
      bottom: 2.0
      left: 2.5
      right: 2.5
EOF

python3 scripts/prepare_markdown_sources.py \
  --config "$CONFIG_PATH" \
  --profile review_import_loop \
  --output "$PREPARED_MD"

require_contains "$PREPARED_MD" "**[+ inserted +]**" "prepared addition"
require_contains "$PREPARED_MD" "**[- remove -]**" "prepared deletion"
require_contains "$PREPARED_MD" "**[- old. -]** **[+ new. +]**" "prepared substitution"
require_not_contains "$PREPARED_MD" "{++ inserted ++}" "prepared raw addition token"
require_not_contains "$PREPARED_MD" "{-- remove --}" "prepared raw deletion token"
require_not_contains "$PREPARED_MD" "{~~ old. ~> new. ~~}" "prepared raw substitution token"

MAKE_CMD="${MAKE:-make}"
CONFIG="$CONFIG_PATH" PROFILE=review_import_loop "$MAKE_CMD" -B all

test -f "$PDF_OUT" || { echo "Missing review-import PDF: $PDF_OUT" >&2; exit 1; }
test -f "$DOCX_OUT" || { echo "Missing review-import DOCX: $DOCX_OUT" >&2; exit 1; }
test -f "$MANIFEST_OUT" || {
  echo "Missing review-import build manifest: $MANIFEST_OUT" >&2
  exit 1
}

pdftotext "$PDF_OUT" "$PDF_TEXT"
unzip -p "$DOCX_OUT" word/document.xml > "$DOCX_XML"

require_contains "$PDF_TEXT" "[+ inserted +]" "PDF addition"
require_contains "$PDF_TEXT" "[- remove -]" "PDF deletion"
require_contains "$PDF_TEXT" "[- old. -]" "PDF substitution deletion"
require_contains "$PDF_TEXT" "[+ new. +]" "PDF substitution addition"

require_contains "$DOCX_XML" "[+ inserted +]" "DOCX addition"
require_contains "$DOCX_XML" "[- remove -]" "DOCX deletion"
require_contains "$DOCX_XML" "[- old. -]" "DOCX substitution deletion"
require_contains "$DOCX_XML" "[+ new. +]" "DOCX substitution addition"
require_contains "$DOCX_XML" "<w:b />" "DOCX bold marker styling"
require_not_contains "$DOCX_XML" "<w:strike" "DOCX strikeout styling"
require_not_contains "$DOCX_XML" "<ns0:strike" "DOCX strikeout styling"

echo "PASS: synthetic review-import loop proof passed."
echo "Evidence written under: $EVIDENCE_DIR"
