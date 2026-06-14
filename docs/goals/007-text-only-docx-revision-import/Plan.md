# Plan: Text-Only DOCX Revision Import Candidate

## Intent

Keep the Goal 007 step narrow: make the revised-DOCX route useful enough to
generate a human-reviewed candidate file for simple prose, while refusing
anything that looks like real manuscript structure.

## Steps

1. Confirm starting state in makedoc.
2. Read required local context and Goal 006 evidence.
3. Add failing tests for the candidate-generator API/CLI:
   - simple one-paragraph candidate output;
   - multiple paragraphs with preserved blank-line separation;
   - paragraph-count mismatch refusal;
   - unsupported figure/table refusals;
   - output-equals-original refusal;
   - existing-output refusal;
   - CLI non-zero refusal.
4. Add the minimal stdlib-only implementation to
   `scripts/import_docx_review_markup.py`.
5. Update the DOCX import decision memo with Goal 007 status and usage.
6. Create this goal packet and log evidence.
7. Run validation:
   - `python3 -m py_compile scripts/import_docx_review_markup.py`
   - `python3 -m unittest tests/test_import_docx_review_markup.py`
   - `make test-review-markup`
   - `make check`
   - `git diff --check`
8. Wake the orchestrator and stop.

## Expected Outcome

Expected outcome: a small, experimental candidate-file generator that is safe
for synthetic simple prose and explicit about refusals. It should support
future human-reviewed trials without claiming DOCX-to-Markdown round-tripping.
