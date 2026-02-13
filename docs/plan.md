# Manuscript Build System Plan

Last updated: 2026-02-13
Owner: Codex + bwbrook

## Goal
Create a reproducible, one-command manuscript build workflow that renders journal-ready PDF and DOCX outputs from repository source files (manuscript text, figures, references, CSL).

## Scope Boundaries
In scope for this iteration:
- Build plumbing (`Makefile` + output conventions)
- Basic environment/tool checks
- Git repository initialization and first push to a private GitHub remote
- Planning and decision documentation
- Citation token migration (`(Author year)` -> `[@citekey]`) with ambiguity reporting
- Figure/caption integration and in-document cross-reference links
- Citation key audit checks against bibliography
- Synthetic fixture manuscript and testbed checks for CI regression testing
- Config-driven profile selection for manuscript source locations
- Journal-name-based CSL discovery and sourcing utility

Out of scope for this iteration:
- Journal-specific Word style template (`reference.docx`) tuning

## Milestones
1. Phase 1 (completed): Build scaffold and repository bootstrap
2. Phase 2 (completed): Manuscript normalization (table/math/unicode cleanup)
3. Phase 3 (completed): Citation migration and unresolved-citation reporting
4. Phase 4 (completed): Figure/caption integration + cross-references
5. Phase 5 (completed): CI/reproducibility guardrails
6. Phase 6 (completed): Config-driven orchestration + onboarding docs

## Phase 1 Work Package
### Deliverables
- `Makefile` with reproducible targets (`all`, `pdf`, `docx`, `check-tools`, `check`, `clean`)
- `.gitignore` for generated artifacts
- `docs/plan.md` and `docs/builder_notes.md` initialized and updated
- Local Git repo initialized, committed, connected to private GitHub repo, pushed

### Acceptance Criteria
- `make check-tools` passes on this machine
- `make docx` produces `dist/manuscript.docx`
- `make pdf` produces `dist/manuscript.pdf`
- `make all` succeeds from a clean state
- Git remote `origin` exists and default branch is pushed

## Phase 2 Work Package
### Deliverables
- Content-preserving normalization edits in `manuscript/text/draft_ms_v2.md`
- Removal of Unicode em-space warning source
- Repair of malformed table row for positive-matched control slope entry
- Updated execution evidence in `docs/builder_notes.md`

### Acceptance Criteria
- `make all` succeeds from a clean state
- `make check` passes
- PDF build no longer emits the previous `U+2003` warning
- Table row for `positive-matched control` is valid markdown and renders correctly

## Phase 3 Work Package
### Deliverables
- `Makefile` lint target `lint-manuscript` for unresolved placeholders/manual citations
- Manual citation conversion in `manuscript/text/draft_ms_v2.md`
- Ambiguity and inference log at `docs/citation_conversion_report.md`
- Updated execution evidence in `docs/builder_notes.md`

### Acceptance Criteria
- `make lint-manuscript` passes
- `make check` passes with lint and build stages
- No manual author-year citations remain in converted manuscript sections
- Citation conversion caveats are documented

## Phase 4 Work Package
### Deliverables
- Multi-source rendering from manuscript + figure-captions files
- Figure caption file converted into renderable figure blocks with stable IDs
- In-text figure references linked to figure IDs
- `refs-audit` command added to verify cited keys exist in bibliography
- User-confirmed citation caveats locked as final in `docs/citation_conversion_report.md`

### Acceptance Criteria
- `make clean && make all` succeeds with figures included from `manuscript/text/figure_captions_v2.md`
- In-text figure references resolve to internal anchors in output
- `make refs-audit` passes with zero unknown citation keys
- `make check` passes with tool check, manuscript lint, refs audit, and build steps

## Phase 5 Work Package
### Deliverables
- GitHub Actions workflow at `.github/workflows/ci.yml`
- CI provisioning of required toolchain (`pandoc`, `xelatex`, `ripgrep`, `python3-yaml`)
- CI execution of `make check` on push/PR/manual dispatch
- Build artifact upload (`dist/`) in CI
- Separate synthetic fixture strategy drafted at `docs/testbed_workplan.md`
- Synthetic fixture implementation under `testbed/` with fixture check targets
- Deliberate edge-case guards for unknown citekeys, manual citations, and malformed tables
- Hardened CI job structure: guard tests first, then parallel main/fixture build jobs

### Acceptance Criteria
- CI workflow file is valid YAML and tracked in repo
- Workflow triggers on `push`, `pull_request`, and `workflow_dispatch`
- Workflow runs `make check` end-to-end
- Workflow uploads `dist/` artifacts for inspection
- Synthetic fixture strategy is documented as an independent follow-on stream
- `make check-fixture` passes locally and in CI
- `make check-fixture-guards` passes by asserting expected failures for edge-case fixtures

## Phase 6 Work Package
### Deliverables
- Profile YAML config in `settings/build.yaml` for default and fixture runs
- Profile resolver utility `scripts/build_profile.py`
- Refactored `Makefile` that sources profile variables from YAML
- Root onboarding documentation at `README.md`
- Journal-style resolver utility `scripts/csl_resolver.py` with search and source/download flows
- Make targets for CSL operations (`csl-search`, `csl-source`)

