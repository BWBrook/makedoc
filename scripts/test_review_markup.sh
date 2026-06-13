#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PREPARED_MD="$TMP_DIR/review_markup_prepared.md"
PDF_TEXT="$TMP_DIR/review_markup_pdf.txt"
DOCX_XML="$TMP_DIR/review_markup_docx.xml"

PDF_OUT="dist/review-markup/review_markup_probe.pdf"
DOCX_OUT="dist/review-markup/review_markup_probe.docx"

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Missing required command for review-markup regression: $command_name" >&2
    exit 1
  }
}

require_contains() {
  local path="$1"
  local needle="$2"
  local label="$3"
  if ! grep -Fq "$needle" "$path"; then
    echo "Missing expected review-markup marker ($label): $needle" >&2
    echo "Inspected file: $path" >&2
    exit 1
  fi
}

require_not_contains() {
  local path="$1"
  local needle="$2"
  local label="$3"
  if grep -Fq "$needle" "$path"; then
    echo "Unexpected untransformed review-markup token ($label): $needle" >&2
    echo "Inspected file: $path" >&2
    exit 1
  fi
}

require_command pdftotext
require_command unzip

python3 -m unittest tests/test_prepare_markdown_sources.py

CONFIG=settings/review_markup.yaml make validate-config

python3 scripts/prepare_markdown_sources.py \
  --config settings/review_markup.yaml \
  --output "$PREPARED_MD"

require_contains "$PREPARED_MD" "**[+ inserted review text +]**" "prepared addition"
require_contains "$PREPARED_MD" "~~[- removed review text -]~~" "prepared deletion"
require_contains "$PREPARED_MD" "~~[- outdated wording -]~~ **[+ revised wording +]**" "prepared substitution"
require_contains "$PREPARED_MD" "**[Reviewer note: reviewer asks for a clearer transition]**" "prepared reviewer note"
require_contains "$PREPARED_MD" '`{++ literal addition ++}`' "inline code protection"
require_contains "$PREPARED_MD" "{-- fenced deletion should remain literal --}" "fenced code protection"
require_not_contains "$PREPARED_MD" "{++ inserted review text ++}" "active addition"
require_not_contains "$PREPARED_MD" "{-- removed review text --}" "active deletion"
require_not_contains "$PREPARED_MD" "{~~ outdated wording ~> revised wording ~~}" "active substitution"
require_not_contains "$PREPARED_MD" "{>> reviewer asks for a clearer transition <<}" "active reviewer note"

CONFIG=settings/review_markup.yaml make -B all

test -f "$PDF_OUT" || { echo "Missing review-markup PDF: $PDF_OUT" >&2; exit 1; }
test -f "$DOCX_OUT" || { echo "Missing review-markup DOCX: $DOCX_OUT" >&2; exit 1; }

pdftotext "$PDF_OUT" "$PDF_TEXT"
unzip -p "$DOCX_OUT" word/document.xml > "$DOCX_XML"

require_contains "$PDF_TEXT" "[+ inserted review text +]" "PDF addition"
require_contains "$PDF_TEXT" "[- removed review text -]" "PDF deletion"
require_contains "$PDF_TEXT" "[- outdated wording -] [+ revised wording +]" "PDF substitution"
require_contains "$PDF_TEXT" "[Reviewer note: reviewer" "PDF reviewer note"
require_contains "$PDF_TEXT" "{++ literal addition ++}" "PDF inline code protection"
require_contains "$PDF_TEXT" "{-- fenced deletion should remain literal --}" "PDF fenced code protection"

require_contains "$DOCX_XML" "[+ inserted review text +]" "DOCX addition"
require_contains "$DOCX_XML" "[- removed review text -]" "DOCX deletion"
require_contains "$DOCX_XML" "[- outdated wording -]" "DOCX substitution deletion"
require_contains "$DOCX_XML" "[+ revised wording +]" "DOCX substitution addition"
require_contains "$DOCX_XML" "[Reviewer note: reviewer asks for a clearer transition]" "DOCX reviewer note"
require_contains "$DOCX_XML" "<w:strike" "DOCX strikeout styling"
require_contains "$DOCX_XML" "{++ literal addition ++}" "DOCX inline code protection"
require_contains "$DOCX_XML" "{-- fenced deletion should remain literal --}" "DOCX fenced code protection"

echo "PASS: review markup regression checks passed."
