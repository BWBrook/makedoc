# Builder Notes

Last updated: 2026-02-13
Context: Phase 1-3 implementation (build scaffold, normalization, citation migration)

## Decision Log
- 2026-02-13: Use plain `Makefile` + pandoc directly for Phase 1 (Quarto remains available for future phases).
- 2026-02-13: Keep Phase 1 content-preserving; do not rewrite manuscript prose/citations yet.
- 2026-02-13: Support current manuscript math style by setting pandoc input format to `markdown+tex_math_dollars+tex_math_single_backslash`.
- 2026-02-13: For Phase 2, apply only minimal normalization edits that do not alter scientific claims or interpretation.
- 2026-02-13: Add a strict manuscript lint gate for unresolved placeholders and manual author-year citation patterns.
- 2026-02-13: Resolve `[REF]` using an inferred synchrony-framework citation pair; record as an explicit inference in report.
- 2026-02-13: Map `Wagg et al. 2022` text citation to available bibliography key `@wagg2021DiversityAsynchronySoil` and log year mismatch caveat.

## Work Log
- 2026-02-13: Reviewed repository structure and manuscript/reference/CSL inputs.
- 2026-02-13: Verified core tooling (`pandoc`, `quarto`, `xelatex`, `latexmk`, `biber`, `tectonic`, `hunspell`).
- 2026-02-13: Initialized planning artifacts (`docs/plan.md`, `docs/builder_notes.md`).
- 2026-02-13: Added Phase 1 build scaffold (`Makefile`, `.gitignore`).
- 2026-02-13: Ran build verification and produced `dist/manuscript.pdf` + `dist/manuscript.docx`.
- 2026-02-13: Initialized Git repository, committed Phase 1 changes, created private GitHub repo, and pushed `main`.
- 2026-02-13: Removed standalone Unicode em-space under Keywords in `manuscript/text/draft_ms_v2.md`.
- 2026-02-13: Repaired malformed markdown table row for `positive-matched control` using `$\lvert b_i^{\mathrm{mixed}} \rvert$`.
- 2026-02-13: Re-ran build checks successfully after normalization edits.
- 2026-02-13: Added `lint-manuscript` target in `Makefile` and wired it into `make check`.
- 2026-02-13: Converted manual citations in `manuscript/text/draft_ms_v2.md` to Pandoc citation keys.
- 2026-02-13: Added `docs/citation_conversion_report.md` with mapping details, inferences, and caveats.
- 2026-02-13: Re-ran lint and full check pipeline after citation conversion.

## Command Evidence
- `make check-tools` -> PASS (`Tool check passed.`)
- `make clean && make all` -> PASS (`dist/manuscript.pdf` and `dist/manuscript.docx` generated)
- `make check` -> PASS (`Build check passed.`)
- `ls -lh dist` -> PASS (`manuscript.pdf` 43K, `manuscript.docx` 17K)
- `git init -b main` -> PASS (new repository initialized)
- `git add . && git commit -m \"Phase 1 scaffold: pandoc build pipeline, plan docs, and notes\"` -> PASS (`67e6938`)
- `gh repo create BWBrook/makedoc --private --source=. --remote=origin --push` -> PASS (private repo created, `origin/main` tracking set)
- `make clean && make all` (post-normalization) -> PASS (`dist/manuscript.pdf` 44K, `dist/manuscript.docx` 18K)
- `make check` (post-normalization) -> PASS (`Build check passed.`)
- `make lint-manuscript` (before conversion) -> FAIL (detected `[REF]` and manual citations as expected)
- `make lint-manuscript` (after conversion) -> PASS (`Manuscript lint passed.`)
- `make check` (after conversion) -> PASS (`Tool check`, `lint-manuscript`, and both builds passed)
- `make clean && make all` (after conversion) -> PASS (`dist/manuscript.pdf` 48K, `dist/manuscript.docx` 19K)

## Build Warnings
- Previous PDF warning for Unicode em-space (`U+2003`) no longer reproduced after Phase 2 edits.

## Open Issues
- Figure files exist but are not yet integrated in manuscript markdown as renderable figure blocks.
- Citation caveat: manuscript originally referenced `Wagg et al. 2022` while bibliography key used is `@wagg2021DiversityAsynchronySoil` (year 2021); verify intended source/year.
- Citation caveat: one former placeholder (`[REF]`) was resolved by inference; confirm this is the intended citation pair.
