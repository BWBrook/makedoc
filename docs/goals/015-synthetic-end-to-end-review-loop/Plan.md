# Plan: Synthetic End-to-End Review Loop Proof

1. Confirm makedoc starts clean on `main...origin/main` at `3031364`.
2. Read repo-local `AGENTS.md` and relevant importer/review-markup docs.
3. Add a focused rerunnable proof target:
   - `make test-review-import-loop`
   - `scripts/test_review_import_loop.sh`
4. Use the proof to generate:
   - temporary original Markdown;
   - temporary revised DOCX;
   - ignored candidate/rendered evidence under `dist/review-import-loop/`.
5. Check candidate tokens, prepared Markdown markers, PDF text, and DOCX XML
   markers.
6. Update operator-facing docs and the spike notes.
7. Run validation:
   - `python3 -m py_compile scripts/import_docx_review_markup.py`
   - `python3 -m unittest tests/test_import_docx_review_markup.py`
   - `make test-review-import-loop`
   - `make test-review-markup`
   - `make check`
   - `git diff --check`
8. Wake the Makedoc orchestrator and stop.
