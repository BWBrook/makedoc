# Goal: DOCX Review Import Feasibility

## Objective

Determine whether edits made in a DOCX can be converted back into a Markdown
revision with traceable Makedoc review-markup tokens.

This is a feasibility spike, not a production importer. The required outcome is
a clear technical recommendation with small runnable evidence.

## Strategic Framing

Outbound Markdown review markup is credible after Goals 001-005. The
uncertainty is inbound:

1. Can a revised DOCX be converted back into source-adjacent Markdown review
   tokens by comparing original text with DOCX-derived revised text?
2. Can native Word Track Changes OOXML be read directly and converted into
   Makedoc review tokens?

Treat the routes separately and do not change outbound rendering semantics.

## Scope

Authorized path:

- `/Users/bwbrook/work/makedoc`

Forbidden:

- `/Users/bwbrook/papers/cpe_time_to_extinction`
- Chief of Staff
- Goal Composer
- sibling project repos
- archive material
- unrelated user files

Out of scope:

- production importer;
- CPE access or mutation;
- native Word automation or GUI Word control;
- dependency installation;
- network or remote services;
- full layout preservation;
- tables, references, figures, comments, moves, formatting-only changes, or
  other complex Word structures beyond noting them as limitations;
- changes to `review_markup.enabled`, outbound rendering, profile schema,
  Make build graph, external adoption semantics, or manuscript workflows;
- Goal 007.

## Required Work

1. Confirm makedoc starts clean at `d912acd` on `main...origin/main`.
2. Read required context:
   - `AGENTS.md`
   - `README.md`
   - `docs/review_markup_external_adoption.md`
   - `docs/markdown_review_markup_spike.md`
   - `scripts/prepare_markdown_sources.py`
   - `tests/test_prepare_markdown_sources.py`
   - recent Goal 004 and Goal 005 packets/logs enough to preserve boundaries.
3. Add a decision memo, preferably `docs/docx_review_import_spike.md`.
4. If feasible, add an explicitly experimental prototype under `scripts/`.
5. If a prototype is added, add focused tests under `tests/` using tiny
   generated synthetic fixtures.
6. Create this Goal 006 packet with `Goal.md`, `Plan.md`, `Runbook.md`, and
   `Log.md`.
7. Validate with the focused script/test commands, `make test-review-markup`,
   and `git diff --check`.
8. Leave changes unstaged and wake the orchestrator.

## Acceptance Criteria

- The decision memo gives a clear recommendation.
- At least one route has runnable evidence, or both are precisely blocked.
- If code is added, focused tests cover supported narrow behavior and current
  review-token output.
- Existing outbound review-markup behavior is unchanged.
- CPE and unrelated repos are untouched.
- The log records start state, design choice, validation evidence,
  limitations, and final status.
