# Log: Text-Only DOCX Revision Import Candidate

## 2026-06-14 - Execution Started

Status: in progress.

Executor: `draftsman`.

Starting state confirmed in `/Users/bwbrook/work/makedoc`:

```text
pwd
/Users/bwbrook/work/makedoc
```

```text
git status --short --branch
## main...origin/main
```

```text
git rev-parse --short HEAD
bba8be2
```

```text
git log -1 --oneline
bba8be2 Add DOCX review import feasibility spike
```

Required context read before implementation:

- `AGENTS.md`
- `README.md`
- `docs/docx_review_import_spike.md`
- `docs/review_markup_external_adoption.md`
- `scripts/import_docx_review_markup.py`
- `tests/test_import_docx_review_markup.py`
- `docs/goals/006-docx-review-import-feasibility/Goal.md`
- `docs/goals/006-docx-review-import-feasibility/Plan.md`
- `docs/goals/006-docx-review-import-feasibility/Runbook.md`
- `docs/goals/006-docx-review-import-feasibility/Log.md`

Repo-local `AGENTS.md` also required broader first reads before substantial
changes, so these were read for consistency:

- `docs/plan.md`
- `docs/builder_notes.md`
- `docs/makedoc_primer_for_agents.md`

CPE was not read or inspected.

## 2026-06-14 - Red Tests Added

Status: implementation in progress.

Extended `tests/test_import_docx_review_markup.py` first, before changing the
prototype script.

Initial focused test run:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: failed as expected. Existing Goal 006 tests still passed; new Goal 007
tests failed because `generate_revised_candidate` and the `revised-candidate`
CLI mode did not exist yet.

New test coverage targets:

- one simple paragraph with insertion, deletion, and substitution tokens;
- multiple paragraphs preserving blank-line separation;
- paragraph-count mismatch refusal;
- unsupported figure/image line refusal;
- unsupported Markdown table refusal;
- output path resolving to original path refusal;
- existing output refusal by default;
- CLI non-zero refusal with an explicit error message.

## 2026-06-14 - Candidate Mode Implemented

Status: validation pending.

Extended:

```text
scripts/import_docx_review_markup.py
```

Added experimental `revised-candidate` mode:

```sh
python3 scripts/import_docx_review_markup.py revised-candidate \
  --original-path path/to/original.md \
  --revised-docx path/to/revised.docx \
  --output path/to/candidate.md
```

Implementation choice:

- keep using Python stdlib DOCX ZIP/XML extraction and `difflib`;
- validate original Markdown shape before writing;
- support only simple prose paragraphs split by blank lines;
- compare each original/revised paragraph with the existing word-diff token
  renderer;
- write a separate output file only after all validation passes;
- return exit status `2` for explicit candidate-generation refusals.

Safety/refusal policy implemented:

- fenced code blocks;
- indented code blocks;
- Markdown tables;
- figure/image lines;
- HTML comments and raw HTML blocks;
- headings;
- blockquotes;
- bullet and numbered lists;
- bracketed Pandoc citation markers;
- existing review-markup tokens;
- paragraph-count mismatch;
- output path equal to original path;
- existing output path unless `--overwrite` is supplied.

Focused test run after implementation:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 11 tests.

CPE and unrelated repos were not touched.

## 2026-06-14 - Validation Complete

Status: complete.

Changed files:

```text
docs/docx_review_import_spike.md
scripts/import_docx_review_markup.py
tests/test_import_docx_review_markup.py
docs/goals/007-text-only-docx-revision-import/Goal.md
docs/goals/007-text-only-docx-revision-import/Plan.md
docs/goals/007-text-only-docx-revision-import/Runbook.md
docs/goals/007-text-only-docx-revision-import/Log.md
```

Validation commands run sequentially:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
```

Result: passed.

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 11 tests.

```text
make test-review-markup
```

Result: passed; 12 review-markup tests passed, review profile config
validation passed, proof DOCX build and review-markup regression checks passed.

```text
make check
```

Result: passed; tool check, config validation, 48 discovered Python tests,
manuscript lint, reference audit, author metadata injection, and build check
passed.

```text
git diff --check
```

Result: passed, then passed again after this validation log update.

Candidate behavior added:

- new `revised-candidate` CLI mode writes a separate Markdown candidate file;
- original and revised text are mapped paragraph-by-paragraph;
- blank-line paragraph separation is preserved;
- insertions, deletions, and substitutions use current Makedoc source tokens;
- the mode refuses unsafe inputs with exit status `2`;
- existing Goal 006 `revised` and `track-changes` routes remain covered.

Refusal cases covered by tests:

- paragraph-count mismatch;
- figure/image source line;
- Markdown table;
- output path resolving to the original path;
- existing output file by default;
- CLI refusal for unsupported Markdown.

Decision memo updated:

```text
docs/docx_review_import_spike.md
```

Memo recommendation: keep this as an experimental human-reviewed utility for
toy/simple prose. Do not present it as real manuscript round-tripping. Before
real manuscript adoption, add approved manuscript-like fixtures and decide
whether citations, headings, lists, figures, tables, and references remain
hard refusals or receive explicit support one by one. Native Track Changes
hardening remains deferred.

Final `git status --short --branch` before log append:

```text
## main...origin/main
 M docs/docx_review_import_spike.md
 M scripts/import_docx_review_markup.py
 M tests/test_import_docx_review_markup.py
?? docs/goals/007-text-only-docx-revision-import/
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, rebases, branch switches, dependency installs, generated artifact
force-adds, CPE access, CPE mutation, unrelated repo reads, native Word
automation, remote services, outbound rendering changes, profile schema
changes, Make build graph changes, adoption-playbook changes, or Goal 008 work
were performed.

Recommended next step: orchestrator review. If accepted, publish the Goal 007
source/docs/test stack. If Barry wants real manuscript use, assign a later
hardening goal with approved examples and explicit support/refusal decisions
for manuscript structures.
