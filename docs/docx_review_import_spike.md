# DOCX Review Import Feasibility Spike

Date: 2026-06-14

## Decision

Do not build a full production DOCX-to-Markdown review importer yet.

The spike shows that two narrow routes are technically possible for simple
prose, but both become fragile once real manuscript structure matters. If Barry
wants this capability next, the safest next goal is a constrained text-only
prototype for plain paragraphs using the revised-DOCX text-diff route. Native
Word Track Changes import should remain a separate, narrower OOXML spike until
there is a small corpus of real tracked-change documents and clear policy for
comments, moves, formatting, tables, citations, and figure references.

## Routes Tested

### Route 1: Revised DOCX Text Diff

Prototype function:

```text
revised_docx_to_review_markup(original_text, revised_docx)
```

The script extracts simple revised paragraph text from `word/document.xml`,
ignoring native deleted text and including inserted text. It then uses a
normalized word diff against original text and emits Makedoc review tokens:

- insertions as `{++ inserted ++}`
- deletions as `{-- deleted --}`
- replacements as `{~~ old ~> new ~~}`

Evidence test:

```text
original: alpha beta remove gamma old
revised:  alpha inserted beta gamma new
output:   alpha {++ inserted ++} beta {-- remove --} gamma {~~ old ~> new ~~}
```

What worked:

- Simple word-level insertions, deletions, and substitutions can be represented
  as current Makedoc review-markup source tokens.
- The route needs only Python stdlib ZIP/XML parsing and `difflib`.
- Tiny DOCX fixtures can be generated in tests without committing binary DOCX
  files.

What is fragile:

- DOCX-derived text has already lost source Markdown structure.
- Mapping revised prose back onto Markdown with citations, figure links,
  headings, tables, reference sections, raw blocks, and line breaks is the real
  hard problem.
- Word-level diffs can be noisy for moved text, punctuation, sentence rewrites,
  citation edits, and paragraph splits/merges.
- An accepted/revised DOCX does not preserve reviewer intent; it only gives a
  before/after text comparison.

Production hardening would require:

- a Markdown normalization and paragraph-mapping layer;
- policy for citation syntax, figure references, links, tables, and headings;
- review UI or human confirmation for ambiguous diffs;
- clear unsupported cases and failure modes;
- manuscript-scale fixtures that remain synthetic or explicitly approved.

### Route 2: Native Track Changes OOXML

Prototype function:

```text
track_changes_docx_to_review_markup(docx)
```

The script reads tiny native Word Track Changes OOXML and converts simple
`w:ins` and `w:del` elements in document order:

- `w:ins` text -> `{++ inserted ++}`
- `w:del` / `w:delText` text -> `{-- deleted --}`

Evidence test:

```text
OOXML order: alpha, w:ins(inserted), beta, w:del(removed), gamma
output:      alpha {++ inserted ++} beta {-- removed --} gamma
```

What worked:

- Tiny synthetic OOXML with `w:ins` and `w:del` can be read directly.
- Deleted text stored in `w:delText` can be recovered.
- The route preserves explicit change intent better than a plain text diff
  when the OOXML is simple.

What is fragile:

- Real Word Track Changes OOXML is more complicated than the tiny fixture:
  changes can cross runs, include formatting changes, contain moves, appear in
  tables/headers/footnotes/comments, and interact with field codes.
- Pairing adjacent delete/insert elements into substitutions is a policy
  decision, not just parsing.
- Comments and reviewer metadata are separate OOXML structures and were not
  handled.
- Mapping changed OOXML back to the original Markdown source remains unsolved.

Production hardening would require:

- a focused OOXML parser with a real tracked-change fixture corpus;
- explicit support or rejection for moves, comments, formatting-only changes,
  tables, headers/footers, footnotes, citations, and figure references;
- paragraph/source mapping back to Markdown;
- tests for common Word export variations.

## Prototype

Added experimental script:

```text
scripts/import_docx_review_markup.py
```

The script has two CLI modes:

```sh
python3 scripts/import_docx_review_markup.py revised \
  --original-text "alpha beta remove gamma old" \
  --revised-docx /path/to/revised.docx

python3 scripts/import_docx_review_markup.py track-changes \
  --docx /path/to/tracked.docx
```

The script is intentionally text-first and dependency-light. It does not import
or modify manuscript repositories.

## Validation

Focused tests use generated temporary DOCX ZIP/XML fixtures:

```text
tests/test_import_docx_review_markup.py
```

Validation commands:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
python3 -m unittest tests/test_import_docx_review_markup.py
make test-review-markup
git diff --check
```

## Recommendation

Defer a production importer for now.

If the capability becomes important, pursue only a constrained text-only next
goal first:

1. Use revised DOCX text extraction plus original Markdown/plain-text
   normalization.
2. Limit scope to simple prose paragraphs.
3. Emit review tokens into a separate candidate Markdown file, never directly
   over canonical manuscript source.
4. Require human review before adopting changes.
5. Keep native Track Changes OOXML import as a separate spike until real
   tracked-change examples and policy decisions are available.

Do not promise round-tripping of Word edits into manuscript Markdown without
substantial hardening and human-in-the-loop review.
