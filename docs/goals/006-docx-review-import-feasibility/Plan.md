# Plan: DOCX Review Import Feasibility

## Intent

Keep the spike narrow and honest: prove small text-only evidence, document
fragility, and recommend whether a real importer should be pursued.

## Steps

1. Confirm starting state in makedoc.
2. Read required context.
3. Implement a small stdlib-only prototype if feasible.
   - Revised DOCX route: extract revised text from DOCX and diff it against
     original text.
   - Native Track Changes route: inspect `w:ins` and `w:del` in tiny OOXML.
4. Add focused tests with generated temporary DOCX ZIP/XML fixtures.
5. Write `docs/docx_review_import_spike.md`.
6. Create the Goal 006 packet and log evidence.
7. Run validation:
   - `python3 -m py_compile scripts/import_docx_review_markup.py`
   - `python3 -m unittest tests/test_import_docx_review_markup.py`
   - `make test-review-markup`
   - `git diff --check`
   - optionally `make check` if cheap and appropriate.
8. Wake orchestrator and stop.

## Expected Outcome

Expected outcome: simple prose import is technically possible, but production
round-tripping should be deferred or constrained because source mapping from
DOCX back to Markdown is the hard part.
