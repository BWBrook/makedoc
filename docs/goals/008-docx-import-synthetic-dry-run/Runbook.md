# Runbook: DOCX Import Synthetic Dry Run

## Starting Commands

From `/Users/bwbrook/work/makedoc`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
git log -1 --oneline
```

Expected:

```text
## main...origin/main
c7adc67
c7adc67 Add text-only DOCX revision candidate importer
```

Do not inspect CPE.

## Focused Commands

Compile:

```sh
python3 -m py_compile scripts/import_docx_review_markup.py
```

Focused tests:

```sh
python3 -m unittest tests/test_import_docx_review_markup.py
```

Manual CLI shape:

```sh
python3 scripts/import_docx_review_markup.py revised-candidate \
  --original-path path/to/original_simple_prose.md \
  --revised-docx path/to/revised.docx \
  --output path/to/review_candidate.md
```

## Validation

Run sequentially:

```sh
python3 -m py_compile scripts/import_docx_review_markup.py
python3 -m unittest tests/test_import_docx_review_markup.py
make test-review-markup
make check
git diff --check
```

## Log Requirements

Record:

- start state;
- required files read;
- red test evidence;
- synthetic dry-run behavior;
- refusal cases covered;
- importer change, if any;
- operator note summary;
- validation results;
- final `git status --short --branch`;
- confirmation that CPE and unrelated repos were untouched.

## Wake-Up

Wake Makedoc orchestrator thread
`019eaf80-3882-7d31-b6a4-3cb4c2ab5699` with completion or blocker status,
changed files, synthetic dry-run behavior, refusal cases, operator-note
summary, validation, final status, and CPE/unrelated repo confirmation.

Stop after the wake-up.
