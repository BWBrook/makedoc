# Builder Notes

Last updated: 2026-04-24
Context: Phase 1-10 implementation (through profile-driven figure placement), plus post-handover hardening and stage-5 external path semantics

## Decision Log
- 2026-10-22: Extend the existing profile geometry/page-number contract to DOCX.
  Preserve standard XML prefixes and namespace declarations referenced by
  markup-compatibility attributes; retain accessible image descriptions when
  captions are moved; remove only known build-input custom properties.
  Protect table rows/headings and suppress layout-only line numbering. Column
  autofit retains authored preferred widths; final manuscript layout still
  requires rendered review.
- 2026-04-24: Keep manual author-year citation lint strict, but strip valid
  Pandoc citation tokens before deciding whether a parenthetical contains a
  manual citation. This allows prose such as acronym definitions with inline
  Pandoc citations while still flagging mixed manual/Pandoc citations.
- 2026-03-17: Use a single cross-platform dependency helper entrypoint (`scripts/install_deps.sh`) and keep `make deps-*` stable across Ubuntu/WSL and macOS.
- 2026-03-17: Prefer `mactex-no-gui` over `basictex` for macOS bootstrap because this repo's default xelatex workflow expects LaTeX packages beyond a minimal TeX install.
- 2026-03-17: Install `PyYAML` into the macOS Python user site during bootstrap so the profile loader works without requiring a separate virtualenv before first use.
- 2026-03-08: Flip external relative-path semantics in one migration: config-entry paths are now config-relative and markdown image paths are source-file-relative.
- 2026-03-17: Resolve non-`dist` relative `output_dir` values against the config file directory so external manuscript repos can keep portable local build destinations.
- 2026-03-08: Use Pandoc `--resource-path` derived from manuscript source directories so merged prepared markdown can retain source-relative image references.
- 2026-03-08: Add a stdlib `unittest` safety net for profile resolution, DOCX style normalization, fixture-contract helper failures, and markdown scanning edge cases rather than introducing a new test dependency.
- 2026-03-08: Refactor lint/reference scanning around a shared markdown visibility helper so fenced code/raw blocks and inline literal citation examples do not trigger false positives.
- 2026-03-08: Move generated profile/layout/source cache artefacts toward explicit Make targets keyed by config/profile selection, reducing parse-time side effects while preserving current entrypoints.
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
- 2026-02-13: Provide a cross-platform dependency helper with Ubuntu/WSL and macOS minimal/full package tiers.
- 2026-02-13: Use cached apt package installs in CI to reduce repeated dependency provisioning overhead.
- 2026-02-13: Keep cached apt setup in CI, but add explicit `apt-get install` verification in build jobs to avoid TeX font availability drift.
- 2026-02-13: Add `wsl-smoke` aggregate Make target to validate bootstrap, profile resolution, local CSL lookup, builds, fixture golden checks, and guard tests in one command.
- 2026-02-13: Generate profile cache include files atomically in `Makefile` to avoid parse-time race failures during concurrent make invocations.
- 2026-02-13: Add strict config-contract validation before builds to catch schema/path regressions early.
- 2026-02-13: Emit machine-readable build manifests for active and fixture profiles to improve reproducibility and evidence capture.
- 2026-02-13: Keep fixture expectations in a versioned YAML contract and expose the canonical `fixture-contract-check` target.
- 2026-02-13: Collect diagnostics bundles on CI failure for faster triage without rerunning jobs locally.
- 2026-02-13: Add profile-driven PDF layout controls through generated include files (page numbers, line spacing, line numbering), applied via `--include-in-header`.
- 2026-02-13: Fixed line-numbering detection by checking LaTeX packages via `kpsewhich` in `scripts/render_pdf_layout.py`.
- 2026-02-13: Add source-merge normalization step (`scripts/prepare_markdown_sources.py`) that injects `<div id="refs"></div>` after first `## References` heading to allow in-document bibliography placement.
- 2026-02-13: Add automatic output-root derivation for `output_dir: dist`, routing builds into `dist/<profile-root>/` so default profile outputs no longer land in raw `dist/`.
- 2026-02-13: Improve line-numbering and margins diagnostics by emitting build-time warnings when LaTeX packages (`lineno`, `etoolbox`, `geometry`) are unavailable for selected profile styling options.
- 2026-02-13: Add profile-controlled figure handling in source preparation (`figures` settings) with page-mode defaults, supplementary ordering, caption placement, and optional inline placeholder routing.
- 2026-02-13: Add dedicated regression target `make test-figure-modes` for pages/inline figure placement behaviors.
- 2026-02-13: Extend figure handling with `placement: captions_page` for a dedicated Figure Captions page and title-bearing figure blocks.

