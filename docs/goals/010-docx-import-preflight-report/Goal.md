# Goal: DOCX Import Preflight and Refusal Report

## Objective

Make the experimental DOCX revised-candidate importer safer and more usable by
adding a preflight/report mode for original Markdown sources.

The mode should tell an operator which blocks are eligible for candidate
import, which blocks are refused, and why, without requiring a revised DOCX and
without copying manuscript prose into the report by default.

## Product Stance

This is an operator-safety and decision-surface goal. It is not a goal to
broaden importer support or make the importer production-ready.

The importer remains a human-reviewed candidate generator, not Word
round-tripping, native Track Changes import, or canonical manuscript mutation.

## Scope

Authorized path:

- `/Users/bwbrook/work/makedoc`

Forbidden:

- `/Users/bwbrook/papers/cpe_time_to_extinction`
- Chief of Staff
- Goal Composer
- sibling project repositories
- archive material
- unrelated user files

## Required Work

1. Confirm makedoc starts clean at `78b24a9` on `main...origin/main`.
2. Read repo-local `AGENTS.md` before other repo work.
3. Add an experimental CLI mode such as:

   ```sh
   python3 scripts/import_docx_review_markup.py preflight \
     --original-path path/to/original.md
   ```

4. Report block counts, eligible simple-prose paragraph counts, refusals,
   block/line references, stable refusal reasons, and a whole-file status.
5. Do not output manuscript prose by default.
6. Keep preflight read-only and do not write candidate files.
7. Keep `revised-candidate` refusal behavior at least as conservative as
   before.
8. Update focused tests, operator docs, spike memo, and this goal packet.
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
- CPE or other external manuscript reads.
- CPE edits, staging, commits, pushes, fetches, pulls, resets, cleans, stashes,
  rebases, branch switches, builds, or artifact regeneration.
- Native Word Track Changes hardening.
- Native Word automation, GUI Word control, dependency installation, remote
  services, or network access.
- Support for citations, headings, lists, tables, figures, comments,
  references, formatting-only changes, moves, or full round-tripping.
- Outbound review-markup rendering changes.
- Profile schema, Make build graph, external adoption playbook, or manuscript
  workflow changes.
- Goal 011.

## Acceptance Criteria

- Preflight can be run on an original Markdown/plain-prose source without a
  revised DOCX.
- Preflight reports eligible/refused block counts, refusal line/block
  references, and refusal reasons without copying prose.
- Exit-code policy is deliberate and documented: report generation exits 0 even
  when refused blocks are present; non-zero status is reserved for CLI, file, or
  runtime errors.
- Existing `revised`, `track-changes`, and `revised-candidate` behavior remains
  intact.
- Focused tests cover positive simple-prose reporting, mixed refusal reporting,
  no-prose report output, and CLI exit behavior.
- CPE and unrelated repos remain untouched.
