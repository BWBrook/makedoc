# Plan: PDF Review Markup Legibility Hardening

## Intent

Fix the review-markup rendering policy where it matters most: a human reading
the generated PDF must be able to understand deleted/old wording. Keep the
change small and honest, and prove it with visual PDF evidence.

## Likely Files To Touch

- `scripts/prepare_markdown_sources.py` - review-markup transform.
- `tests/test_prepare_markdown_sources.py` - transform contract tests.
- `scripts/test_review_markup.sh` - artifact-level regression checks.
- `README.md` - public rendering contract if policy changes.
- `docs/makedoc_primer_for_agents.md` - external authoring/rendering contract.
- `docs/goals/004-pdf-review-markup-legibility-hardening/Log.md` - execution
  and evidence record.

Only touch Makefile/build graph files if the chosen solution truly needs
format-aware PDF/DOCX source preparation.

## Steps

1. Capture state.
   - Record `makedoc` status/HEAD.
   - Record CPE status/HEAD.
   - Confirm CPE is still the dirty Goal 003 pilot branch.

2. Read required context.
   - Read all `Read First` files from `Goal.md`.
   - In CPE, read only the authorized pilot files.

3. Reproduce the visual problem.
   - Use existing fixture or CPE pilot output.
   - Render the relevant PDF page to PNG with `pdftoppm`.
   - Record that current deletion text is not readable enough by eye.

4. Choose a rendering policy.
   - Prefer a single simple policy if it gives acceptable PDF and DOCX output.
   - Use format-aware source prep only if that is clearly the smallest robust
     way to preserve DOCX strikeout while fixing PDF legibility.
   - Avoid new dependencies and colour styling unless they are clearly free.

5. Write focused tests first.
   - Update or add tests that pin the chosen prepared Markdown output.
   - Ensure default-off behavior and protected regions still pass.

6. Implement the smallest change.
   - Keep source token syntax unchanged.
   - Keep review markup default-off.
   - Preserve existing figure/code/comment protections.

7. Update artifact regression checks.
   - Update `scripts/test_review_markup.sh` so it checks the new deletion/old
     wording evidence in prepared Markdown, PDF text, and DOCX XML where
     applicable.
   - If visual evidence cannot be automated robustly, generate a page image and
     record manual inspection in `Log.md`.

8. Update docs.
   - Revise README and primer if PDF/DOCX rendering descriptions change.
   - Be explicit if PDF and DOCX render deletion differently.

9. Validate the fixture.
   - Run targeted unit tests.
   - Run `make test-review-markup`.
   - Run the review-markup profile build and artifact checks.

10. Validate against CPE.
    - Use the existing CPE pilot branch as-is.
    - Do not edit CPE source files.
    - Rebuild `PROFILE=review_markup_pilot`.
    - Inspect PDF/DOCX artifacts and render the PDF page image.

11. Run the broader ladder.
    - Run author/figure regressions.
    - Run `make check` and `make check-fixture`.
    - Run `git diff --check`.

12. Finalize.
    - Update `Log.md` with decisions, artifacts, visual result, validation, and
      final statuses.
    - Leave changes unstaged.
    - Wake the orchestrator and stop.

## Expected Outcome

Expected best outcome: review-markup deletion text becomes readable in PDF
while DOCX remains strong. The docs tell the truth about the chosen rendering
policy, and the regression script proves the behavior with generated artifacts.

Acceptable blocker outcome: the current build path cannot satisfy both PDF
readability and DOCX strikeout without a broader build-graph change. In that
case, stop with evidence and recommend the smallest next design decision.