## Work Log
- 2026-04-24: Hardened `scripts/lint_manuscript.py` so parenthesized
  acronym-plus-Pandoc-citation text, such as `FD [@key]`, no longer triggers a
  false manual-citation failure; added regression tests for the accepted and
  still-failing mixed citation cases.
- 2026-03-17: Added `scripts/install_deps.sh`, switched `Makefile` dependency targets to use it, and added macOS PATH handling for `/Library/TeX/texbin`.
- 2026-03-17: Updated `README.md` bootstrap docs so `make deps-*` covers both Ubuntu/WSL and macOS.
- 2026-03-17: Fixed macOS bootstrap to install `PyYAML` for `python3` and bypass profile-loading during `make deps-*` runs.
- 2026-03-17: Updated `scripts/build_profile.py` so non-`dist` relative `output_dir` values resolve from the config directory, matching external manuscript expectations on macOS and Linux.
- 2026-03-08: Updated `scripts/build_profile.py` and downstream callers so config-relative profile entries resolve against the config file directory and surface as resolved absolute paths.
- 2026-03-08: Updated `scripts/prepare_markdown_sources.py` to validate source-relative image resources early and fail with resolved paths for missing assets.
- 2026-03-08: Added Pandoc `--resource-path` wiring in `Makefile` based on resolved manuscript source directories.
- 2026-03-08: Added `scripts/test_external_relative_paths.sh` plus CI coverage for a synthetic external-manuscript repo using relative config entries and source-relative image paths.
- 2026-03-08: Updated in-repo fixture config and figure markdown to follow the new config-relative/source-relative contract.
- 2026-03-08: Updated AGENTS, README, handover, and external-manuscript primer docs to describe the new path semantics.
- 2026-03-08: Added `tests/` coverage for `build_profile`, `normalize_docx_styles`, `fixture_golden_check`, and markdown scanning edge cases.
- 2026-03-08: Added `make python-tests`, added explicit Poppler preflight for fixture contract checks, and updated CI to run Python unit tests plus `make test-output-routing`.
- 2026-03-08: Added shared helper `scripts/markdown_scan.py` and updated lint/reference audit flows to ignore fenced code blocks, raw blocks, and inline code examples while preserving CLI behaviour.
- 2026-03-08: Added shared schema constants in `scripts/profile_schema.py` and reused them across resolver, validator, scaffold, and DOCX normalization paths.
- 2026-03-08: Refactored `Makefile` cache generation so profile include files, prepared markdown, and layout fragments are generated as explicit cache targets keyed by selected config/profile.
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
- 2026-02-13: Added dependency helper targets (`deps-estimate-*`, `deps-install-*`, `deps-dry-run-*`) backed by the cross-platform installer.
- 2026-02-13: Added `scripts/profile_scaffold.py` and `make profile-scaffold` wrapper target for profile generation/appending.
- 2026-02-13: Added `scripts/fixture_golden_check.py` and integrated it into `check-fixture`.
- 2026-02-13: Updated GitHub Actions CI to use cached apt package setup and run fixture golden checks.
- 2026-02-13: Expanded `README.md` with Ubuntu/WSL bootstrap and profile scaffold instructions.
- 2026-02-13: Detected CI regression (`run 21974358589`) caused by cache-only build dependency restore missing TeX font readiness.
- 2026-02-13: Added explicit build-job dependency verification step (`apt-get install -y ...`) after cache restore and revalidated green CI.
- 2026-02-13: Added `make wsl-smoke` target and documented WSL clone options (HTTPS and SSH) in README.
- 2026-02-13: Switched profile cache generation writes to temp-file-and-rename for concurrency safety.
- 2026-02-13: Added `scripts/validate_build_config.py` and integrated `make validate-config` into `check` and `check-fixture`.
- 2026-02-13: Added `scripts/render_pdf_layout.py`, integrated layout header generation into PDF build targets, and extended `settings/build.yaml` with layout keys.
- 2026-02-13: Updated `scripts/profile_scaffold.py` and `Makefile` to include `PAGE_NUMBERS`, `LINE_SPACING`, and `LINE_NUMBERING` options in scaffold and profile-driven builds.
- 2026-02-13: Added `scripts/build_manifest.py` and `scripts/diagnose_build.py`.
- 2026-02-13: Added `Makefile` targets for manifests (`manifest`, `fixture-manifest`, `show-manifest`) and diagnostics (`diagnose`, `fixture-diagnose`).
- 2026-02-13: Added fixture contract file `testbed/expected/golden_contract.yaml` and wired contract-aware fixture checks.
- 2026-02-13: Updated CI to run config validation, publish manifest artifacts, and upload diagnostics bundles on failure.
- 2026-02-13: Updated README and fixture expectation docs for contract/manifests/diagnostics workflows.
- 2026-02-13: Verified updated CI run (`21975285208`) passed with new config-validation, manifest artifact, and failure-diagnostics steps.
- 2026-02-13: Verified `## References` in testbed main is honored as bibliography insertion point via fixture output.
- 2026-02-13: Added `margins` controls to profile defaults and schema validation; defaults are A4 + 1.5 cm.
- 2026-02-13: Fixed line-numbering check path in `scripts/render_pdf_layout.py` so `lineno` availability is detected via `kpsewhich` instead of `\IfFileExists`.
- 2026-02-13: Extended `make profile-scaffold` to include margin-related arguments for `paper_size` and per-side values.

