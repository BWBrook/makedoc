# Log: Eligible-Block Preflight Reporting

## 2026-06-18 - Execution Started

Status: in progress.

Executor: `draftsman`.

Makedoc starting state after reading repo-local `AGENTS.md`:

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
cd47925
```

Recent log context:

```text
cd47925 Record CPE structured preflight audit
4406365 Add structured DOCX import preflight output
4d1786a Add DOCX import preflight report
78b24a9 Record CPE DOCX import readiness trial
e23dbd2 Add DOCX import synthetic dry run
```

Makedoc matched the expected clean Goal 012 baseline.

## 2026-06-18 - CPE State

Status: read-only state confirmed.

CPE state after reading CPE repo-local `AGENTS.md`:

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

CPE matched the expected preserved pilot state. No CPE reconciliation was
performed.

## 2026-06-18 - Design Choice

Chosen JSON field:

```text
eligible_blocks_detail
```

Schema:

```json
{
  "block": 2,
  "start_line": 3,
  "end_line": 3
}
```

Rationale: the name is explicit and does not overload the existing
`eligible_blocks` count. Objects contain only block and line references, not
source prose.

## 2026-06-18 - Test-First Implementation

Focused tests were added before implementation for:

- all-simple-prose JSON/report data with eligible refs for every block;
- mixed input with one eligible block and refused structures;
- front matter, heading, and citation cases with no prose leakage through the
  JSON payload.

Initial focused test run failed with five `KeyError: 'eligible_blocks_detail'`
errors, confirming the missing report field.

Implementation then added `eligible_blocks_detail` to the shared preflight
report data. Text output remains compact and unchanged.

Focused test rerun:

```text
python3 -m unittest tests/test_import_docx_review_markup.py
PASS - Ran 24 tests
```

## 2026-06-18 - CPE Structured Audit Rerun

Status: validation pending.

Raw and derived temporary evidence:

```text
/tmp/makedoc-goal013-eligible-blocks/cpe-main-preflight.json
/tmp/makedoc-goal013-eligible-blocks/cpe-main-preflight-summary.json
/tmp/makedoc-goal013-eligible-blocks/cpe-main-eligible-refs.json
/tmp/makedoc-goal013-eligible-blocks/cpe-main-refusal-refs.json
```

Audit command run from makedoc:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path /Users/bwbrook/papers/cpe_time_to_extinction/manuscript/text/main.md \
  --format json
```

Result: passed, exit status 0.

Preflight summary:

| Metric | Value |
| --- | ---: |
| overall status | REFUSED |
| total blocks | 48 |
| eligible blocks | 23 |
| eligible block refs reported | 23 |
| refused blocks | 25 |
| safe_to_attempt | false |

Refusal reasons:

| Reason | Count |
| --- | ---: |
| unsupported Markdown heading | 17 |
| unsupported Markdown Pandoc citation | 8 |

First five eligible references:

```text
block 2 lines 3-3
block 4 lines 7-7
block 6 lines 11-11
block 8 lines 15-15
block 11 lines 21-21
```

Last five eligible references:

```text
block 39 lines 77-77
block 41 lines 81-81
block 43 lines 85-85
block 45 lines 89-89
block 47 lines 93-93
```

Tracked docs intentionally do not copy CPE prose, title text, heading text,
citation text, figure captions, or paragraph text.

Product finding: whole-file canonical CPE remains correctly refused. Eligible
refs now make it practical for a later workflow to propose prose-only ranges
for human approval without copying prose by default.

Recommended next importer strategy: keep support conservative; use structured
preflight JSON for decision support; if more work is desired, make the next
importer goal a controlled excerpt-selection workflow rather than support
broadening.

CPE branch-fate recommendation: preserve the CPE pilot branch through Goal 013
review. Make Goal 014 a separate explicit CPE branch disposition or cleanup
decision.

Validation ladder after documentation updates:

```text
python3 -m py_compile scripts/import_docx_review_markup.py
PASS

python3 -m unittest tests/test_import_docx_review_markup.py
PASS - Ran 24 tests

make test-review-markup
PASS

make check
PASS - Ran 61 tests

git diff --check
PASS
```

Changed makedoc files:

```text
docs/docx_review_import_cpe_preflight_audit.md
docs/docx_review_import_operator_note.md
docs/docx_review_import_spike.md
scripts/import_docx_review_markup.py
tests/test_import_docx_review_markup.py
docs/goals/013-eligible-block-preflight-reporting/Goal.md
docs/goals/013-eligible-block-preflight-reporting/Plan.md
docs/goals/013-eligible-block-preflight-reporting/Runbook.md
docs/goals/013-eligible-block-preflight-reporting/Log.md
```

Final makedoc status before wake-up:

```text
## main...origin/main
 M docs/docx_review_import_cpe_preflight_audit.md
 M docs/docx_review_import_operator_note.md
 M docs/docx_review_import_spike.md
 M scripts/import_docx_review_markup.py
 M tests/test_import_docx_review_markup.py
?? docs/goals/013-eligible-block-preflight-reporting/
```

Final CPE status before wake-up:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

Final CPE HEAD:

```text
e1b2433
```

Boundary confirmations:

- no CPE edits, builds, artifact regeneration, or git mutations;
- no importer support broadening;
- no staging, commits, pushes, fetches, pulls, resets, cleans, stashes,
  rebases, or branch switches;
- no dependency installs;
- no generated artifact force-adds;
- no Chief of Staff, Goal Composer, sibling repo, archive, unrelated-file, or
  out-of-scope CPE reads;
- no Goal 014 work.
