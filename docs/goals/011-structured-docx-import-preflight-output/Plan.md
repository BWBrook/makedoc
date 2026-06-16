# Plan: Structured DOCX Import Preflight Output

## Intent

Add a machine-readable preflight output for action agents and future
automation while preserving the default human-readable text report and the
existing conservative refusal policy.

## Steps

1. Preflight makedoc repository state.
2. Read required repo and importer context.
3. Add failing tests for JSON CLI behavior, shared status, no-prose output,
   refused-exit-zero, and invalid format handling.
4. Move preflight status into shared report data.
5. Add `--format text|json` to the preflight CLI.
6. Render JSON with Python stdlib `json`.
7. Preserve existing text preflight and candidate behavior.
8. Update operator-facing docs and spike memo.
9. Create/update the Goal 011 packet and execution log.
10. Run validation sequentially.
11. Wake the orchestrator and stop.

## Expected Outcome

Expected outcome: `scripts/import_docx_review_markup.py preflight
--original-path ... --format json` prints valid JSON with the same counts,
status, and refusal objects as the text report, without including manuscript
prose.

This should make preflight easier for agents to consume without changing what
the importer considers safe.
