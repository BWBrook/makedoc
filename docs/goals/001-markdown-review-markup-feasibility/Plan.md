# Plan: Markdown Review Markup Feasibility Spike

## Intent

Keep this small and evidence-driven. The goal is to learn whether visible
Markdown review markup belongs in `makedoc`, and if so what the next production
goal should be.

## Steps

1. Capture starting state.
   - Record `pwd`, branch/status, and HEAD in `Log.md`.
   - Note the pre-existing `.DS_Store`.

2. Inspect the current source-preparation path.
   - Review `scripts/prepare_markdown_sources.py`.
   - Review adjacent tests in `tests/test_prepare_markdown_sources.py`.
   - Identify whether review markup should be transformed before or during
     source preparation.

3. Design the smallest experimental syntax path.
   - Start from CriticMarkup-like additions, deletions, substitutions, and
     optional reviewer notes.
   - Keep normal manuscript behavior unchanged unless explicitly enabled.
   - Avoid new dependencies unless absolutely necessary.

4. Implement the minimal transform if feasible.
   - Prefer a small, testable function.
   - Preserve code fences, inline code, citation tokens, figure markdown, and
     raw blocks.
   - Keep the output legible in both DOCX and PDF.

5. Add focused evidence.
   - Add unit or shell coverage for the transform.
   - Add the smallest fixture/source example needed to render evidence.
   - Avoid committing generated DOCX/PDF outputs unless repo policy already
     tracks that type of artifact.

6. Validate sequentially.
   - Run targeted review-markup checks first.
   - Run the required Makedoc validation ladder from `Goal.md`.
   - Stop and report if validation exposes a blocker.

7. Write the decision memo.
   - Summarize what was tried.
   - Show the proposed syntax and rendered behavior.
   - Explain limitations.
   - Recommend the next goal or recommend stopping.

8. Wake the orchestrator.
   - Send a short completion or blocked message back to the Makedoc thread.
   - Do not start a second goal.

## Expected Outcome

The expected best outcome is a minimal, default-off review-markup path that
renders visibly in generated DOCX/PDF and has enough tests to justify a
production-hardening follow-up.

The acceptable alternative outcome is a clear no-go memo with evidence.
