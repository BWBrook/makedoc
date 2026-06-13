# Goal: Review Markup Production Hardening

## Objective

Turn the Goal 001 review-markup spike into a stable, documented, default-off
experimental feature that manuscript authors and external-repo agents can opt
into safely.

Success means a person can read a small, documented Markdown authoring contract,
enable `review_markup.enabled`, run a first-class regression target, and see
traceable additions/deletions/substitutions/notes in generated DOCX/PDF output
without changing ordinary manuscript builds.

## Why This Matters

Goal 001 proved that CriticMarkup-like Markdown tokens can render visibly in
DOCX/PDF through ordinary Pandoc Markdown. Goal 002 should make that route
dependable enough to keep in the toolkit.

This goal is deliberately a hardening step, not a second research spike. The
longer-horizon ideas remain:

- visible Markdown-origin review markup in generated DOCX/PDF outputs;
- possible future DOCX-to-Markdown change import;
- possible future native Word Track Changes support.

Only the first item is in scope here.

## Operating Mode

Implementation hardening plus documentation.

## Review Surface

The Makedoc orchestrator will review:

- the docs diff, especially the README and agent primer contract;
- the Makefile/test diff for a first-class review-markup regression surface;
- any source/schema/test changes needed to make the authoring contract true;
- generated proof evidence if rendering behavior or styling changes;
- `Log.md` and validation evidence.

## Scope

In scope:

- Document `review_markup.enabled` in the config schema and profile examples.
- Document the supported authoring syntax:
  - `{++ added text ++}`
  - `{-- deleted text --}`
  - `{~~ old text ~> new text ~~}`
  - `{>> reviewer note <<}`
- State the authoring contract clearly:
  - disabled by default;
  - line-local tokens only;
  - no nested review markup;
  - inline code, fenced code blocks, hidden/raw blocks, and figure image lines
    are not transformed;
  - intended for visible generated review traces, not Word Review-pane data.
- Add or promote a first-class `make test-review-markup` regression target.
- Add focused tests or a shell regression script proving the prepared Markdown
  and, where practical, DOCX/PDF evidence for the review-markup probe.
- Expand unit/schema tests only where needed to enforce the documented
  contract.
- Decide and record whether the current bold/bracket/strike rendering remains
  the production-experimental style for now.
- Keep `docs/markdown_review_markup_spike.md` as the Goal 001 decision memo;
  update it only if a short status note is useful, not as the main docs home.

Out of scope:

- True Microsoft Word Track Changes XML or Review-pane semantics.
- DOCX-to-Markdown import.
- Round-trip change reconciliation.
- Broad external manuscript road tests.
- New dependencies unless the current route becomes impossible without one.
- Changing default behavior for ordinary profiles.
- Commit, push, PR creation, or publication work.

## Read First

- `AGENTS.md` - repo rules, validation expectations, and external-path policy.
- `README.md` - current public build/profile/check surface.
- `docs/makedoc_primer_for_agents.md` - external manuscript authoring contract.
- `docs/markdown_review_markup_spike.md` - Goal 001 decision memo.
- `docs/goals/001-markdown-review-markup-feasibility/Goal.md`
- `docs/goals/001-markdown-review-markup-feasibility/Log.md`
- `settings/review_markup.yaml` - proof profile added by Goal 001.
- `testbed/manuscript/text/review_markup_probe.md` - proof manuscript source.
- `scripts/prepare_markdown_sources.py` - review-markup transform hook.
- `scripts/build_profile.py` - profile resolution and `review_markup` parsing.
- `scripts/profile_schema.py` - allowed profile keys.
- `scripts/validate_build_config.py` - config/schema validation.
- `tests/test_prepare_markdown_sources.py`
- `tests/test_build_profile.py`
- `tests/test_validate_build_config.py`
- `Makefile` - validation targets and sequencing expectations.

## Starting State Checks

