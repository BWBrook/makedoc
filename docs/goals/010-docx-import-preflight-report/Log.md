# Log: DOCX Import Preflight and Refusal Report

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
78b24a9
```

Recent log context:

```text
78b24a9 Record CPE DOCX import readiness trial
e23dbd2 Add DOCX import synthetic dry run
c7adc67 Add text-only DOCX revision candidate importer
bba8be2 Add DOCX review import feasibility spike
d912acd Document external review markup adoption
```

Repository state matched the expected clean Goal 009 baseline.

## 2026-06-15 - Context Read

Status: implementation in progress.

Required context read:

- `AGENTS.md`
- `README.md`
- `docs/plan.md`
- `docs/builder_notes.md`
- `docs/makedoc_primer_for_agents.md`
- `docs/docx_review_import_spike.md`
- `docs/docx_review_import_operator_note.md`
- `scripts/import_docx_review_markup.py`
- `tests/test_import_docx_review_markup.py`
- `docs/goals/009-cpe-real-manuscript-import-readiness/Goal.md`
- `docs/goals/009-cpe-real-manuscript-import-readiness/Plan.md`
- `docs/goals/009-cpe-real-manuscript-import-readiness/Runbook.md`
- `docs/goals/009-cpe-real-manuscript-import-readiness/Log.md`

No CPE, Chief of Staff, Goal Composer, sibling repos, archive material, or
unrelated user files were read.

## 2026-06-15 - Red Tests

Status: implementation in progress.

Added tests for the desired preflight API and CLI behavior before implementing
the mode.

Red command:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: failed as expected because `preflight_markdown_source`,
`format_preflight_report`, and the `preflight` subcommand did not yet exist.
Existing importer behavior tests otherwise continued to run.

## 2026-06-15 - Implementation

Status: validation pending.

Implementation choice:

- added `preflight_markdown_source(original_path)`;
- added `format_preflight_report(report)`;
- added CLI mode:

  ```sh
  python3 scripts/import_docx_review_markup.py preflight \
    --original-path path/to/original.md
  ```

The preflight mode uses the same conservative unsupported-Markdown policy as
`revised-candidate`, but reports all refused blocks instead of stopping at the
first refusal.

Report behavior:

- reports non-empty block count;
- reports eligible simple-prose paragraph count;
- reports refused block count;
- lists block number, line range, first refused line, and refusal reason;
- emits `SAFE_TO_ATTEMPT` only when the whole source has at least one block and
  no refusals;
- emits `REFUSED` when unsupported blocks are present;
- emits `NO_ELIGIBLE_BLOCKS` for empty/no-block input;
- does not include source prose by default.

Exit-code policy: preflight exits 0 when the report is produced, even if
refused blocks are present. Non-zero status remains reserved for CLI, file, or
runtime errors.

Focused importer tests passed after implementation:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 18 tests.

Compile check passed:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
```

Result: passed.

Validation ladder still pending after documentation and log updates.

## 2026-06-15 - Validation Complete

Status: complete.

Changed makedoc files:

```text
docs/docx_review_import_operator_note.md
docs/docx_review_import_spike.md
docs/goals/010-docx-import-preflight-report/Goal.md
docs/goals/010-docx-import-preflight-report/Plan.md
docs/goals/010-docx-import-preflight-report/Runbook.md
docs/goals/010-docx-import-preflight-report/Log.md
scripts/import_docx_review_markup.py
tests/test_import_docx_review_markup.py
```

Validation commands run sequentially from makedoc:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
```

Result: passed.

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 18 tests.

```text
make test-review-markup
```

Result: passed; 12 review-markup tests passed, review profile config
validation passed, proof DOCX build ran, and review-markup regression checks
passed.

```text
make check
```

Result: passed; tool check, config validation, 55 discovered Python tests,
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
 M scripts/import_docx_review_markup.py
 M tests/test_import_docx_review_markup.py
?? docs/goals/010-docx-import-preflight-report/
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, rebases, branch switches, dependency installs, generated artifact
force-adds, CPE/external manuscript reads, out-of-scope repo reads, importer
support broadening, outbound rendering changes, profile schema changes, Make
build graph changes, or Goal 011 work were performed.

Recommended next step: orchestrator review. If accepted, publish the Goal 010
stack. For importer strategy, the next product decision is whether preflight is
enough for cautious operator-led use on approved simple-prose excerpts, or
whether a later goal should add a machine-readable report format or approved
real-manuscript hardening examples.

## 2026-06-15 - Narrow Review Iteration

Status: validation pending.

Orchestrator review found one safety gap: YAML/front-matter style delimiter
lines such as `---` were reported by preflight as safe simple prose, and
`revised-candidate` could continue past the structural issue to a later
paragraph-count refusal. That was too permissive for the simple-prose-only
contract.

Red tests added before implementation:

- `revised-candidate` refuses a source containing front-matter style delimiter
  lines and does not write output;
- `preflight` reports `unsupported Markdown front matter or thematic break`;
- preflight output does not copy the front-matter title or prose into the
  report.

Red command:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: failed as expected. Preflight counted the delimiter block as eligible,
and `revised-candidate` raised paragraph-count mismatch instead of the intended
front-matter/thematic-break refusal.

Implementation:

- added a shared refusal for delimiter-only lines matching `---`, `***`, or
  `___` with optional surrounding whitespace;
- reason: `unsupported Markdown front matter or thematic break`;
- wired it through the existing shared unsupported-Markdown policy so both
  `preflight` and `revised-candidate` refuse the same structure;
- updated operator docs and the spike memo refusal lists.

Focused importer tests passed after the fix:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 20 tests.

Full validation ladder pending.

## 2026-06-15 - Review Iteration Validation Complete

Status: complete.

Validation commands run sequentially from makedoc:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
```

Result: passed.

```text
python3 -m unittest tests/test_import_docx_review_markup.py
```

Result: passed, 20 tests.

```text
make test-review-markup
```

Result: passed; 12 review-markup tests passed, review profile config
validation passed, proof DOCX build ran, and review-markup regression checks
passed.

```text
make check
```

Result: passed; tool check, config validation, 57 discovered Python tests,
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
 M scripts/import_docx_review_markup.py
 M tests/test_import_docx_review_markup.py
?? docs/goals/010-docx-import-preflight-report/
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, rebases, branch switches, dependency installs, generated artifact
force-adds, CPE/external manuscript reads, out-of-scope repo reads, importer
support broadening, outbound rendering changes, profile schema changes, Make
build graph changes, or Goal 011 work were performed.

Recommended next step: orchestrator review of the narrowed fix. If accepted,
publish the Goal 010 stack.
