# DOCX Review Import Feasibility Spike

Date: 2026-06-14

## Decision

Do not build a full production DOCX-to-Markdown review importer yet.

The spike shows that two narrow routes are technically possible for simple
prose, but both become fragile once real manuscript structure matters. Goal 007
added a constrained text-only candidate-file prototype for plain paragraphs
using the revised-DOCX text-diff route. It is useful as a human-reviewed
candidate generator, not as round-tripping.

Native Word Track Changes import should remain a separate, narrower OOXML spike
until there is a small corpus of real tracked-change documents and clear policy
for comments, moves, formatting, tables, citations, and figure references.

Goal 008 added a synthetic manuscript-like dry run and an operator note:

```text
docs/docx_review_import_operator_note.md
```

Use that note before running `revised-candidate`. It states the simple-prose
preconditions, preflight workflow, safe output handling, review checklist, and
refusal policy.

Goal 010 added a `preflight` mode so an operator can inspect an original source
for simple-prose eligibility before supplying a revised DOCX. The report gives
counts, block/line references, and refusal reasons without copying manuscript
prose by default.

Goal 011 added structured JSON output for that same preflight policy so agents
and automation can consume the report without scraping the human-readable text.
The text report remains the default.

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

The script has four CLI modes:

```sh
python3 scripts/import_docx_review_markup.py revised \
  --original-text "alpha beta remove gamma old" \
  --revised-docx /path/to/revised.docx

python3 scripts/import_docx_review_markup.py revised-candidate \
  --original-path /path/to/original.md \
  --revised-docx /path/to/revised.docx \
  --output /path/to/candidate.md

python3 scripts/import_docx_review_markup.py preflight \
  --original-path /path/to/original.md

python3 scripts/import_docx_review_markup.py preflight \
  --original-path /path/to/original.md \
  --format json

python3 scripts/import_docx_review_markup.py track-changes \
  --docx /path/to/tracked.docx
```

The script is intentionally text-first and dependency-light. It does not import
or modify manuscript repositories.

### Goal 007 candidate-file mode

`revised-candidate` writes a separate Markdown candidate file containing
Makedoc review-markup tokens. It is intended for human review of simple prose
only.

The mode:

- reads original Markdown/plain prose from `--original-path`;
- extracts revised DOCX text using the same revised-DOCX route as Goal 006;
- maps original and revised text paragraph-by-paragraph;
- preserves blank-line paragraph separation;
- emits `{++ inserted ++}`, `{-- deleted --}`, and
  `{~~ old ~> new ~~}` tokens;
- refuses to write directly over the original source;
- refuses to overwrite an existing output file unless `--overwrite` is passed;
- exits non-zero with an explicit refusal message for unsupported input.

Conservative refusal cases include:

- paragraph-count mismatches;
- fenced or indented code blocks;
- Markdown tables;
- front matter or thematic break delimiter lines;
- figure/image lines;
- raw HTML or HTML comments;
- headings, blockquotes, bullet lists, and numbered lists;
- bracketed Pandoc citation markers;
- existing review-markup tokens.

This mode deliberately refuses ordinary manuscript structures such as figures,
tables, headings, lists, and citations. That is the safety contract: candidate
generation is acceptable only when the source is simple enough that a human can
inspect the generated review tokens without hidden structural mapping claims.

### Goal 008 synthetic dry run

Goal 008 added a synthetic manuscript-like dry-run test with three simple prose
paragraphs. The generated temporary DOCX fixture made edits across paragraphs,
including insertion, deletion, substitution, and unchanged segments. The
candidate output preserved paragraph separation and placed review tokens in the
expected paragraphs.

Goal 008 also tightened citation refusal so narrative Pandoc citations such as
`@smith2020` are rejected, alongside bracketed citation forms such as
`[@smith2020]` and `[-@smith2020]`.

This remains a synthetic proof only. Real manuscript trials require a later
explicit goal and approved example material.

### Goal 009 controlled CPE readiness trial

Goal 009 used CPE only as an approved read-only proving ground and copied a
tiny simple-prose excerpt into `/tmp/makedoc-goal009-cpe-import/` for a
controlled trial. The trial succeeded on an excerpt that already satisfied the
operator-note preconditions: candidate output preserved paragraph separation
and produced sensible insertion, deletion, and substitution tokens.

