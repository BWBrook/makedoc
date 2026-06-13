# Plan: Review Markup Production Hardening

## Intent

Make the Goal 001 review-markup route dependable enough to keep as an
experimental toolkit feature. Favor durable documentation, a clean Make target,
and focused regression evidence over styling ambition.

## Files Likely To Change

- `README.md` - public profile-schema and regression-command documentation.
- `docs/makedoc_primer_for_agents.md` - external manuscript authoring contract.
- `Makefile` - likely `test-review-markup` target.
- `scripts/test_review_markup.sh` - likely focused shell regression for the
  proof profile and generated evidence.
- `tests/test_prepare_markdown_sources.py` - narrow parser/contract edge tests
  if existing unit tests are insufficient.
- `tests/test_build_profile.py` and/or `tests/test_validate_build_config.py` -
  narrow schema/profile tests if docs expose unsupported input forms.
- `docs/goals/002-review-markup-production-hardening/Log.md` - work log and
  validation evidence.

Do not move or redesign the existing source-preparation pipeline unless the
documented contract cannot be met otherwise.

## Steps

1. Capture starting state.
   - Run the starting commands from `Goal.md`.
   - Record branch, status, HEAD, and last five commits in `Log.md`.
   - Note that the Goal 002 packet itself is authorized untracked state.

2. Read the required context.
   - Read all files listed under `Read First` in `Goal.md`.
   - Pay special attention to the Goal 001 memo and existing review-markup
     tests before changing behavior.

3. Decide the hardening posture.
   - Treat `review_markup.enabled` as experimental but first-class.
   - Keep it default-off.
   - Prefer the current robust bold/bracket/strike style unless a tiny style
     improvement works in both DOCX and PDF.
   - Record the styling decision in `Log.md`.

4. Document the config surface in `README.md`.
   - Add `review_markup.enabled` to the config schema list.
   - Add a concise example profile snippet.
   - Add or update regression-command documentation for
     `make test-review-markup`.
   - Make clear this is visible generated review markup, not Word Track
     Changes.

5. Document the authoring contract in the primer.
   - Add a review-markup subsection near Markdown authoring/profile setup.
   - Show the four supported token forms and their rendered intent.
   - Document line-local, no-nesting, code-block, inline-code, hidden/raw-block,
     and figure-line constraints.
   - Explain when external manuscript repos should enable it and when they
     should leave it off.

6. Add a first-class regression target.
   - Add `test-review-markup` to `.PHONY`.
   - Wire it to a small shell script or focused command sequence.
   - Prefer a script if artifact inspection needs several checks.
   - Keep the target sequential and self-contained.

7. Build the focused regression evidence.
   - Validate `settings/review_markup.yaml`.
   - Generate or inspect prepared Markdown from
     `testbed/manuscript/text/review_markup_probe.md`.
   - Assert addition, deletion, substitution, and reviewer-note traces.
   - Assert protected content remains literal where the contract says it
     should.
   - If checking rendered artifacts directly, use tools already present in the
     repo workflow, such as `pdftotext` and DOCX zip/XML inspection.

8. Add narrow unit/schema coverage as needed.
   - Add tests only for documented contract gaps.
   - Avoid broad parser rewrites or speculative syntax support.
   - Keep nested/multiline tokens explicitly unsupported unless a tiny change
     is unavoidable and well tested.

9. Run validation.
   - Run the focused target first.
   - Run the full validation ladder from `Goal.md` sequentially.
   - Record exact commands and pass/fail status in `Log.md`.

10. Finalize for orchestrator review.
    - Run `git diff --check`.
    - Capture final `git status --short --branch`.
    - Leave all changes unstaged.
    - Send the wake-up to the Makedoc orchestrator and stop.

## Expected Outcome

Expected best outcome: `review_markup.enabled` remains experimental and
default-off, but is documented, has a first-class regression target, and has a
clear authoring contract suitable for cautious use by external manuscript
repos.

Acceptable alternative outcome: the docs and regression work expose a real
contract mismatch, and the final report recommends keeping review markup
spike-only until a narrower follow-up resolves it.
