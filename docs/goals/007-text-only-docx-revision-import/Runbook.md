# Runbook: Text-Only DOCX Revision Import Candidate

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
bba8be2
bba8be2 Add DOCX review import feasibility spike
```

Do not inspect CPE.

## Prototype Commands

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
  --original-path path/to/original.md \
  --revised-docx path/to/revised.docx \
  --output path/to/candidate.md
```

Existing Goal 006 modes should still work:

```sh
python3 scripts/import_docx_review_markup.py revised \
  --original-text "alpha beta remove gamma old" \
  --revised-docx path/to/revised.docx

python3 scripts/import_docx_review_markup.py track-changes \
  --docx path/to/tracked.docx
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
- implementation choice;
- candidate behavior and refusal cases;
- memo update;
- validation results;
- final `git status --short --branch`;
- confirmation that CPE and unrelated repos were untouched.

## Wake-Up

Wake Makedoc orchestrator thread
`019eaf80-3882-7d31-b6a4-3cb4c2ab5699` with completion or blocker status,
changed files, CLI behavior, refusal cases, validation, final status, and
CPE/unrelated repo confirmation.

Stop after the wake-up.
