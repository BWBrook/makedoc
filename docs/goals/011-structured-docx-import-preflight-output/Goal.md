# Goal: Structured DOCX Import Preflight Output

## Objective

Add a stable machine-readable output option to the experimental DOCX import
preflight command so operators and future action-agent workflows can consume
preflight results without scraping the human-readable report.

## Product Stance

This is an automation-safety and reporting goal. It is not a goal to broaden
importer support or make the importer production-ready.

The existing text report remains the default for humans. JSON is for
agents/automation that need the same conservative preflight data in a stable
shape.

## Scope

Authorized path:

- `/Users/bwbrook/work/makedoc`

Forbidden:

- `/Users/bwbrook/papers/cpe_time_to_extinction`
- external manuscript repositories
- Chief of Staff
- Goal Composer
- sibling project repositories
- archive material
- unrelated user files

## Required Work

1. Confirm makedoc starts clean at `4d1786a` on `main...origin/main`.
2. Read repo-local `AGENTS.md` before other repo work.
3. Add structured output to the existing preflight command, preferably:

   ```sh
   python3 scripts/import_docx_review_markup.py preflight \
     --original-path path/to/original.md \
     --format json
   ```

4. Keep text output as the default.
5. Make status part of shared preflight report data so text and JSON cannot
   drift.
6. Use only Python standard library JSON support.
7. Do not include source prose in JSON by default.
8. Keep preflight read-only and do not write candidate files.
9. Keep the existing conservative refusal behavior unchanged.
10. Update focused tests, operator docs, spike memo, and this goal packet.
11. Run validation from makedoc:
    - `python3 -m py_compile scripts/import_docx_review_markup.py`
    - `python3 -m unittest tests/test_import_docx_review_markup.py`
    - `make test-review-markup`
    - `make check`
    - `git diff --check`
12. Leave changes unstaged and wake the orchestrator.

## Non-Goals

- Production importer.
- Importer support broadening.
- CPE or other external manuscript reads.
- CPE edits, staging, commits, pushes, fetches, pulls, resets, cleans, stashes,
  rebases, branch switches, builds, or artifact regeneration.
- Native Word Track Changes hardening.
- Native Word automation, GUI Word control, dependency installation, remote
  services, or network access.
- Support for citations, headings, lists, tables, figures, comments,
  references, front matter/thematic breaks, formatting-only changes, moves, or
  full round-tripping.
- Outbound review-markup rendering changes.
- Profile schema, Make build graph, external adoption playbook, or manuscript
  workflow changes.
- Goal 012.

## Acceptance Criteria

- `preflight --format json` emits valid deterministic JSON with stable field
  names.
- JSON includes status, path, total/eligible/refused block counts,
  `safe_to_attempt`, and refusal objects with block/line references and reason.
- JSON does not include original block text, paragraph text, heading text,
  citation text, title text, or other source prose by default.
- `preflight` still exits 0 when the report is produced, including refused
  reports.
- Invalid format values fail through normal CLI argument validation.
- Existing `revised`, `track-changes`, `revised-candidate`, and text preflight
  behavior remains intact.
- CPE and unrelated repos remain untouched.
