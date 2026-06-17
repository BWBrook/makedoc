# Goal: CPE Structured DOCX Import Preflight Audit

## Objective

Use the structured DOCX-import preflight report to audit the canonical CPE
manuscript source as a read-only real-manuscript target.

The goal is to quantify what the current importer policy refuses or accepts on
a real makedoc manuscript without broadening support, copying manuscript prose
into tracked docs, or mutating CPE.

## Product Stance

This is an evidence and product-decision goal. It is not an implementation
hardening goal.

The importer remains a conservative, experimental, human-reviewed candidate
generator for simple prose. Whole canonical manuscript sources are expected to
be unsafe when they contain ordinary manuscript structure.

## Scope

Authorized paths:

- `/Users/bwbrook/work/makedoc`
- `/Users/bwbrook/papers/cpe_time_to_extinction` for read-only evidence only
- `/tmp/makedoc-goal012-cpe-preflight/` for temporary evidence

Forbidden:

- Chief of Staff
- Goal Composer
- sibling project repositories
- archive material
- unrelated user files

## Required Work

1. Confirm makedoc starts clean at `4406365` on `main...origin/main`.
2. Read makedoc `AGENTS.md` before other makedoc work.
3. Read CPE `AGENTS.md` before any CPE inspection.
4. Confirm CPE is on preserved branch `codex/makedoc-review-markup-pilot` at
   `e1b2433` with the expected dirty pilot state.
5. Run structured preflight from makedoc:

   ```sh
   python3 scripts/import_docx_review_markup.py preflight \
     --original-path /Users/bwbrook/papers/cpe_time_to_extinction/manuscript/text/main.md \
     --format json
   ```

6. Store raw JSON under `/tmp/makedoc-goal012-cpe-preflight/`.
7. Parse and summarize JSON without copying CPE prose into tracked docs.
8. Record overall status, block counts, refusal reason counts, line/block
   references, product finding, importer recommendation, and CPE branch-fate
   recommendation.
9. Do not run `revised-candidate` unless preflight unexpectedly reports
   `SAFE_TO_ATTEMPT`; if that happens, stop and wake the orchestrator first.
10. Run validation from makedoc:
    - `python3 -m py_compile scripts/import_docx_review_markup.py`
    - `python3 -m unittest tests/test_import_docx_review_markup.py`
    - `make test-review-markup`
    - `make check`
    - `git diff --check`
11. Leave changes unstaged and wake the orchestrator.

## Non-Goals

- Importer changes.
- Importer support broadening.
- `revised-candidate` against CPE unless whole-file preflight surprisingly
  reports `SAFE_TO_ATTEMPT`.
- CPE edits, staging, commits, pushes, fetches, pulls, resets, cleans, stashes,
  rebases, branch switches, builds, artifact regeneration, cleanup, or
  branch-fate execution.
- Native Word Track Changes hardening.
- Native Word automation, GUI Word control, dependency installation, remote
  services, or network access.
- Support for citations, headings, lists, tables, figures, comments,
  references, front matter/thematic breaks, raw HTML, code blocks,
  formatting-only changes, moves, or full round-tripping.
- Outbound review-markup rendering changes.
- Profile schema, Make build graph, or manuscript workflow changes.
- Goal 013.

## Acceptance Criteria

- Makedoc and CPE preflight states match expectations, or the goal stops with
  exact blocker status.
- Raw CPE preflight JSON is stored only under `/tmp`.
- Tracked docs contain no CPE manuscript prose, title text, heading text,
  citation text, figure captions, or paragraph text.
- Summary records overall status, total/eligible/refused block counts, refusal
  reasons by count, useful block/line references, and product recommendation.
- CPE and unrelated repos remain unmodified.
