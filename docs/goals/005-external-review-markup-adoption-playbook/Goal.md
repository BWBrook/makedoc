# Goal: External Review Markup Adoption Playbook

## Objective

Create a practical, reusable playbook for safely adopting the default-off
Markdown review-markup workflow in external manuscript repositories, grounded
in the CPE pilot evidence while preserving the CPE branch unchanged.

Success means a future agent or human can pilot review markup in another
external manuscript repo without contaminating canonical manuscript sources,
submission profiles, or manuscript history.

## Context

Goals 001-004 established and hardened the review-markup workflow:

- Goal 001 proved human-editable Markdown review tokens could render visibly in
  generated DOCX/PDF outputs.
- Goal 002 documented and tested the feature as default-off experimental
  behavior.
- Goal 003 proved the workflow on the external CPE manuscript using an isolated
  pilot profile and pilot source.
- Goal 004 changed deletion and old-wording rendering to readable bold
  bracketed markers so PDFs are human-readable by eye.

Barry approved this Goal 005 and delegated the CPE branch fate to the Makedoc
orchestrator.

## CPE Disposition Decision

Preserve the current CPE pilot branch unchanged as local evidence.

Do not commit it, push it, discard it, reset it, clean it, or convert it into
manuscript history during Goal 005. Cleanup or formal manuscript-side
publication should be a later explicit action after the adoption pattern is
documented and reviewed.

## Scope

Authorized paths:

- `/Users/bwbrook/work/makedoc` - implementation and documentation repo.
- `/Users/bwbrook/papers/cpe_time_to_extinction` - read-only evidence repo.

Out of scope:

- Chief of Staff, Goal Composer, sibling project repos, archive material, or
  unrelated user files.
- CPE source edits.
- CPE staging, commits, pushes, fetches, pulls, resets, cleans, stashes,
  rebases, branch switches, renames, or reconciliation.
- Regenerating CPE build artifacts unless a concrete blocker is found and the
  orchestrator is woken first.
- Engine code changes, rendering semantic changes, schema changes, Make target
  changes, tests, fixtures, or generated artifacts.
- Native Word Track Changes.
- DOCX-to-Markdown import.
- Goal 006.

## Required Work

1. Confirm expected starting state in makedoc and CPE.
2. Read CPE repo-local `AGENTS.md` before any CPE inspection.
3. Inspect only the permitted CPE evidence surface.
4. Add `docs/review_markup_external_adoption.md`.
5. Add concise pointers from README and the external-agent primer.
6. Create this Goal 005 packet with `Goal.md`, `Plan.md`, `Runbook.md`, and
   `Log.md`.
7. Run:

   ```sh
   make test-review-markup
   git diff --check
   ```

8. Leave all makedoc changes unstaged for orchestrator review.
9. Wake the Makedoc orchestrator with changed files, CPE inspection performed,
   CPE final status, validation results, whether CPE artifacts were
   regenerated, and recommended next step.

## Acceptance Criteria

- The playbook covers purpose and non-goals, safe external pilot pattern,
  authoring rules, validation checklist, evidence/artifact policy, CPE pilot
  disposition, and decision gates.
- CPE remains unchanged as local evidence.
- No CPE build artifacts are regenerated.
- No engine semantics or generated artifact policy changes are made.
- Validation passes or a blocker is reported with evidence.
- Final status and wake-up are complete.
