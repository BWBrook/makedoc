# Builder Notes

Last updated: 2026-02-13
Context: Phase 1-7 implementation (build scaffold through config-driven and onboarding automation hardening)

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
- 2026-02-13: Execute synthetic fixture workstream before CI hardening so hardening can target a controlled test corpus.
- 2026-02-13: Add explicit negative guard tests so CI proves failure-detection behavior, not just happy-path builds.
- 2026-02-13: Split CI into fast guard job + parallel build jobs to improve diagnostics and reduce time-to-failure.
- 2026-02-13: Disable GitHub `::error` annotations during expected-failure guard tests to avoid misleading CI noise.
- 2026-02-13: Switch build orchestration to profile YAML (`settings/build.yaml`) so sources can point to other repositories without changing Make targets.
- 2026-02-13: Keep synthetic testbed as default profile baseline while preserving dedicated fixture profile for hardening checks.
- 2026-02-13: Implement journal-name CSL resolver with local-first matching and Zotero style-index fallback download.
- 2026-02-13: Add a profile scaffold helper and Make wrapper so onboarding new manuscript repositories does not require manual YAML editing.
- 2026-02-13: Add fixture golden checks based on rendered DOCX/PDF structure rather than brittle byte-for-byte snapshots.
- 2026-02-13: Provide an Ubuntu/WSL installer script with minimal/full package tiers and apt simulation size reporting.
- 2026-02-13: Use cached apt package installs in CI to reduce repeated dependency provisioning overhead.
- 2026-02-13: Keep cached apt setup in CI, but add explicit `apt-get install` verification in build jobs to avoid TeX font availability drift.

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
- 2026-02-13: Implemented synthetic fixture manuscript, references, and dummy figures under `testbed/`.
- 2026-02-13: Added fixture build/lint/audit targets to `Makefile` and integrated fixture checks into CI.
- 2026-02-13: Updated `docs/testbed_workplan.md` status from proposed to implemented baseline.
- 2026-02-13: Added `scripts/lint_manuscript.py` and switched lint targets to script-driven checks.
- 2026-02-13: Added fixture edge-case sources for unknown citekey/manual citation/malformed table.
- 2026-02-13: Added `check-fixture-guards` target to assert expected failures for edge-case inputs.
- 2026-02-13: Hardened CI workflow into `guard-tests`, `build-main`, and `build-fixture` jobs with artifact summaries.
- 2026-02-13: Added `settings/build.yaml` with `default` and `fixture` profiles.
- 2026-02-13: Added `scripts/build_profile.py` and refactored `Makefile` to resolve active/fixture variables from YAML config.
- 2026-02-13: Added `scripts/csl_resolver.py` and Make targets `csl-search` / `csl-source`.
- 2026-02-13: Added root `README.md` documenting quickstart, profile schema, CSL tooling, and external path wiring.
- 2026-02-13: Added `scripts/install_ubuntu_deps.sh` and dependency helper targets (`deps-estimate-*`, `deps-install-*`, `deps-dry-run-*`).
- 2026-02-13: Added `scripts/profile_scaffold.py` and `make profile-scaffold` wrapper target for profile generation/appending.
- 2026-02-13: Added `scripts/fixture_golden_check.py` and integrated it into `check-fixture`.
- 2026-02-13: Updated GitHub Actions CI to use cached apt package setup and run fixture golden checks.
- 2026-02-13: Expanded `README.md` with Ubuntu/WSL bootstrap and profile scaffold instructions.
- 2026-02-13: Detected CI regression (`run 21974358589`) caused by cache-only build dependency restore missing TeX font readiness.
- 2026-02-13: Added explicit build-job dependency verification step (`apt-get install -y ...`) after cache restore and revalidated green CI.

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
- `make check-fixture` -> PASS (`fixture-lint`, `fixture-refs-audit`, and fixture PDF/DOCX builds passed)
- `gh run watch 21971721843 --repo BWBrook/makedoc --exit-status` -> PASS (workflow passed again after CI/doc updates)
- `make check-fixture-guards` -> PASS (all three edge-case failures detected as expected)
- `make check-fixture-guards && make check && make check-fixture` -> PASS (combined local verification after hardening changes)
- `gh run watch 21972231252 --repo BWBrook/makedoc --exit-status` -> PASS (CI run with fixture pipeline steps completed successfully)
- `make check-fixture-guards` (after annotation suppression fix) -> PASS (expected failures still detected; no shell invocation errors)
- `gh run watch 21972670054 --repo BWBrook/makedoc --exit-status` -> PASS (hardened CI with `guard-tests`, `build-main`, and `build-fixture` all succeeded)
- `gh run watch 21972735861 --repo BWBrook/makedoc --exit-status` -> PASS (repeat validation of hardened CI on latest `main` commit)
- `make profiles` -> PASS (lists `default` and `fixture`; active profile marked)
- `make profile-show` -> PASS (resolved profile values emitted from `settings/build.yaml`)
- `make check` (post-config refactor) -> PASS (default profile testbed build + lint/audit checks)
- `make check-fixture-guards && make check-fixture` (post-config refactor) -> PASS
- `make csl-search JOURNAL="Oikos"` -> PASS (local and remote CSL candidates listed)
- `make csl-source JOURNAL="Oikos"` -> PASS (local-first resolution to `testbed/csl/fixture_style.csl`)
- `python3 scripts/csl_resolver.py source --journal "Ecology Letters" --search-dir testbed/csl --dest-dir dist/csl_smoke --force --path-only` -> PASS (`dist/csl_smoke/ecology-letters.csl` downloaded)
- `make deps-estimate-minimal` -> PASS (prints minimal package set and apt simulated disk estimate)
- `make deps-estimate-full` -> PASS (prints full package set and apt simulated disk estimate)
- `make deps-dry-run-minimal` -> PASS (simulated minimal install without root privileges)
- `make deps-dry-run-full` -> PASS (simulated full install without root privileges)
- `make profile-scaffold PROFILE_NAME=demo_profile` -> PASS (prints scaffold YAML snippet without file writes)
- `make check-fixture` -> PASS (fixture lint/audit/build plus fixture golden checks passed)
- `python3 -m py_compile scripts/build_profile.py scripts/csl_resolver.py scripts/profile_scaffold.py scripts/fixture_golden_check.py scripts/lint_manuscript.py scripts/refs_audit.py` -> PASS
- `gh run watch 21974286056 --repo BWBrook/makedoc --exit-status` -> PASS (CI run with cached apt setup and fixture golden checks green across all jobs)
- `gh run watch 21974358589 --repo BWBrook/makedoc --exit-status` -> FAIL (cache-only restore in build jobs triggered LaTeX font availability error)
- `gh run watch 21974394354 --repo BWBrook/makedoc --exit-status` -> PASS (cached restore + explicit apt verification produced clean green CI)

## Build Warnings
- Previous PDF warning for Unicode em-space (`U+2003`) no longer reproduced after Phase 2 edits.

## Open Issues
- 14 bibliography keys are currently unused (reported by `make refs-audit`); non-blocking but useful for future bibliography pruning.
- Figures are linked and rendered, but panel-level references (e.g., 1A, 1B) still point to whole-figure anchors by design.
- Further CI hardening options remain (for example richer PR annotations), now supported by both real and synthetic guard suites.