Run from `/Users/bwbrook/work/makedoc` before implementation:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
git log -5 --oneline
```

Expected baseline before this packet was written:

```text
## main...origin/main
```

Expected HEAD:

```text
42802b5 Add markdown review markup feasibility spike
```

After this packet is present, the Goal 002 files should appear as untracked
orchestrator-authorized work. Do not treat those files as cleanup.

## Git And Publication Policy

- Edits are allowed for this goal.
- Do not commit or push.
- Do not stage files; leave all changes unstaged for orchestrator review.
- Do not fetch, pull, reset, clean, stash, or discard existing state.
- Do not remove generated ignored outputs unless they block validation.
- Report any unexpected dirty or untracked files before widening work.

## Data, Compute, And Staging Policy

- Use only the local Mac mini checkout at `/Users/bwbrook/work/makedoc`.
- Work only inside this repository.
- Do not read Chief of Staff, Goal Composer, sibling project repositories,
  archive material, or unrelated user files.
- Keep generated build outputs under existing ignored locations such as
  `dist/` and `.cache/`.
- Do not force-add generated DOCX/PDF outputs.
- Run top-level Make targets sequentially, never in parallel.

## Required Work

1. Capture and log the starting state.
2. Read the required files above.
3. Document the review-markup profile option in `README.md`.
4. Document the external-author contract in
   `docs/makedoc_primer_for_agents.md`.
5. Add a first-class `make test-review-markup` target unless a better
   existing target clearly covers the same job. If you choose not to add it,
   explain why in `Log.md`.
6. Add focused regression coverage for the review-markup proof path. The
   target should at minimum prove that:
   - the profile validates;
   - prepared Markdown contains addition, deletion, substitution, and reviewer
     note traces;
   - inline code/fenced code/figure-line protections remain true;
   - generated DOCX/PDF evidence is either checked directly or regenerated by
     an explicitly documented command.
7. Add any narrow unit/schema tests needed to align implementation with the
   documented contract.
8. Make a styling policy call. Default preference: keep the current
   bold/bracket/strike rendering unless a small, robust improvement works
   cleanly in both DOCX and PDF without new dependencies.
9. Update `Log.md` with decisions, validation output, final git status, and
   remaining risks.

## Validation Gates

Run sequentially. The goal is not complete until these pass or a blocker is
reported with evidence:

- targeted review-markup unit tests or shell tests;
- `make test-review-markup` if added;
- `CONFIG=settings/review_markup.yaml make validate-config`;
- `CONFIG=settings/review_markup.yaml make -B all` if rendering evidence
  needs to be regenerated or styling changed;
- `make test-author-injection`;
- `make test-figure-modes`;
- `make check`;
- `make check-fixture`;
- `git diff --check`.

If a broader check fails after the focused review-markup target passes, stop
and report the smallest likely cause before widening.

## Deliverables

- Updated README documentation for `review_markup.enabled`.
- Updated external-agent primer documentation for review-markup authoring.
- A first-class review-markup regression target or a documented reason it was
  not added.
- Focused tests/script changes needed for the target.
- Any narrow schema/source-prep fixes required by the documented contract.
- Updated `Log.md`.
- Final report with changed files, validation, remaining risks, and final
  `git status --short --branch`.

## Decision Authority

You may decide:

- exact docs wording and placement;
- exact target/script naming if `make test-review-markup` remains available;
- whether the target checks generated PDF/DOCX files directly or keeps direct
  artifact inspection in the runbook;
- whether current bold/bracket/strike styling is the right
  production-experimental policy;
- small test refactors that keep behavior unchanged.

Pause before:

- adding dependencies;
- implementing native Word Track Changes;
- implementing DOCX-to-Markdown import;
- changing defaults for existing profiles;
- modifying external manuscript repositories;
- committing, staging, pushing, fetching, pulling, cleaning, resetting, or
  stashing;
- broadening into a new Goal 003.

## Checkpoint Rules

Send a wake-up to the Makedoc orchestrator if:

- the existing review-markup implementation and the documented contract cannot
  be reconciled narrowly;
- direct DOCX/PDF evidence needs a new dependency or fragile platform-specific
  inspection;
- validation fails in a way that appears unrelated to this goal;
- the work would require one of the pause-before boundaries.

## Stop Conditions

Stop when one of these is true:

- the hardening, docs, regression target, and validation evidence are complete;
- evidence shows the Goal 001 route should remain spike-only for now;
- the work would require one of the pause-before boundaries.

## Final Response Requirements

Report:

- what changed;
- where the review-markup contract now lives;
- what the new or confirmed regression target checks;
- what validation ran and whether it passed;
- whether generated proof artifacts were created and where;
- remaining risks or unknowns;
- final `git status --short --branch`;
- confirmation that there were no commits, staging, pushes, fetches, pulls,
  resets, cleans, stashes, dependency installs, external-repo reads, Chief/Goal
  Composer reads, or artifacts force-added;
- recommended next goal or explicit recommendation to pause.
