# Runbook: Synthetic End-to-End Review Loop Proof

## Baseline

```sh
cd /Users/bwbrook/work/makedoc
git status --short --branch
git rev-parse --short HEAD
git log -5 --oneline
```

Expected:

```text
## main...origin/main
3031364
```

## Proof Target

```sh
make test-review-import-loop
```

The target:

- creates temporary synthetic original Markdown and revised DOCX inputs;
- runs `revised-candidate`;
- writes generated evidence under `dist/review-import-loop/`;
- prepares the candidate through `review_markup.enabled: true`;
- builds PDF/DOCX/manifest evidence;
- checks candidate tokens, prepared Markdown, PDF text, and DOCX XML markers.

Expected generated evidence:

```text
dist/review-import-loop/review_import_candidate.md
dist/review-import-loop/review_import_loop.pdf
dist/review-import-loop/review_import_loop.docx
dist/review-import-loop/review_import_loop_build_manifest.json
```

## Validation

Run sequentially:

```sh
python3 -m py_compile scripts/import_docx_review_markup.py
python3 -m unittest tests/test_import_docx_review_markup.py
make test-review-import-loop
make test-review-markup
make check
git diff --check
```

## Stop Conditions

Stop and wake the orchestrator if:

- the baseline differs materially;
- the proof requires CPE or real manuscript material;
- importer support would need to broaden;
- generated artifacts would need to be force-added;
- validation fails for a reason outside this goal.
