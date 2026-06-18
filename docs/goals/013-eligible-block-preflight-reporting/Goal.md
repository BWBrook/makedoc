# Goal: Eligible-Block Reporting for Structured DOCX Import Preflight

## Objective

Extend structured DOCX-import preflight JSON so it reports prose-free metadata
for eligible simple-prose blocks, then rerun the read-only CPE structured audit
to show how eligible ranges can support future controlled excerpt selection.

This is a reporting and workflow-safety goal. It is not a goal to broaden
importer support.

## Context

Goal 012 showed that the canonical CPE source remains correctly refused for
whole-file `revised-candidate` import:

```text
status: REFUSED
total_blocks: 48
eligible_blocks: 23
refused_blocks: 25
unsupported Markdown heading: 17
unsupported Markdown Pandoc citation: 8
```

The product gap was that JSON reported refusal objects but did not report
equivalent eligible block references.

## Scope

Authorized implementation repo:

```text
/Users/bwbrook/work/makedoc
```

Authorized read-only proving-ground repo:

```text
/Users/bwbrook/papers/cpe_time_to_extinction
```

Temporary evidence location:

```text
/tmp/makedoc-goal013-eligible-blocks/
```

## Required Work

1. Confirm makedoc is clean on `main...origin/main` at `cd47925`.
2. Read makedoc `AGENTS.md` before work.
3. Read CPE `AGENTS.md` before CPE inspection.
4. Confirm CPE is on preserved branch `codex/makedoc-review-markup-pilot`
   at `e1b2433` with only the expected pilot changes.
5. Add a stable prose-free eligible block array to preflight JSON.
6. Add focused tests proving eligible refs are present and do not leak source
   prose.
7. Rerun structured preflight against canonical CPE source and store raw and
   derived evidence only under `/tmp/makedoc-goal013-eligible-blocks/`.
8. Update durable docs and this goal log with counts, refs, validation, and
   product recommendation.
9. Leave all changes unstaged and wake the orchestrator.

## Non-Goals

- Importer support broadening.
- Support for citations, headings, lists, tables, figures, comments,
  references, front matter/thematic breaks, raw HTML, code blocks, native Word
  Track Changes, formatting-only changes, moves, or full round-tripping.
- CPE edits, builds, artifact regeneration, git mutations, cleanup, or branch
  disposition execution.
- Staging, commits, pushes, fetches, pulls, resets, cleans, stashes, rebases,
  branch switches, dependency installs, or generated artifact force-adds.
- Chief of Staff, Goal Composer, sibling repo, archive, unrelated-file, or
  broader CPE reads.
- Goal 014.

## Acceptance Criteria

- JSON output includes `eligible_blocks_detail` objects with `block`,
  `start_line`, and `end_line`.
- Existing top-level counts and `refusals` objects are preserved.
- JSON and text preflight behavior remains prose-free by default.
- Existing `revised`, `track-changes`, and `revised-candidate` tests still pass.
- CPE audit records eligible/refused counts and summarized eligible refs
  without copying CPE prose into tracked docs.
- CPE and unrelated repos remain unmodified.
