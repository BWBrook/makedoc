# Runbook: Structured DOCX Import Preflight Output

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
4d1786a
4d1786a Add DOCX import preflight report
```

Read repo-local `AGENTS.md` first.

## Preflight Commands

Default human-readable text:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path path/to/original.md
```

Structured JSON:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path path/to/original.md \
  --format json
```

Expected JSON fields:

```json
{
  "status": "SAFE_TO_ATTEMPT",
  "path": "/absolute/path/to/original.md",
  "total_blocks": 1,
  "eligible_blocks": 1,
  "refused_blocks": 0,
  "safe_to_attempt": true,
  "refusals": []
}
```

Refusal objects include:

```json
{
  "block": 1,
  "start_line": 1,
  "end_line": 3,
  "line": 1,
  "reason": "unsupported Markdown front matter or thematic break"
}
```

Exit policy:

- `0`: preflight report produced, including reports with refused blocks.
- non-zero: CLI, file, or runtime error.

Invalid `--format` values should fail via argparse choices.

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
changed files, CLI shape, JSON field summary, exit-code policy, no-prose
behavior, tests, validation, final status, and explicit boundary
confirmations.

Stop after the wake-up.
