# Goal: PDF Review Markup Legibility Hardening

## Objective

Make review-markup deletion and old-wording traces readable in generated PDF
output while preserving useful DOCX review traces.

Goal 003 proved the external CPE workflow but exposed a product problem: PDF
additions and reviewer notes were readable, and DOCX deletion strikeout was
usable, but PDF deletion/old-wording strikeout rendered mostly as strike lines
rather than readable deleted words. This goal should fix or revise that
rendering policy before review markup is used more broadly.

## Why This Matters

Barry's review-markup requirement is human-facing: a person must be able to see
Markdown edits as visibly traceable when a DOCX or PDF is generated. Passing
text extraction or DOCX XML checks is not enough if the rendered PDF is
visually ambiguous.

The right outcome is not necessarily prettier styling. The right outcome is a
robust, portable, readable policy that works in the existing `makedoc` build
pipeline and remains easy for authors to understand.

## Operating Mode

Engine hardening with artifact-level visual evidence.

Authorized paths:

- `/Users/bwbrook/work/makedoc` - implementation repo
- `/Users/bwbrook/papers/cpe_time_to_extinction` - evidence-only external
  manuscript pilot repo

Do not read or modify other repositories.

## Review Surface

The Makedoc orchestrator will review:

- source-prep/build-system/test diffs;
- review-markup docs updates;
- generated fixture DOCX/PDF evidence;
- generated CPE pilot DOCX/PDF evidence;
- rendered PDF page image evidence, not only `pdftotext`;
- validation output;
- final statuses for both repos.

## Scope

In scope:

- Investigate why current deletion/old-wording PDF rendering is not visually
  legible enough.
- Revise the review-markup rendering policy so PDF deletion/old wording is
  human-readable.
- Preserve the existing author-facing token syntax:
  - `{++ added text ++}`
  - `{-- deleted text --}`
  - `{~~ old text ~> new text ~~}`
  - `{>> reviewer note <<}`
- Preserve default-off behavior.
- Preserve ordinary clean manuscript builds.
- Prefer the smallest robust change that works with Pandoc, DOCX, and PDF.
- Update tests, `make test-review-markup`, docs, and the Goal 004 `Log.md`.
- Use the existing CPE pilot branch as an evidence surface without editing CPE
  source files.

Out of scope:

- True Microsoft Word Track Changes.
- DOCX-to-Markdown import.
- Red/green colour polish unless it is trivial, portable, and not required for
  legibility.
- New dependencies unless no existing-tool route is viable and you stop first.
- Broad manuscript adoption beyond the existing CPE pilot branch.
- CPE source edits, staging, commits, or pushes.
- Publication closeout.

## Starting State

`makedoc` was clean before this packet was written:

```text
## main...origin/main
```

Expected `makedoc` HEAD:

```text
6d134c6 Record CPE review markup pilot
```

CPE was preserved after Goal 003 as a local dirty pilot branch:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

Expected CPE HEAD:

```text
e1b2433
```

The CPE dirty state above is expected and must be preserved. Do not clean,
stash, stage, commit, reset, or push it.

## Read First

In `/Users/bwbrook/work/makedoc`:

- `AGENTS.md`
- `README.md`
- `docs/makedoc_primer_for_agents.md`
- `docs/markdown_review_markup_spike.md`
- `docs/goals/002-review-markup-production-hardening/Goal.md`
- `docs/goals/002-review-markup-production-hardening/Log.md`
- `docs/goals/003-cpe-review-markup-pilot/Goal.md`
- `docs/goals/003-cpe-review-markup-pilot/Log.md`
- `scripts/prepare_markdown_sources.py`
- `scripts/test_review_markup.sh`
- `tests/test_prepare_markdown_sources.py`
- `settings/review_markup.yaml`
- `testbed/manuscript/text/review_markup_probe.md`
- `Makefile`

In `/Users/bwbrook/papers/cpe_time_to_extinction`, read repo-local
`AGENTS.md` first, then only if needed:

- `settings/build.yaml`
- `manuscript/text/main_review_markup_probe.md`

Do not read unrelated CPE notes/literature/material for this goal.

## Git Policy

In `/Users/bwbrook/work/makedoc`:

- Edits are allowed.
- Do not stage, commit, push, fetch, pull, reset, clean, or stash.
- Leave changes unstaged for orchestrator review.

In `/Users/bwbrook/papers/cpe_time_to_extinction`:

- Do not edit source files.
- Do not stage, commit, push, fetch, pull, reset, clean, stash, rebase, or
  switch branches.
