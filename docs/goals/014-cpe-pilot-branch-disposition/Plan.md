# Plan: CPE Pilot Branch Disposition

1. Read makedoc `AGENTS.md` and confirm makedoc status/HEAD.
2. Read CPE `AGENTS.md` before any CPE operation.
3. Confirm CPE branch, HEAD, dirty state, and local branch relationship.
4. If the guard matches, perform only the authorized cleanup:
   - restore CPE `settings/build.yaml`;
   - remove CPE `manuscript/text/main_review_markup_probe.md`;
   - remove CPE `build/review-markup-pilot/` if present;
   - switch to CPE `main`;
   - delete the local pilot branch with normal `git branch -d`.
5. Add the Makedoc disposition note and Goal 014 packet.
6. Run Makedoc `git diff --check`.
7. Confirm final makedoc and CPE statuses.
8. Wake the Makedoc orchestrator and stop.
