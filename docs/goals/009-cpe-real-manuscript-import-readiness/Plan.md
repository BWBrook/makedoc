# Plan: CPE Real-Manuscript Import Readiness

## Intent

Run a narrowly bounded real-prose readiness trial without turning it into a
real manuscript adoption or importer feature goal.

## Steps

1. Preflight makedoc.
2. Preflight CPE after reading CPE `AGENTS.md`.
3. Read current makedoc importer/operator context.
4. Scan CPE `manuscript/text/main.md` for tiny simple-prose candidate
   paragraphs that contain no currently refused Markdown structures.
5. Create temporary evidence under `/tmp/makedoc-goal009-cpe-import/`.
6. Generate a synthetic revised DOCX from the selected real prose excerpt.
7. Run `scripts/import_docx_review_markup.py revised-candidate`.
8. Inspect candidate structure and token categories.
9. Record evidence in the Goal 009 log without copying CPE prose into tracked
   docs.
10. Run validation.
11. Wake the orchestrator and stop.

## Expected Outcome

Expected outcome: at least one small CPE simple-prose excerpt should be usable
as a controlled readiness proof. The result should support a later
human-approved real-manuscript trial only if the paragraph mapping remains
sensible and CPE stays untouched.
