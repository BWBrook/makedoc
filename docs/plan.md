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

Out of scope for this iteration:
- Figure/cross-reference wiring and numbering conventions
- Journal-specific Word style template (`reference.docx`) tuning
- CI automation

## Milestones
1. Phase 1 (completed): Build scaffold and repository bootstrap
2. Phase 2 (completed): Manuscript normalization (table/math/unicode cleanup)
3. Phase 3 (completed): Citation migration and unresolved-citation reporting
4. Phase 4: Figure/caption integration + cross-references
5. Phase 5: CI/reproducibility guardrails

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

## Update Protocol
- Update this file whenever scope, milestones, acceptance criteria, or status changes.
- Record command-level execution details and decisions in `docs/builder_notes.md`.
