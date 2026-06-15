# Log: CPE Real-Manuscript Import Readiness

## 2026-06-15 - Execution Started

Status: in progress.

Executor: `draftsman`.

Makedoc starting state confirmed after reading repo-local `AGENTS.md`:

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
e23dbd2
```

Recent log context:

```text
e23dbd2 Add DOCX import synthetic dry run
c7adc67 Add text-only DOCX revision candidate importer
bba8be2 Add DOCX review import feasibility spike
```

CPE starting state confirmed after reading CPE repo-local `AGENTS.md`:

```text
pwd
/Users/bwbrook/papers/cpe_time_to_extinction
```

```text
git status --short --branch
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

```text
git rev-parse --short HEAD
e1b2433
```

Both repositories matched expected state. CPE pilot branch state was preserved
and not reconciled.

## 2026-06-15 - Context Read

Status: trial in progress.

Makedoc import/operator context read:

- `docs/docx_review_import_spike.md`
- `docs/docx_review_import_operator_note.md`
- `scripts/import_docx_review_markup.py`
- `tests/test_import_docx_review_markup.py`
- `docs/goals/008-docx-import-synthetic-dry-run/Log.md`

No Chief of Staff, Goal Composer, sibling repos, archive material, or unrelated
user files were read.

## 2026-06-15 - CPE Excerpt Audit

Status: trial in progress.

Read-only scan of CPE canonical manuscript source:

```text
/Users/bwbrook/papers/cpe_time_to_extinction/manuscript/text/main.md
```

The scan found multiple candidate paragraphs that met the current importer
preconditions: simple prose, blank-line paragraph boundaries, and no currently
refused Markdown structures.

Selected excerpt for the controlled trial:

```text
manuscript/text/main.md lines 23 and 27
```

Tracked docs intentionally do not copy the CPE prose. Structurally, the
selected excerpt consists of two standalone prose paragraphs with no headings,
citations, lists, tables, figure image lines, raw HTML, code blocks, or review
markup tokens.

## 2026-06-15 - Temporary Trial

Status: validation pending.

Temporary evidence directory:

```text
/tmp/makedoc-goal009-cpe-import/trial-20260615-141115/
```

Temporary files created:

```text
/tmp/makedoc-goal009-cpe-import/trial-20260615-141115/cpe_original_excerpt.md
/tmp/makedoc-goal009-cpe-import/trial-20260615-141115/cpe_revised_excerpt.docx
/tmp/makedoc-goal009-cpe-import/trial-20260615-141115/cpe_candidate.md
```

The original excerpt file contains only the selected CPE lines copied into
`/tmp`. The revised DOCX is a synthetic generated ZIP/XML fixture with small
edits to the excerpt. No CPE files were edited.

Trial command run from makedoc:

```sh
python3 scripts/import_docx_review_markup.py revised-candidate \
  --original-path /tmp/makedoc-goal009-cpe-import/trial-20260615-141115/cpe_original_excerpt.md \
  --revised-docx /tmp/makedoc-goal009-cpe-import/trial-20260615-141115/cpe_revised_excerpt.docx \
  --output /tmp/makedoc-goal009-cpe-import/trial-20260615-141115/cpe_candidate.md
```

Result: passed, exit status 0.

Candidate inspection summary:

- paragraph count: 2;
- insertion markers: 1;
- deletion markers: 1;
- substitution markers: 2;
- paragraph 1 contained the expected insertion and deletion markers;
- paragraph 2 contained the expected substitution markers;
- paragraph separation was preserved.

Readiness finding: the current importer can handle a tiny real CPE
simple-prose excerpt when the excerpt already satisfies the operator note
preconditions. This supports a later controlled real-manuscript hardening goal
with approved examples, but does not justify broader importer support or
general real-manuscript use yet.

CPE branch-fate recommendation: keep the preserved pilot branch unchanged until
Barry or the orchestrator explicitly authorizes cleanup, commit, disposal, or
formal manuscript-side publication.

## 2026-06-15 - Validation Complete

Status: complete.

Changed makedoc files:

```text
docs/docx_review_import_operator_note.md
docs/docx_review_import_spike.md
docs/goals/009-cpe-real-manuscript-import-readiness/Goal.md
docs/goals/009-cpe-real-manuscript-import-readiness/Plan.md
docs/goals/009-cpe-real-manuscript-import-readiness/Runbook.md
docs/goals/009-cpe-real-manuscript-import-readiness/Log.md
```

Validation commands run sequentially from makedoc:

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

Final makedoc `git status --short --branch` before log append:

```text
## main...origin/main
 M docs/docx_review_import_operator_note.md
 M docs/docx_review_import_spike.md
?? docs/goals/009-cpe-real-manuscript-import-readiness/
```

Final CPE status:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

Final CPE HEAD:

```text
e1b2433
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, rebases, branch switches, dependency installs, generated artifact
force-adds, CPE edits, CPE builds, CPE artifact regeneration, unrelated repo
reads, native Word automation, remote services, importer support broadening,
outbound rendering changes, profile schema changes, Make build graph changes,
or Goal 010 work were performed.

Recommended next step: orchestrator review. If accepted, publish the Goal 009
docs-only stack. For importer strategy, a later controlled real-manuscript
hardening goal is reasonable only with approved examples and explicit
support/refusal decisions; otherwise keep the importer as an experimental
simple-prose candidate generator.