## Command Evidence
- 2026-10-22: `make python-tests` passes 41 tests, including a real Pandoc 3.1.3
  DOCX round-trip retaining math, links, descriptions and unrelated custom
  metadata. Namespace declarations, property ordering, geometry, footer
  relationships, repeated normalization and disabled numbering are checked.
- 2026-10-22: `make test-author-injection`, `make test-figure-modes`, `make check`
  and `make check-fixture` pass sequentially. The fixture has one table, three
  images and eight PDF pages. A LibreOffice 24.2 DOCX render was inspected on
  all eight pages: A4, page numbers 1–8, readable equations/figures and no image
  height line numbering. The fixture's narrow `Presence` column still wraps
  its header; authored column proportions remain a manuscript layout concern.
- `PATH="/Users/bwbrook/work/makedoc/.venv/bin:$PATH" make python-tests` -> PASS
  (23 tests, including the manual-citation lint false-positive regression).
- `PATH="/Users/bwbrook/work/makedoc/.venv/bin:$PATH" make check CONFIG=/Users/bwbrook/papers/rc-dates/settings/build.yaml` -> PASS
  (external `rc-dates` profile validates, lints, audits references, builds DOCX/PDF, and writes manifest).
- `python3 -m unittest discover -s tests -p 'test_*.py'` -> PASS (18 tests including config-relative resolution, resource-path derivation, and source-relative image validation)
- `make validate-config` -> PASS (default + fixture configs now validate through config-relative path resolution)
- `make test-figure-modes` -> PASS (temp repo fixture exercises source-relative figure image paths)
- `make test-external-relative-paths` -> PASS (synthetic external repo succeeds with relative config entries and source-relative image paths)
- `make test-output-routing` -> PASS (output routing unchanged after config-relative/source-relative migration)
- `make check && make check-fixture && make check-fixture-guards && make profiles && make profile-show` -> PASS (full sequential repo validation green with absolute resolved profile display)
- `python3 -m unittest discover -s tests -p 'test_*.py'` -> PASS (13 tests covering output routing logic, DOCX XML normalization, fixture-contract failure paths, and markdown scanning behaviour)
- `make python-tests` -> PASS (same 13 stdlib unit tests through the canonical Make target)
- `make validate-config` -> PASS (`Build config validation passed for selected profile(s): default` and `fixture`)
- `make test-output-routing` -> PASS (fixture-only, default-profile, and fallback-output routing all succeed with keyed cache artefacts)
- `make check && make check-fixture && make check-fixture-guards` -> PASS (full sequential repo validation passes after markdown-scanning, schema-sharing, and Makefile refactors)
- `make profiles && make profile-show && make show-manifest` -> PASS (profile listing/show and manifest display remain functional after the Make bootstrap refactor)
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
- `make wsl-smoke` -> PASS (all bootstrap and build/guard checks completed successfully in one run)
- `(make profile-show >/tmp/makedoc_profile_a.out & make profile-show >/tmp/makedoc_profile_b.out & wait)` -> PASS (concurrent profile cache generation remained stable)
- `python3 -m py_compile scripts/build_profile.py scripts/validate_build_config.py scripts/build_manifest.py scripts/diagnose_build.py scripts/fixture_golden_check.py scripts/lint_manuscript.py scripts/refs_audit.py scripts/csl_resolver.py scripts/profile_scaffold.py` -> PASS
- `python3 - <<'PY' ... yaml.safe_load('.github/workflows/ci.yml') ...` -> PASS (updated workflow YAML parses)
- `make validate-config` -> PASS (`Build config validation passed for selected profile(s): default, fixture`)
- `make check` (Phase 8 hardening) -> PASS (includes config validation and writes `dist/<profile-root>/<output_stem>_build_manifest.json`)
- `make check-fixture` (Phase 8 hardening) -> PASS (includes config validation, fixture manifest, and contract checks)
- `make check-fixture-guards` (Phase 8 hardening) -> PASS (all three expected-failure guards still observed)
- `make show-manifest` -> PASS (pretty-printed active manifest JSON)
- `make diagnose` -> PASS (created `dist/diagnostics/<timestamp>_default` bundle)
- `make fixture-diagnose` -> PASS (created `dist/diagnostics/<timestamp>_fixture` bundle)
- `make fixture-contract-check` -> PASS (fixture contract checks passed)
- `make manifest && make fixture-manifest` -> PASS (manifests present; make reports up-to-date)
- `gh run watch 21975285208 --repo BWBrook/makedoc --exit-status` -> PASS (Phase 8 CI run green; diagnostics upload steps skipped because no failures)
- `make testbed` -> PASS (created `dist/testbed/fixture_manuscript.pdf`, `dist/testbed/fixture_manuscript.docx`, `dist/testbed/fixture_manuscript_build_manifest.json` and no root `dist/` files)
- `make PROFILE=fixture check-fixture` -> PASS (fixture pipeline + contract check; `Build config` validated and outputs remain under `dist/testbed/*`)
- `make test-output-routing` -> PASS (`dist/testbed` outputs only for fixture flows; default `make all` routes to `dist/` as expected)
- `./scripts/test_output_routing.sh` -> PASS (`dist/manuscript-#` fallback path is validated with a synthetic profile and no `.git`/`manuscript/` context).
- `make all` -> PASS and no LaTeX undefined-figure-reference warnings after adding two-pass PDF rendering for LaTeX engines.
- `python3 -m py_compile scripts/build_profile.py scripts/render_pdf_layout.py scripts/validate_build_config.py scripts/profile_scaffold.py` -> PASS
- `make clean && make all` -> PASS (layout-aware PDF/DOCX and manifest generation succeed for default profile)
- `make PROFILE=fixture all` -> PASS (fixture profile builds to `dist/testbed` with layout-aware includes)
- `make check` -> PASS (`check-tools`, validation, lint, refs-audit, build, manifest path all pass)
- `make check-fixture` -> PASS (fixture checks + contract checks pass with layout header generation)
- `make test-output-routing` -> PASS (routing regression passes)
- `python3 -m py_compile scripts/prepare_markdown_sources.py` -> PASS
- `make check` -> PASS (reference-anchor normalization in source merge path included)
- `make check-fixture` -> PASS (`## References` heading in fixture now anchors rendered bibliography).
- `make all` -> PASS and now produces `dist/testbed/manuscript.*` instead of `dist/manuscript.*` for the default profile.
- `make all` -> PASS and fixture figure reference warnings are now resolved after rerendering PDF with second LaTeX pass.
- `python3 -m py_compile scripts/build_profile.py scripts/render_pdf_layout.py scripts/validate_build_config.py scripts/profile_scaffold.py` -> PASS
- `make clean && make all` -> PASS (`line numbering and margin options active in profiles; outputs in dist/testbed`).
- `make profile-scaffold PROFILE_NAME=demo_profile` -> PASS (includes margin defaults in emitted snippet).
- `make check-fixture` -> PASS (`figure placement and caption settings applied during source prep; golden contract updated for figure labels`).
- `make test-output-routing` -> PASS (output location behavior unchanged by figure pipeline edits).
- `make clean && make all` -> PASS (`default and fixture figure placement now produces one figure per page with Fig. labels`).
- `make test-figure-modes` -> PASS (`pages mode includes ordered labels with one clearpage per figure; inline mode removes placeholder, suppresses clearpage, and keeps caption below image`).
- `make test-figure-modes` -> PASS (`new captions_page mode adds Figure Captions page and successive title-bearing figure pages`).
- `make test-output-routing` -> PASS after config split (`settings/build.yaml` for active + `settings/fixture.yaml` for fixture); confirms fixture outputs now land in `dist/fixture/*`.
- `make check-fixture` -> PASS after fixture config split (fixture lint/audit/build/contract checks run from `settings/fixture.yaml`).
- `make all` -> PASS and produces only active outputs under `dist/testbed/*` (no fixture outputs rebuilt by default).
- `make test-author-injection` -> PASS (placeholder replacement and after-title fallback are both validated).
- `make check` / `make check-fixture` -> PASS with profile-driven author metadata injection and testbed `authors.yaml` path checks enabled.
- `python3 -m py_compile scripts/prepare_markdown_sources.py` -> PASS (section-flow and author-superscript changes compile cleanly).
- `make test-author-injection` -> PASS (now also validates default page breaks after authors, before `Introduction`, and before `References`, plus level-2 spacing guard).
- `make test-figure-modes` -> PASS (inline mode updated for default references page break while preserving no figure-page break behavior).
- `make check && make check-fixture && make -B all` -> PASS (full validation suite and forced rebuild with new section-flow defaults).

## Build Warnings
- Previous PDF warning for Unicode em-space (`U+2003`) no longer reproduced after Phase 2 edits.

## Open Issues
- Figures are linked and rendered, but panel-level references (e.g., 1A, 1B) still point to whole-figure anchors by design.
- Further CI hardening options remain (for example richer PR annotations), now supported by both real and synthetic guard suites.
