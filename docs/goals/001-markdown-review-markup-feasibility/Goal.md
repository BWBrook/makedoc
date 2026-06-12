# Goal: Markdown Review Markup Feasibility Spike

## Objective

Produce a bounded proof of concept showing whether `makedoc` can support
human-editable Markdown review markup that renders as visibly traceable edits
in generated DOCX and PDF outputs.

The spike should answer the product question, not pretend the full review
workflow is solved. A successful result may be either:

- a small working experimental path with fixture coverage and rendered evidence;
- or a clear evidence-backed recommendation that this approach should be
  changed, deferred, or rejected.

## Why This Matters

Barry wants a manuscript workflow where edits can remain traceable while the
source of truth stays in Markdown and generated DOCX/PDF outputs remain useful
for human review.

The immediate target is visible redline-style traceability in generated outputs.
The longer-horizon direction is to explore whether changes made in DOCX can
eventually be imported back into a revised, diff-tracked Markdown source. That
DOCX-to-Markdown import path is future context only for this goal.

## Operating Mode

Implementation feasibility spike with a decision memo.

## Review Surface

The Makedoc orchestrator will review:

- the code and fixture diff;
- the test/validation evidence;
- generated DOCX/PDF evidence or a clear explanation of why rendering could
  not be proven;
- a short decision memo recommending the next step.

## Scope

In scope:

- Investigate a small CriticMarkup-like Markdown syntax for additions,
  deletions, substitutions, and optional reviewer notes.
- Prefer a syntax that is hand-editable in plain Markdown, for example:
  - `{++ added text ++}`
  - `{-- deleted text --}`
  - `{~~ old text ~> new text ~~}`
  - `{>> reviewer note <<}`
- Add the smallest implementation needed to prove visible rendering in the
  existing `makedoc` pipeline.
- Keep the feature experimental and disabled by default unless you have a very
  strong reason to do otherwise.
- Add a tiny fixture or targeted regression showing review markup in source and
  its rendered/converted form.
- Document what works, what fails, and what should happen next.

Out of scope:

- True Microsoft Word Track Changes semantics in the Word Review pane.
- DOCX-to-Markdown change import.
- Broad manuscript workflow redesign.
- External manuscript road-testing.
- New dependencies unless the evidence clearly justifies them.
- Commit, push, PR creation, or release/publication work.

## Read First

- `AGENTS.md` - repo-local operating rules and validation expectations.
- `README.md` - current build profile and quality-gate surface.
- `docs/plan.md` - current completed phases and remaining scope context.
- `docs/builder_notes.md` - current implementation evidence and caveats.
- `docs/makedoc_primer_for_agents.md` - external-path policy and manuscript
  authoring contract.
- `scripts/prepare_markdown_sources.py` - likely pipeline hook for a Markdown
  source transform.
- `tests/test_prepare_markdown_sources.py` - adjacent fixture/test pattern.
- `Makefile` - validation targets and sequencing expectations.

## Starting State Checks

- Confirm `pwd` is `/Users/bwbrook/work/makedoc`.
- Confirm `git status --short --branch` before edits.
- Preserve the existing untracked `.DS_Store`; do not clean or stage it.
- Confirm `git rev-parse --short HEAD`.

## Git And Publication Policy

- Edits are allowed for this goal.
- Do not commit or push.
- Do not stage files; leave all changes unstaged for orchestrator review.
- Do not fetch, pull, reset, clean, stash, or discard existing state.
- Treat the pre-existing untracked `.DS_Store` as user/environment state to
  preserve and report.

## Data, Compute, And Staging Policy

- Use only the local Mac mini checkout.
- Keep any new durable fixture sources small and repo-local.
- Generated build outputs may be created under existing ignored output/cache
  locations such as `dist/` and `.cache/`; do not force-add generated outputs.
- Do not use remote compute or external services.
- Run top-level Make targets sequentially, never in parallel.

## Required Work

1. Investigate the smallest integration point for Markdown review markup.
2. Implement or prototype the transform behind an experimental/default-off
   path if feasible.
3. Add focused tests or fixture coverage proving the transform behavior.
4. Produce rendered DOCX/PDF evidence if practical within the existing build
   pipeline.
5. Write a short decision memo, suggested path:
   `docs/markdown_review_markup_spike.md`.

## Validation Gates

Choose validation proportional to the actual change, but the goal is not
complete until you have run and reported at least:

- targeted unit or shell tests for the review-markup behavior;
- `make test-author-injection`;
- `make test-figure-modes`;
- `make check`;
- `make check-fixture`.

Run these sequentially. If one fails, stop widening and explain the failure,
the likely cause, and the smallest next step.

If you determine that implementation should not proceed, run the relevant
non-mutating inspection/tests needed to support that recommendation and explain
why the full validation ladder was not applicable.

## Deliverables

- A minimal experimental implementation or an evidence-backed no-go decision.
- Focused tests/fixture changes, if implementation proceeds.
- A decision memo at `docs/markdown_review_markup_spike.md`.
- Updated docs only where needed to explain experimental behavior.
- Updated `Log.md` in this goal packet.
- Final report with changed files, validation, remaining risks, and git status.

## Decision Authority

You may decide:

- exact internal function/module boundaries for the spike;
- the smallest experimental config shape, if one is needed;
- whether reviewer notes should render inline, as bracketed text, or be
  deferred if they complicate the proof;
- whether the spike should stop with a no-go recommendation.

Pause before:

- adding non-standard dependencies;
- attempting real Word Track Changes XML;
- attempting DOCX-to-Markdown import;
- changing default output behavior for ordinary manuscripts;
- broadening into external manuscript road tests;
- deleting or cleaning existing files.

## Checkpoint Rules

Send a wake-up to the Makedoc orchestrator if:

- the selected rendering route cannot produce visible DOCX and PDF evidence;
- the transform conflicts with citation, figure, reference, or author-metadata
  processing;
- a new dependency appears necessary;
- the validation ladder uncovers unrelated breakage.

## Stop Conditions

Stop when one of these is true:

- the proof of concept, memo, and validation evidence are complete;
- the evidence shows the proposed route is not viable;
- the work would require one of the pause-before boundaries.

## Final Response Requirements

Report:

- what changed or was produced;
- where the memo and any fixture evidence live;
- what validation ran and whether it passed;
- what remains uncertain or risky;
- the final `git status --short --branch`;
- whether `.DS_Store` remained preserved and unstaged;
- the recommended next goal.
