# Plan: DOCX Import Preflight and Refusal Report

## Intent

Add a read-only preflight surface that helps an operator decide whether the
experimental `revised-candidate` mode is safe to attempt before preparing or
supplying a revised DOCX.

## Steps

1. Preflight makedoc repository state.
2. Read required repo and importer context.
3. Add failing tests for the desired preflight API and CLI behavior.
4. Implement a minimal preflight report by sharing the existing conservative
   refusal policy.
5. Preserve existing candidate generation behavior and refusal messages.
6. Update operator-facing docs and spike memo.
7. Create/update the Goal 010 packet and execution log.
8. Run validation sequentially.
9. Wake the orchestrator and stop.

## Expected Outcome

Expected outcome: `scripts/import_docx_review_markup.py preflight
--original-path ...` prints a prose-free report with counts, block/line
references, refusal reasons, and an obvious whole-file status.

The mode should make routine operator decisions safer without making any new
Markdown structures eligible for import.
