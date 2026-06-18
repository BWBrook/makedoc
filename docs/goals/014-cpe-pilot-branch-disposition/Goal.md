# Goal: CPE Pilot Branch Disposition and Cleanup

## Objective

Retire the local CPE review-markup/import pilot branch and worktree state now
that the Makedoc evidence has been published.

This is housekeeping, not importer development.

## Scope

Primary record repo:

```text
/Users/bwbrook/work/makedoc
```

External repo allowed only for this goal:

```text
/Users/bwbrook/papers/cpe_time_to_extinction
```

## Required Guard

Before cleanup, confirm:

- Makedoc is clean on `main...origin/main` at `efb07e0` or a direct
  descendant.
- CPE is on local branch `codex/makedoc-review-markup-pilot` at `e1b2433`.
- CPE dirty state is exactly:
  - modified `settings/build.yaml`;
  - untracked `manuscript/text/main_review_markup_probe.md`.
- Local `main` and `codex/makedoc-review-markup-pilot` have no unique commits
  relative to one another.

If any guard differs, stop before cleanup.

## Authorized Cleanup

If the guard matches:

1. Restore only CPE `settings/build.yaml` to the local branch state.
2. Remove only CPE `manuscript/text/main_review_markup_probe.md`.
3. Remove only ignored CPE `build/review-markup-pilot/` outputs if present.
4. Confirm CPE is clean.
5. Switch CPE to local `main`.
6. Delete local CPE branch `codex/makedoc-review-markup-pilot` only with
   normal non-force branch deletion.

## Makedoc Record

Create this goal packet and add a short prose-free disposition note to:

```text
docs/docx_review_import_cpe_preflight_audit.md
```

Record statuses, commit IDs, branch names, paths, and decisions only. Do not
copy CPE manuscript prose, headings, citations, paragraph text, figure
captions, or review probe text.

## Non-Goals

- Importer development or support broadening.
- Makedoc engine, test, schema, Makefile, or behavior changes.
- CPE staging, commits, pushes, fetches, pulls, resets, cleans, stashes,
  rebases, force deletes, force pushes, builds, or artifact regeneration.
- Makedoc staging, commits, or pushes.
- Dependency installs.
- Goal 015.

## Acceptance Criteria

- CPE ends clean on local `main` at `e1b2433`.
- CPE local pilot branch is deleted by normal non-force deletion.
- CPE pilot source file is absent.
- CPE ignored pilot output directory is absent if it existed.
- Makedoc docs record the disposition without CPE manuscript prose.
- `git diff --check` passes in Makedoc.
