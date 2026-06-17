# Runbook: CPE Structured DOCX Import Preflight Audit

## Makedoc Preflight

From `/Users/bwbrook/work/makedoc`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
git log -5 --oneline
```

Expected:

```text
## main...origin/main
4406365
4406365 Add structured DOCX import preflight output
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

## Audit Command

Run from makedoc:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path /Users/bwbrook/papers/cpe_time_to_extinction/manuscript/text/main.md \
  --format json \
  > /tmp/makedoc-goal012-cpe-preflight/cpe-main-preflight.json
```

Parse only metadata fields. Do not copy manuscript prose into tracked docs.

If the report unexpectedly returns `SAFE_TO_ATTEMPT`, stop and wake the
orchestrator before running `revised-candidate`.

## Evidence Paths

```text
/tmp/makedoc-goal012-cpe-preflight/cpe-main-preflight.json
/tmp/makedoc-goal012-cpe-preflight/cpe-main-preflight-summary.json
/tmp/makedoc-goal012-cpe-preflight/cpe-main-refusal-refs.json
```

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
changed files, makedoc and CPE before/after status, evidence paths, preflight
summary, no-prose confirmation, recommendations, validation, and explicit
boundary confirmations.

Stop after the wake-up.
