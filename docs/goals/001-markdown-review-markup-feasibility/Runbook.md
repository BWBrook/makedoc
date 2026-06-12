# Runbook: Markdown Review Markup Feasibility Spike

## Starting Commands

Run from `/Users/bwbrook/work/makedoc`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
git log -5 --oneline
```

Record the results in `Log.md`.

## Read-First Checklist

Read:

```text
AGENTS.md
README.md
docs/plan.md
docs/builder_notes.md
docs/makedoc_primer_for_agents.md
scripts/prepare_markdown_sources.py
tests/test_prepare_markdown_sources.py
Makefile
```

## Implementation Notes

- Keep the transform isolated and easy to test.
- Do not transform review markup inside fenced code blocks, raw blocks, or
  inline code spans.
- Watch for interactions with citations, references, figure extraction, and
  author metadata.
- Prefer ordinary Pandoc-compatible Markdown output over DOCX-specific hacks.
- Treat true Word Track Changes and DOCX-to-Markdown import as future work.

## Suggested Validation Ladder

Run only after the relevant implementation or no-go evidence exists:

```sh
make test-author-injection
make test-figure-modes
make check
make check-fixture
```

Add and run any targeted review-markup test before the broader ladder.

Do not run top-level Make targets in parallel.

## Wake-Up Requirement

When done or blocked, send the Makedoc orchestrator
(`019eaf80-3882-7d31-b6a4-3cb4c2ab5699`) a short wake-up using thread tools.
Include:

- completion or blocked status;
- changed files;
- validation result;
- memo path;
- final git status;
- recommended next step.

Do not begin follow-up work after sending the wake-up.
