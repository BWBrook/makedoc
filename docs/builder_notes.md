# Builder Notes

Last updated: 2026-02-13
Context: Phase 1-5 implementation (build scaffold, normalization, citations, figures, CI)

## Decision Log
- 2026-02-13: Use plain `Makefile` + pandoc directly for Phase 1 (Quarto remains available for future phases).
- 2026-02-13: Keep Phase 1 content-preserving; do not rewrite manuscript prose/citations yet.
- 2026-02-13: Support current manuscript math style by setting pandoc input format to `markdown+tex_math_dollars+tex_math_single_backslash`.
- 2026-02-13: For Phase 2, apply only minimal normalization edits that do not alter scientific claims or interpretation.
- 2026-02-13: Add a strict manuscript lint gate for unresolved placeholders and manual author-year citation patterns.
- 2026-02-13: Resolve `[REF]` using an inferred synchrony-framework citation pair; record as an explicit inference in report.
- 2026-02-13: Map `Wagg et al. 2022` text citation to available bibliography key `@wagg2021DiversityAsynchronySoil` and log year mismatch caveat.
- 2026-02-13: User confirmed both citation caveats; lock them as final project decisions.
- 2026-02-13: Keep figure captions in a separate source file and render via multi-file pandoc inputs for maintainability.
- 2026-02-13: Add `refs-audit` as a non-optional quality gate in `make check`.
- 2026-02-13: Use GitHub Actions as the baseline reproducibility gate and run `make check` in CI.
- 2026-02-13: Track synthetic fixture manuscript as a separate follow-on workstream, not bundled into immediate CI rollout.

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
- 2026-02-13: Added `scripts/refs_audit.py` and `make refs-audit` for citation-key/bibliography validation.
- 2026-02-13: Updated `Makefile` to build from `manuscript/text/draft_ms_v2.md` and `manuscript/text/figure_captions_v2.md`.
- 2026-02-13: Replaced plain caption prose with renderable figure blocks and stable IDs in `figure_captions_v2.md`.
- 2026-02-13: Linked in-text figure mentions in results text to figure anchors.
- 2026-02-13: Validated generated LaTeX contains expected figure labels and hyperlink targets.
- 2026-02-13: Added `.github/workflows/ci.yml` to provision dependencies and run `make check` on push/PR/manual dispatch.
- 2026-02-13: Added CI artifact upload for `dist/` outputs.
- 2026-02-13: Drafted synthetic testbed proposal in `docs/testbed_workplan.md`.

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
- `make refs-audit` -> PASS (`Unknown keys: 0`; reports 14 unused bibliography keys as non-fatal)
- `make check` (after refs-audit + Phase 4) -> PASS (`check-tools`, `lint-manuscript`, `refs-audit`, and build stages passed)
- `make clean && make all` (after Phase 4) -> PASS (`dist/manuscript.pdf` 500K, `dist/manuscript.docx` 445K, includes figures)
- `python3 - <<'PY' ... yaml.safe_load('.github/workflows/ci.yml') ...` -> PASS (workflow YAML parses)
- `make check` (Phase 5 local revalidation) -> PASS (same full gate as CI target command)
- `gh run watch 21971671370 --repo BWBrook/makedoc --exit-status` -> PASS (GitHub Actions workflow `manuscript-ci` completed successfully)

## Build Warnings
- Previous PDF warning for Unicode em-space (`U+2003`) no longer reproduced after Phase 2 edits.

## Open Issues
- 14 bibliography keys are currently unused (reported by `make refs-audit`); non-blocking but useful for future bibliography pruning.
- Figures are linked and rendered, but panel-level references (e.g., 1A, 1B) still point to whole-figure anchors by design.
- Synthetic fixture workflow is planned (`docs/testbed_workplan.md`) and pending implementation.
