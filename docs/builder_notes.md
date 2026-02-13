# Builder Notes

Last updated: 2026-02-13
Context: Phase 1 implementation (build scaffold + Git/GitHub bootstrap)

## Decision Log
- 2026-02-13: Use plain `Makefile` + pandoc directly for Phase 1 (Quarto remains available for future phases).
- 2026-02-13: Keep Phase 1 content-preserving; do not rewrite manuscript prose/citations yet.
- 2026-02-13: Support current manuscript math style by setting pandoc input format to `markdown+tex_math_dollars+tex_math_single_backslash`.

## Work Log
- 2026-02-13: Reviewed repository structure and manuscript/reference/CSL inputs.
- 2026-02-13: Verified core tooling (`pandoc`, `quarto`, `xelatex`, `latexmk`, `biber`, `tectonic`, `hunspell`).
- 2026-02-13: Initialized planning artifacts (`docs/plan.md`, `docs/builder_notes.md`).
- 2026-02-13: Added Phase 1 build scaffold (`Makefile`, `.gitignore`).
- 2026-02-13: Ran build verification and produced `dist/manuscript.pdf` + `dist/manuscript.docx`.

## Command Evidence
- `make check-tools` -> PASS (`Tool check passed.`)
- `make clean && make all` -> PASS (`dist/manuscript.pdf` and `dist/manuscript.docx` generated)
- `make check` -> PASS (`Build check passed.`)
- `ls -lh dist` -> PASS (`manuscript.pdf` 43K, `manuscript.docx` 17K)

## Build Warnings
- PDF build warning: missing glyph for Unicode em-space (`U+2003`) from `manuscript/text/draft_ms_v2.md`.
- Impact: non-blocking for Phase 1; should be cleaned in Phase 2 normalization.

## Open Issues
- Manuscript still contains manual citations and one placeholder `[REF]`.
- Figure files exist but are not yet integrated in manuscript markdown as renderable figure blocks.
