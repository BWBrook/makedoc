# Goal: DOCX Import Synthetic Dry Run

## Objective

Prove the Goal 007 `revised-candidate` importer on a synthetic
manuscript-like dry run, strengthen operator-facing guardrails, and decide
whether the tool is ready for a controlled real-manuscript trial later.

This is not a real manuscript trial and must not touch CPE.

## Product Stance

The importer is a human-reviewed candidate generator, not round-tripping.

Goal 008 should make that operationally hard to misunderstand. Prefer one more
synthetic hardening pass before any real paper.

Preserve hard refusals for manuscript structures such as citations, headings,
lists, figures, and tables. Broaden support only for refusal behavior, not for
mapping real manuscript structure.

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

1. Confirm makedoc starts clean at `c7adc67` on `main...origin/main`.
2. Read required context:
   - `AGENTS.md`
   - `README.md`
   - `docs/docx_review_import_spike.md`
   - `docs/review_markup_external_adoption.md`
   - `scripts/import_docx_review_markup.py`
   - `tests/test_import_docx_review_markup.py`
   - Goal 007 packet/log enough to preserve behavior and boundaries.
3. Add a synthetic manuscript-like positive dry-run test using generated
   temporary DOCX ZIP/XML fixtures.
4. Add or confirm realistic refusal tests for Pandoc citations, headings,
   lists, figures, and tables.
5. Modify `scripts/import_docx_review_markup.py` only if needed for the dry
   run, safety behavior, or clearer operator-facing error messages.
6. Add `docs/docx_review_import_operator_note.md`.
7. Update `docs/docx_review_import_spike.md` with Goal 008 status and a
   pointer to the operator note.
8. Create this Goal 008 packet with `Goal.md`, `Plan.md`, `Runbook.md`, and
   `Log.md`.
9. Validate with the focused script/test commands, `make test-review-markup`,
   `make check`, and `git diff --check`.
10. Leave changes unstaged and wake the orchestrator.

## Non-Goals

- Production importer.
- CPE access or mutation.
- Real manuscript input.
- Native Word Track Changes hardening.
- Native Word automation or GUI Word control.
- Dependency installation, remote services, or network access.
- Support broadening for comments, moves, formatting-only changes, tables,
  citations, figures, references, headings, lists, or complex Markdown mapping.
- Outbound review-markup rendering changes.
- `review_markup.enabled`, profile schema, Make build graph, external adoption
  playbook, or manuscript workflow changes.
- Goal 009.

## Acceptance Criteria

- Synthetic manuscript-like positive test passes across multiple prose
  paragraphs.
- Realistic unsupported manuscript structures are refused clearly and safely.
- Operator note is concise, practical, and does not overclaim.
- Existing Goal 006/007 CLI modes still work.
- CPE and unrelated repos are untouched.
- Final changes remain unstaged for orchestrator review.