- Reading CPE pilot files and regenerating ignored `build/` artifacts is
  allowed.
- If CPE status differs materially from the expected Goal 003 pilot state,
  stop and report before using it.

## Required Work

1. Capture starting state for both repos in `Log.md`.
2. Reproduce or inspect the current PDF deletion-legibility problem using the
   fixture or CPE pilot output.
3. Identify the smallest robust rendering-policy change.
4. Implement the change in `makedoc`.
5. Update tests to cover the new rendering policy.
6. Update `scripts/test_review_markup.sh` so it verifies the new policy in
   generated evidence.
7. Update README/primer wording if the visible rendering contract changes.
8. Regenerate fixture review-markup DOCX/PDF evidence under ignored paths.
9. Regenerate CPE pilot DOCX/PDF evidence under ignored CPE `build/` paths
   without editing CPE source files.
10. Produce rendered PDF page image evidence, for example via `pdftoppm`, and
    inspect/report whether deletion/old-wording text is readable by eye.
11. Update `Log.md` with the decision, commands, artifacts, visual evidence,
    remaining risks, and final statuses.

## Implementation Guidance

Prefer simple, portable strategies. Candidate routes include, but are not
limited to:

- a common Markdown rendering policy that makes deletion text readable in both
  PDF and DOCX;
- a small format-aware source-preparation path if preserving DOCX strikeout
  requires different PDF/DOCX prepared sources;
- a minimal LaTeX/Pandoc styling adjustment if it solves PDF readability
  without new dependencies or fragile journal-specific behavior.

Do not assume the current strikeout policy must survive in PDF. If the best
portable PDF behavior is readable bracketed deletion text without strikeout,
that is acceptable if DOCX remains useful and docs/tests are honest.

## Validation Gates

Run sequentially from `/Users/bwbrook/work/makedoc` unless noted otherwise:

```sh
python3 -m unittest tests/test_prepare_markdown_sources.py
make test-review-markup
CONFIG=settings/review_markup.yaml make validate-config
CONFIG=settings/review_markup.yaml make -B all
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make validate-config
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make -B all
make test-author-injection
make test-figure-modes
make check
make check-fixture
git diff --check
```

Artifact checks must include:

- prepared Markdown inspection for fixture review markup;
- PDF text inspection for fixture and CPE pilot;
- DOCX XML inspection for fixture and CPE pilot;
- rendered PDF page image inspection for the fixture or CPE pilot showing
  readable deletion/old-wording text.

If full `make check` or `make check-fixture` fails for a reason unrelated to
this goal, stop and report before widening.

## Acceptance Criteria

The goal is complete only if:

- PDF deletion/old-wording review traces are readable by eye in rendered PDF
  evidence;
- DOCX still shows useful visible review traces;
- additions and reviewer notes remain readable;
- canonical CPE `manuscript/text/main.md` remains untouched;
- CPE remains on the local dirty Goal 003 pilot branch with no new source
  edits;
- `review_markup.enabled` remains default-off;
- tests/docs/logs match the chosen rendering policy;
- validation gates pass or a blocker is reported with evidence.

## Deliverables

- Engine/test/docs changes in `makedoc`, if needed.
- Updated `scripts/test_review_markup.sh`, if the regression checks change.
- Updated Goal 004 `Log.md`.
- Generated fixture and CPE proof artifacts under ignored paths.
- Rendered PDF page image evidence under a temporary or ignored path.
- Final report with changed files, validation, artifacts, visual finding, final
  statuses, and recommended next step.

## Decision Authority

You may decide:

- exact implementation route among the candidate strategies;
- whether PDF should keep strikeout or switch to another readable deletion
  representation;
- whether docs should describe PDF and DOCX rendering separately;
- exact test and artifact-inspection mechanics.

Pause before:

- adding dependencies;
- attempting native Word Track Changes;
- attempting DOCX-to-Markdown import;
- redesigning the build graph broadly;
- changing CPE source files;
- committing or pushing anything;
- cleaning or reconciling either repo;
- reading outside authorized paths;
- starting Goal 005.

## Wake-Up Requirement

When done or blocked, send the Makedoc orchestrator
(`019eaf80-3882-7d31-b6a4-3cb4c2ab5699`) a short wake-up using thread tools.
Include:

- completion or blocked status;
- chosen rendering policy;
- changed files;
- generated artifact paths;
- rendered PDF image evidence path;
- validation result;
- final statuses for `makedoc` and CPE;
- recommended next step.

Stop after sending the wake-up.