### Acceptance Criteria
- `make all` and `make check` run from the configured default profile without bespoke manuscript folders
- `make PROFILE=fixture all` and `make check-fixture` continue to pass
- `make profiles` and `make profile-show` report active config state
- `make csl-search JOURNAL="..."` surfaces style matches
- `make csl-source JOURNAL="..."` resolves a local style or downloads a suitable one
- `README.md` documents quickstart, config schema, and external-repo path usage

## Risks and Mitigations
- Citation placeholders and non-token citations may limit final bibliography formatting
  - Mitigation: keep Phase 1 focused on build plumbing; handle citation migration in Phase 3
- Markdown math parsing mismatch (`\\[ ... \\]`) can break PDF build
  - Mitigation: use explicit pandoc input format extensions in `Makefile`
- TeX/font differences across systems can affect rendering
  - Mitigation: lock commands and capture tooling versions in builder notes

## Status
- [x] Plan and builder notes scaffolding
- [x] Makefile and gitignore implementation
- [x] Build verification
- [x] GitHub private remote setup and push

## Latest Execution Notes
- 2026-02-13: `make check-tools`, `make all`, and `make check` all passed.
- 2026-02-13: Build outputs created at `dist/manuscript.pdf` and `dist/manuscript.docx`.
- 2026-02-13: Non-blocking warning observed during PDF build for Unicode em-space (`U+2003`) in manuscript text.
- 2026-02-13: Git initialized on branch `main` and first commit created (`67e6938`).
- 2026-02-13: Private GitHub remote created and pushed: `https://github.com/BWBrook/makedoc`.
- 2026-02-13: Phase 2 normalization edits applied to manuscript source (removed standalone em-space and corrected malformed table row).
- 2026-02-13: `make clean && make all` and `make check` passed after normalization with no previous em-space warning.
- 2026-02-13: Added `lint-manuscript` target and integrated it into `make check`.
- 2026-02-13: Converted manual author-year citations in manuscript to Pandoc citekeys and removed `[REF]` placeholder.
- 2026-02-13: Recorded citation mapping caveats in `docs/citation_conversion_report.md` and revalidated with `make lint-manuscript` + `make check`.
- 2026-02-13: Added `refs-audit` target and integrated it into `make check`.
- 2026-02-13: Switched build to render combined sources (`draft_ms_v2.md` + `figure_captions_v2.md`) and converted captions file to actual figure blocks with IDs.
- 2026-02-13: Linked in-text `Fig.` references to figure anchors (`#fig-main-insurance`, `#fig-main-richness`) and validated anchor generation in LaTeX output.
- 2026-02-13: Locked citation caveats as final per user confirmation.
- 2026-02-13: Added GitHub Actions CI workflow (`.github/workflows/ci.yml`) to install dependencies and run `make check` for push/PR/manual runs.
- 2026-02-13: Added CI artifact upload of `dist/` outputs for inspection.
- 2026-02-13: Drafted separate synthetic fixture/testbed workstream plan at `docs/testbed_workplan.md`.
- 2026-02-13: Verified first CI execution passed on GitHub (`manuscript-ci` run `21971671370`, job `build-and-check`).
- 2026-02-13: Implemented synthetic fixture assets and build pipeline under `testbed/`.
- 2026-02-13: Added `check-fixture` and fixture lint/refs-audit targets; verified local pass.
- 2026-02-13: Updated CI to run both `make check` and `make check-fixture`.
- 2026-02-13: Added `scripts/lint_manuscript.py` with markdown table validation and GitHub annotation support.
- 2026-02-13: Added edge-case fixtures and `check-fixture-guards` to assert expected failures for unknown citekeys/manual citations/malformed tables.
- 2026-02-13: Hardened CI into three jobs (`guard-tests`, `build-main`, `build-fixture`) with artifact summaries and uploads.
- 2026-02-13: Suppressed GitHub error annotations for expected-failure guard fixtures via `DISABLE_GHA_ANNOTATIONS=1`.
- 2026-02-13: Verified hardened CI passed on GitHub (`manuscript-ci` run `21972670054`) with all three jobs green.
- 2026-02-13: Revalidated hardened CI on GitHub (`manuscript-ci` run `21972735861`) with `guard-tests`, `build-main`, and `build-fixture` all succeeding.
- 2026-02-13: Introduced profile-driven build configuration (`settings/build.yaml`) and resolver script (`scripts/build_profile.py`).
- 2026-02-13: Refactored `Makefile` to consume resolved profile values for main and fixture pipelines.
- 2026-02-13: Added root `README.md` with quickstart and external repository wiring guidance.
- 2026-02-13: Added journal-style resolver (`scripts/csl_resolver.py`) and Make targets `csl-search` / `csl-source`.
- 2026-02-13: Revalidated gates after config transition (`make check`, `make check-fixture`, `make check-fixture-guards` all passed).

## Update Protocol
- Update this file whenever scope, milestones, acceptance criteria, or status changes.
- Record command-level execution details and decisions in `docs/builder_notes.md`.
