# Runbook: DOCX Import Preflight and Refusal Report

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
78b24a9
78b24a9 Record CPE DOCX import readiness trial
```

Read repo-local `AGENTS.md` first.

## Preflight Command

Run from makedoc:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path path/to/original.md
```

Expected report shape:

```text
DOCX revised-candidate preflight
Overall status: SAFE_TO_ATTEMPT
Blocks considered: <n>
Eligible simple-prose paragraphs: <n>
Refused blocks: <n>
Safe to attempt revised-candidate: yes
```

When refused blocks are present, the report should include block and line
references plus refusal reasons, but not source prose.

Exit policy:

- `0`: preflight report produced, including reports with refused blocks.
- non-zero: CLI, file, or runtime error.

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
changed files, CLI shape, exit-code policy, report behavior, tests,
validation, final status, and explicit boundary confirmations.

Stop after the wake-up.
