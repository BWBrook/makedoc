# Log: DOCX Import Synthetic Dry Run

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
c7adc67
```

```text
git log -1 --oneline
c7adc67 Add text-only DOCX revision candidate importer
```

Required context read before implementation:

- `AGENTS.md`
- `README.md`
- `docs/docx_review_import_spike.md`
- `docs/review_markup_external_adoption.md`
- `scripts/import_docx_review_markup.py`
- `tests/test_import_docx_review_markup.py`
- `docs/goals/007-text-only-docx-revision-import/Goal.md`
- `docs/goals/007-text-only-docx-revision-import/Plan.md`
- `docs/goals/007-text-only-docx-revision-import/Runbook.md`
- `docs/goals/007-text-only-docx-revision-import/Log.md`

Repo-local `AGENTS.md` also required broader first reads before substantial
changes, so these were read for consistency:

- `docs/plan.md`
- `docs/builder_notes.md`
- `docs/makedoc_primer_for_agents.md`

CPE was not read or inspected.

## 2026-06-14 - Red Tests Added

Status: implementation in progress.

Extended `tests/test_import_docx_review_markup.py` before changing the
prototype script.

Initial focused test run:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: failed as expected. The new narrative Pandoc citation refusal case
failed because `@smith2020` was not yet rejected. Existing positive and safety
behavior otherwise remained intact.

New test coverage targets:

- synthetic manuscript-like three-paragraph dry run with insertion, deletion,
  substitution, unchanged segments, and preserved paragraph separation;
- positive CLI smoke for `revised-candidate`;
- bracketed, suppressed-author, and narrative Pandoc citation refusals;
- heading, bullet list, and numbered list refusals.

Existing Goal 007 tests continue to cover paragraph-count mismatch,
figure/image refusal, table refusal, output-equals-original refusal, existing
output refusal, and CLI non-zero refusal.

## 2026-06-14 - Guardrail Tightened

Status: validation pending.

Changed:

```text
scripts/import_docx_review_markup.py
```

Implementation change: added conservative narrative Pandoc citation detection
for source lines such as `@smith2020`. This is a refusal-only hardening; no
new manuscript structures are supported.

Focused test run after the change:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 15 tests.

## 2026-06-14 - Operator Note And Memo Updated

Status: validation pending.

Added:

```text
docs/docx_review_import_operator_note.md
```

The operator note explains:

- when to use `revised-candidate`;
- simple-prose-only preconditions;
- separate candidate output handling;
- human review requirements;
- review checklist;
- refusal policy;
- real manuscript trial boundary.

Updated:

```text
docs/docx_review_import_spike.md
```

Memo now records Goal 008 synthetic dry-run status and points operators to the
operator note.

CPE and unrelated repos were not touched.

## 2026-06-14 - Validation Complete

Status: complete.

Changed files:

```text
docs/docx_review_import_spike.md
docs/docx_review_import_operator_note.md
scripts/import_docx_review_markup.py
tests/test_import_docx_review_markup.py
docs/goals/008-docx-import-synthetic-dry-run/Goal.md
docs/goals/008-docx-import-synthetic-dry-run/Plan.md
docs/goals/008-docx-import-synthetic-dry-run/Runbook.md
docs/goals/008-docx-import-synthetic-dry-run/Log.md
```

Validation commands run sequentially:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
```

Result: passed.

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 15 tests.

```text
make test-review-markup
```

Result: passed; 12 review-markup tests passed, review profile config
validation passed, proof DOCX build and review-markup regression checks passed.

```text
make check
```

Result: passed; tool check, config validation, 52 discovered Python tests,
manuscript lint, reference audit, author metadata injection, and build check
passed.

```text
git diff --check
```

Result: passed, then passed again after this validation log update.

Synthetic dry-run behavior added:

- generated temporary DOCX ZIP/XML fixture with three manuscript-like simple
  prose paragraphs;
- revised fixture includes insertion, deletion, substitution, and unchanged
  paragraph segments;
- candidate output preserves paragraph separation and places tokens in the
  expected paragraphs;
- CLI positive smoke verifies `revised-candidate` writes the candidate file.

Refusal guardrails covered:

- paragraph-count mismatch;
- figure/image source line;
- Markdown table;
- bracketed, suppressed-author, and narrative Pandoc citations;
- headings;
- bullet and numbered lists;
- output path resolving to original path;
- existing output file by default;
- CLI non-zero refusal for unsupported Markdown.

Importer change:

- added a conservative narrative Pandoc citation refusal regex;
- no new supported manuscript structures were introduced.

Operator-note summary:

- use `revised-candidate` only for simple prose paragraphs;
- write to a separate candidate path;
- inspect candidate output manually before adopting tokens;
- treat refusals as safety outcomes;
- require a later explicit goal and approved examples for CPE or any real
  manuscript trial.

Final `git status --short --branch` before log append:

```text
## main...origin/main
 M docs/docx_review_import_spike.md
 M scripts/import_docx_review_markup.py
 M tests/test_import_docx_review_markup.py
?? docs/docx_review_import_operator_note.md
?? docs/goals/008-docx-import-synthetic-dry-run/
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, rebases, branch switches, dependency installs, generated artifact
force-adds, CPE access, CPE mutation, unrelated repo reads, native Word
automation, remote services, outbound rendering changes, profile schema
changes, Make build graph changes, external-adoption playbook changes, or Goal
009 work were performed.

Recommended next step: orchestrator review. If accepted, publish the Goal 008
source/docs/test stack. A controlled real-manuscript trial should remain a
later explicit goal with approved example material.
