# Log: DOCX Review Import Feasibility

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
d912acd
```

```text
git log -1 --oneline
d912acd Document external review markup adoption
```

Required context read before implementation:

- `AGENTS.md`
- `README.md`
- `docs/review_markup_external_adoption.md`
- `docs/markdown_review_markup_spike.md`
- `scripts/prepare_markdown_sources.py`
- `tests/test_prepare_markdown_sources.py`
- Goal 004 log
- Goal 005 goal and log

CPE was not read or inspected.

## 2026-06-14 - Prototype And Memo Added

Status: validation in progress.

Added experimental prototype:

```text
scripts/import_docx_review_markup.py
```

Added focused tests with generated temporary DOCX ZIP/XML fixtures:

```text
tests/test_import_docx_review_markup.py
```

Added decision memo:

```text
docs/docx_review_import_spike.md
```

Routes tested:

1. Revised DOCX route: extract simple revised text from `word/document.xml`,
   compare it with original text using a normalized word diff, and emit
   `{++ ... ++}`, `{-- ... --}`, and `{~~ old ~> new ~~}` tokens.
2. Native Track Changes route: read tiny OOXML `w:ins` and `w:del` content in
   document order and emit insertion/deletion tokens.

Initial validation:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
```

Result: passed.

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 3 tests.

Design decision: keep the prototype text-first and dependency-light using only
Python stdlib ZIP/XML parsing and `difflib`. Do not invoke Word, do not install
dependencies, do not use CPE or real manuscript content, and do not alter
outbound review-markup semantics.

## 2026-06-14 - Validation Complete

Status: complete.

Decision memo recommendation:

- Do not build a full production DOCX-to-Markdown review importer yet.
- If Barry wants the capability next, pursue a constrained text-only prototype
  for simple prose paragraphs using the revised-DOCX text-diff route.
- Keep native Track Changes OOXML import as a separate spike until real
  tracked-change examples and policy decisions exist.

Route evidence:

- Revised DOCX route worked for a tiny generated DOCX where original text
  `alpha beta remove gamma old` and revised DOCX text
  `alpha inserted beta gamma new` produced:

  ```text
  alpha {++ inserted ++} beta {-- remove --} gamma {~~ old ~> new ~~}
  ```

- Native Track Changes route worked for tiny synthetic OOXML containing
  `w:ins(inserted)` and `w:del(removed)` in document order, producing:

  ```text
  alpha {++ inserted ++} beta {-- removed --} gamma
  ```

Limitations recorded in the memo:

- mapping DOCX-derived text back onto Markdown structure is the hard problem;
- citations, figure links, headings, tables, field codes, comments, moves,
  formatting-only changes, and paragraph splits/merges are unsupported;
- accepted/revised DOCX comparison loses reviewer intent;
- real Track Changes OOXML needs a fixture corpus and policy decisions before
  production hardening.

Validation commands run:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
```

Result: passed.

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 3 tests.

```text
make test-review-markup
```

Result: passed; existing outbound review-markup regression still passes.

```text
make check
```

Result: passed; 40 discovered Python tests, lint, reference audit, author
injection, default build, and manifest generation passed. This broader check
was run because the spike added a script and a new unit-test module, and the
repo check is cheap on this fixture.

```text
git diff --check
```

Result: passed.

Final `git status --short --branch`:

```text
## main...origin/main
?? docs/docx_review_import_spike.md
?? docs/goals/006-docx-review-import-feasibility/
?? scripts/import_docx_review_markup.py
?? tests/test_import_docx_review_markup.py
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, rebases, branch switches, dependency installs, generated artifact
force-adds, CPE access, CPE mutation, unrelated repo reads, native Word
automation, network/remote services, outbound rendering changes, profile
schema changes, Make build graph changes, or Goal 007 work were performed.

Recommended next step: orchestrator review of the memo and prototype. If
accepted, either publish this spike as evidence or write a new narrowly scoped
goal for a text-only, human-reviewed importer prototype; defer full native
Track Changes import until real examples and policy decisions are available.