This is a readiness finding, not production adoption. CPE was not mutated, and
real manuscript use should still require a later explicit goal with approved
examples and human review.

### Goal 010 preflight report

Goal 010 added:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path /path/to/original.md
```

The mode reads only the original Markdown/plain-prose source and writes no
candidate file. It reports:

- total non-empty blocks considered;
- eligible simple-prose paragraph count;
- refused block count;
- block and line references for each refusal;
- refusal reasons aligned with `revised-candidate`;
- an overall status, including `SAFE_TO_ATTEMPT` only when the whole source is
  eligible under current conservative rules.

The report intentionally does not include manuscript prose by default.
Preflight exits 0 when the report is produced, even if refused blocks are
present; non-zero status is reserved for CLI, file, or runtime errors.

This improves operator visibility before candidate generation but does not
broaden importer support. Citations, headings, lists, tables, figures, front
matter, thematic breaks, code, raw HTML, existing review markup, and other
unsupported manuscript structures remain refusals.

### Goal 011 structured preflight output

Goal 011 added:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path /path/to/original.md \
  --format json
```

The default remains `--format text`. JSON output uses only Python standard
library support and reports the same policy/data as the text report:

- `status`: `SAFE_TO_ATTEMPT`, `REFUSED`, or `NO_ELIGIBLE_BLOCKS`;
- `path`: absolute path to the preflighted source;
- `total_blocks`;
- `eligible_blocks`;
- `refused_blocks`;
- `safe_to_attempt`;
- `refusals`: objects with `block`, `start_line`, `end_line`, `line`, and
  `reason`.

JSON output intentionally does not include source prose, title text, heading
text, citation text, or paragraph text by default. Preflight still exits 0 when
the report is produced, including reports with refused blocks; non-zero status
is reserved for CLI, file, or runtime errors.

### Goal 013 eligible block reporting

Goal 013 extended structured preflight JSON with `eligible_blocks_detail`,
a prose-free array of eligible block references:

```json
{
  "block": 2,
  "start_line": 3,
  "end_line": 3
}
```

The field is intended for action-agent and operator workflows that need to
propose candidate simple-prose excerpt ranges for human approval without
copying manuscript text into logs or tracked notes. It does not broaden
importer support: headings, citations, figures, tables, lists, front matter,
raw HTML, code, and existing review markup remain refusals.

### Goal 015 synthetic review loop proof

Goal 015 added a rerunnable synthetic proof:

```sh
make test-review-import-loop
```

The target connects the text-only revised-DOCX candidate generator to the
visible review-markup renderer:

1. generate a temporary simple-prose original Markdown source;
2. generate a temporary synthetic revised DOCX;
3. run `revised-candidate` to write a separate candidate Markdown file;
4. prepare the candidate with `review_markup.enabled: true`;
5. build generated PDF/DOCX evidence;
6. inspect candidate tokens, prepared Markdown markers, PDF text, and DOCX XML
   for addition, deletion, and substitution traces.

Evidence is written under:

```text
dist/review-import-loop/
```

This remains synthetic evidence only. It proves the controlled operator loop
for simple prose, not general real-manuscript import or Word round-tripping.

## Validation

Focused tests use generated temporary DOCX ZIP/XML fixtures:

```text
tests/test_import_docx_review_markup.py
```

Validation commands:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
python3 -m unittest tests/test_import_docx_review_markup.py
make test-review-import-loop
make test-review-markup
git diff --check
```

## Recommendation

Defer a production importer for now.

The constrained text-only revised-DOCX route now has an experimental
candidate-file prototype. The next decision is whether this is enough as a
small human-reviewed utility, or whether Barry wants a separate hardening goal
with real approved examples.

Before any real manuscript adoption beyond toy/simple prose:

1. Keep candidate output separate from canonical manuscript source.
2. Require human review before copying any candidate tokens into manuscript
   history.
3. Add approved manuscript-like fixtures for paragraph mapping behavior.
4. Decide whether citations, headings, lists, figures, tables, and references
   should remain hard refusals or receive explicit support one by one.
5. Keep native Track Changes OOXML import as a separate spike until real
   tracked-change examples and policy decisions are available.

Do not promise round-tripping of Word edits into manuscript Markdown without
substantial hardening and human-in-the-loop review.
