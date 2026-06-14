# Plan: DOCX Import Synthetic Dry Run

## Intent

Keep Goal 008 as a synthetic guardrail pass. The tool should feel safer to
operate, not broader.

## Steps

1. Confirm starting state in makedoc.
2. Read required local context and Goal 007 evidence.
3. Add failing tests first:
   - synthetic three-paragraph manuscript-like dry run;
   - positive CLI dry-run smoke;
   - realistic citation refusal, including narrative Pandoc citation syntax;
   - heading and list refusals.
4. Make only the minimal importer change required by the tests.
5. Add the operator note.
6. Update the DOCX import spike memo with Goal 008 status and the operator note
   pointer.
7. Create this goal packet and log evidence.
8. Run validation:
   - `python3 -m py_compile scripts/import_docx_review_markup.py`
   - `python3 -m unittest tests/test_import_docx_review_markup.py`
   - `make test-review-markup`
   - `make check`
   - `git diff --check`
9. Wake the orchestrator and stop.

## Expected Outcome

Expected outcome: the importer remains experimental and narrow, but has
manuscript-like synthetic evidence plus clearer operator documentation. A real
manuscript trial should remain a later explicit goal with approved examples.
