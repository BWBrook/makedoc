# Runbook: CPE Real-Manuscript Import Readiness

## Makedoc Preflight

From `/Users/bwbrook/work/makedoc`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
git log -3 --oneline
```

Expected:

```text
## main...origin/main
e23dbd2
e23dbd2 Add DOCX import synthetic dry run
```

Read makedoc `AGENTS.md` first.

## CPE Preflight

From `/Users/bwbrook/papers/cpe_time_to_extinction`, read `AGENTS.md` before
any inspection, then run:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
```

Expected:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
e1b2433
```

Do not mutate CPE.

## Trial Command

Create temporary files under `/tmp/makedoc-goal009-cpe-import/`, then run from
makedoc:

```sh
python3 scripts/import_docx_review_markup.py revised-candidate \
  --original-path /tmp/makedoc-goal009-cpe-import/<trial>/cpe_original_excerpt.md \
  --revised-docx /tmp/makedoc-goal009-cpe-import/<trial>/cpe_revised_excerpt.docx \
  --output /tmp/makedoc-goal009-cpe-import/<trial>/cpe_candidate.md
```

Inspect candidate paragraph count and review-token categories. Do not copy CPE
prose into tracked docs.

## Validation

Run sequentially from makedoc:

```sh
python3 -m py_compile scripts/import_docx_review_markup.py
python3 -m unittest tests/test_import_docx_review_markup.py
make test-review-markup
make check
git diff --check
```

## Wake-Up

Wake Makedoc orchestrator thread
`019eaf80-3882-7d31-b6a4-3cb4c2ab5699` with completion or blocker status,
changed files, CPE before/after status, safe excerpt result, temporary evidence
paths, validation, final statuses, and explicit boundary confirmations.

Stop after the wake-up.
