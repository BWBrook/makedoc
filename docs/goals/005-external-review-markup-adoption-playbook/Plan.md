# Plan: External Review Markup Adoption Playbook

## Intent

Document the review-markup adoption pattern now that the feature has moved from
fixture proof to external CPE pilot and PDF-legible rendering.

Keep this goal documentation-only in makedoc, with CPE used only as read-only
evidence.

## Steps

1. Confirm starting state.
   - `makedoc` should be clean on `main...origin/main` at `e4be37c`.
   - CPE should be on `codex/makedoc-review-markup-pilot` at `e1b2433` with
     the preserved pilot diff.

2. Inspect CPE evidence narrowly.
   - Read CPE `AGENTS.md` first.
   - Check status and HEAD.
   - Read `settings/build.yaml`.
   - Read `manuscript/text/main_review_markup_probe.md`.
   - Confirm canonical `main.md` has no review tokens.
   - Check whether existing pilot outputs are present.

3. Write the playbook.
   - Prefer `docs/review_markup_external_adoption.md`.
   - Include non-goals and decision gates.
   - Ground the CPE branch disposition explicitly.

4. Add pointers.
   - Add only short README and primer pointers.
   - Do not duplicate the full playbook.

5. Create the Goal 005 packet.
   - Include goal, plan, runbook, and log.
   - Record starting state and CPE evidence.

6. Validate.
   - Run `make test-review-markup`.
   - Run `git diff --check`.
   - Do not run CPE builds.

7. Wake and stop.
   - Include changed files, CPE inspection, CPE status, validation, artifact
     regeneration status, and recommended next step.

## Expected Outcome

Expected outcome: a concise adoption playbook that lets future agents pilot
review markup in external manuscript repos without contaminating canonical
sources or committing generated evidence artifacts by default.

Expected CPE outcome: branch preserved unchanged for Barry/orchestrator
inspection.
