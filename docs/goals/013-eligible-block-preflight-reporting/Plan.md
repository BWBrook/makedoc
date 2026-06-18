# Plan: Eligible-Block Preflight Reporting

1. Confirm makedoc and CPE starting states.
2. Read the importer script, focused tests, operator note, spike memo, CPE
   preflight audit note, and recent goal context.
3. Add failing tests for `eligible_blocks_detail` in safe, mixed, and
   prose-leak-sensitive JSON cases.
4. Implement the minimal shared preflight report change.
5. Rerun the focused importer tests.
6. Rerun CPE structured preflight and derive prose-free summary files under
   `/tmp/makedoc-goal013-eligible-blocks/`.
7. Update docs and Goal 013 log.
8. Run validation:
   - `python3 -m py_compile scripts/import_docx_review_markup.py`
   - `python3 -m unittest tests/test_import_docx_review_markup.py`
   - `make test-review-markup`
   - `make check`
   - `git diff --check`
9. Confirm final makedoc and CPE statuses.
10. Wake the Makedoc orchestrator and stop.
