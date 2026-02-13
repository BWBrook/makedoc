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

Out of scope for this iteration:
- Full citation token migration (`(Author year)` -> `[@citekey]`)
- Figure/cross-reference wiring and numbering conventions
- Journal-specific Word style template (`reference.docx`) tuning
- CI automation

## Milestones
1. Phase 1 (current): Build scaffold and repository bootstrap
2. Phase 2: Manuscript normalization (table/math/unicode cleanup)
3. Phase 3: Citation migration and unresolved-citation reporting
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

## Update Protocol
- Update this file whenever scope, milestones, acceptance criteria, or status changes.
- Record command-level execution details and decisions in `docs/builder_notes.md`.
