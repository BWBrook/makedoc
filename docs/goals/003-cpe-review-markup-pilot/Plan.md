# Plan: CPE Review Markup External Manuscript Pilot

## Intent

Exercise the review-markup workflow in a real external manuscript repository
without endangering the manuscript's clean draft/submission paths.

## File Strategy

In `/Users/bwbrook/papers/cpe_time_to_extinction`:

- Modify `settings/build.yaml` to add a `review_markup_pilot` profile.
- Create `manuscript/text/main_review_markup_probe.md` as a pilot-only copy of
  the current full draft with a tiny visible review-markup probe.
- Leave `manuscript/text/main.md` unchanged and free of review-markup tokens.
- Leave `manuscript/text/figures.md`, references, CSL, author metadata, and
  figures unchanged unless a blocker is reported.

In `/Users/bwbrook/work/makedoc`:

- Update only `docs/goals/003-cpe-review-markup-pilot/Log.md` during the pilot,
  unless the pilot exposes a true engine bug that requires orchestrator
  direction.

## Steps

1. Capture starting state in both repos.
   - Record `pwd`, status, HEAD, log summary, and remote/default evidence in
     `Log.md`.

2. Read the contracts.
   - Read all `Read First` files from `Goal.md`.
   - In CPE, read `AGENTS.md` before any other CPE file.

3. Prepare the CPE branch safely.
   - Confirm CPE is clean.
   - Run `git fetch --prune origin`.
   - Run `git merge --ff-only origin/main`.
   - Run `git switch -c codex/makedoc-review-markup-pilot`.
   - Stop if any step fails or if the branch already exists.

4. Add the pilot source.
   - Copy `manuscript/text/main.md` to
     `manuscript/text/main_review_markup_probe.md`.
   - Add a short, unmistakably pilot-only review-markup sentence near the
     start of the source, for example after the `## Abstract` heading:

     ```markdown
     Pilot-only review-markup probe: {++ inserted pilot text ++}, {-- removed pilot text --}, {~~ old pilot wording ~> revised pilot wording ~~}, and {>> confirm visible review trace output <<}.
     ```

   - Do not edit `manuscript/text/main.md`.

5. Add the pilot profile.
   - Add `review_markup_pilot` to CPE `settings/build.yaml`.
   - Base it on `draft`.
   - Use `../manuscript/text/main_review_markup_probe.md` plus existing
     `../manuscript/text/figures.md`.
   - Set output directory to `../build/review-markup-pilot`.
   - Set output stem to `cpe_time_to_extinction_review_markup_pilot`.
   - Set:

     ```yaml
     review_markup:
       enabled: true
     ```

6. Validate the engine baseline.
   - From `makedoc`, run `make test-review-markup`.

7. Validate the CPE pilot profile.
   - From `makedoc`, run validation and forced render for
     `PROFILE=review_markup_pilot`.
   - Inspect PDF text and DOCX XML for inserted/deleted/substitution/note
     traces and DOCX strikeout styling.

8. Confirm ordinary CPE paths are unaffected.
   - Validate `PROFILE=draft` and `PROFILE=submission`.
   - Confirm canonical `manuscript/text/main.md` contains no review-markup
     tokens.
   - Build draft/submission if cheap and stable; otherwise explain why profile
     validation is sufficient for this pilot.

9. Record friction and final state.
   - Update `Log.md` with command results, artifact paths, whether the docs were
     sufficient, and any rough edges in the external-path experience.
   - Run `git diff --check` in CPE.
   - Run `git diff --check -- docs/goals/003-cpe-review-markup-pilot` in
     `makedoc`.
   - Capture final statuses for both repos.

10. Wake the orchestrator and stop.
    - Do not stage, commit, push, clean, stash, reset, or start follow-up work.

## Expected Outcome

Expected best outcome: the CPE repo has a local dirty pilot branch with one
dedicated review-markup profile, one pilot-only manuscript source, generated
DOCX/PDF evidence, and no changes to canonical clean manuscript sources.

Acceptable blocker outcome: CPE cannot be fast-forwarded or branched safely, or
the external profile exposes a real `makedoc` bug that should be handled as a
separate engine goal.
