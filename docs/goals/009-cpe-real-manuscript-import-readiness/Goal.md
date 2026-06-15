# Goal: CPE Real-Manuscript Import Readiness

## Objective

Determine whether the experimental text-only DOCX `revised-candidate`
importer can safely handle a tiny simple-prose excerpt from a real makedoc
manuscript, using `/Users/bwbrook/papers/cpe_time_to_extinction` as the
approved proving ground.

This is a readiness/evidence goal, not a production feature goal.

## Product Stance

The importer remains a human-reviewed candidate generator, not round-tripping.

Goal 009 should test readiness against approved real manuscript prose without
mutating CPE, widening importer support, or weakening refusal policy.

## Scope

Authorized paths:

- `/Users/bwbrook/work/makedoc`
- `/Users/bwbrook/papers/cpe_time_to_extinction` for read-only evidence only
- `/tmp/makedoc-goal009-cpe-import/` for temporary trial files

Forbidden:

- Chief of Staff
- Goal Composer
- sibling project repositories
- archive material
- unrelated user files

## Required Work

1. Confirm makedoc starts clean at `e23dbd2` on `main...origin/main`.
2. Read makedoc `AGENTS.md` before other makedoc work.
3. Confirm CPE is on preserved branch `codex/makedoc-review-markup-pilot` at
   `e1b2433` with the expected dirty pilot state.
4. Read CPE `AGENTS.md` before any CPE inspection.
5. Audit canonical CPE `manuscript/text/main.md` enough to identify whether a
   tiny simple-prose excerpt exists.
6. If no safe excerpt exists, record the readiness/refusal finding and stop.
7. If a safe excerpt exists, copy only the tiny excerpt into `/tmp`, create a
   synthetic revised DOCX, run `revised-candidate`, inspect the candidate, and
   record evidence paths and behavior.
8. Create this Goal 009 packet and log evidence.
9. Run validation from makedoc:
   - `python3 -m py_compile scripts/import_docx_review_markup.py`
   - `python3 -m unittest tests/test_import_docx_review_markup.py`
   - `make test-review-markup`
   - `make check`
   - `git diff --check`
10. Leave changes unstaged and wake the orchestrator.

## Non-Goals

- Production importer.
- Importer support broadening.
- CPE edits, staging, commits, pushes, fetches, pulls, resets, cleans, stashes,
  rebases, branch switches, builds, or artifact regeneration.
- Native Word Track Changes hardening.
- Native Word automation, GUI Word control, dependency installation, remote
  services, or network access.
- Support for citations, headings, lists, tables, figures, comments,
  references, formatting-only changes, moves, or full round-tripping.
- Outbound review-markup rendering changes.
- Profile schema, Make build graph, or manuscript workflow changes.
- Goal 010.

## Acceptance Criteria

- Makedoc and CPE preflight states match expectations, or the goal stops with
  exact blocker status.
- CPE canonical source is inspected only enough to locate a tiny safe excerpt.
- Temporary evidence is written only under `/tmp/makedoc-goal009-cpe-import/`.
- Tracked docs do not copy CPE prose; they record line references, structural
  description, and evidence summaries only.
- Trial result records whether the current importer supports a later controlled
  real-manuscript hardening goal, a refusal-policy adjustment goal, or no
  further importer work for now.
- CPE and unrelated repos remain untouched.
