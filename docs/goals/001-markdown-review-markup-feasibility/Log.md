# Log: Markdown Review Markup Feasibility Spike

## 2026-06-12 - Goal Packet Created

Status: ready for `draftsman`.

Makedoc orchestrator created this packet after Barry approved a feasibility
spike for visible Markdown review markup. The immediate target is redline-style
traceability in generated DOCX/PDF outputs. True Word Track Changes semantics
and DOCX-to-Markdown import are explicitly future context, not part of Goal
001.

Starting state expected before `draftsman` begins:

```text
## main...origin/main
?? .DS_Store
```

Expected HEAD:

```text
ed849d3 Fix macOS bootstrap portability
```

No implementation work has started in this log.

## 2026-06-12 - Starting State Captured

Status: in progress.

Starting commands were run from `/Users/bwbrook/work/makedoc`.

```text
pwd
/Users/bwbrook/work/makedoc
```

```text
git status --short --branch
## main...origin/main
?? .DS_Store
?? docs/goals/
```

The additional untracked `docs/goals/` entry is this Goal 001 packet. The
pre-existing `.DS_Store` remains untracked and will be preserved.

```text
git rev-parse --short HEAD
ed849d3
```

```text
git log -5 --oneline
ed849d3 Fix macOS bootstrap portability
62ec7a0 agent: fix(lint): ignore pandoc citekeys in manual-cite scan
096de00 Harden path handling and rebuild checks
4d5e652 Enable YAML metadata in markdown input
33dc434 Fix external output dir resolution
```

Read-first packet and repo files reviewed before implementation:

- `Goal.md`, `Plan.md`, `Runbook.md`, `Log.md`
- `AGENTS.md`
- `README.md`
- `docs/plan.md`
- `docs/builder_notes.md`
- `docs/makedoc_primer_for_agents.md`
- `scripts/prepare_markdown_sources.py`
- `tests/test_prepare_markdown_sources.py`
- `Makefile`

## 2026-06-12 - Experimental Path Implemented

Status: validation complete.

Implemented a default-off `review_markup.enabled` profile option. When enabled,
`scripts/prepare_markdown_sources.py` converts small CriticMarkup-like tokens
into plain Pandoc-visible Markdown:

- `{++ added text ++}` -> bold `[+ added text +]`
- `{-- deleted text --}` -> stricken `[- deleted text -]`
- `{~~ old text ~> new text ~~}` -> stricken old text plus bold new text
- `{>> note <<}` -> bold reviewer note

The transform runs after figure extraction, skips fenced code blocks and inline
code spans, and leaves ordinary/default profiles unchanged unless the profile
explicitly enables review markup.

Added focused evidence:

- `settings/review_markup.yaml`
- `testbed/manuscript/text/review_markup_probe.md`
- `docs/markdown_review_markup_spike.md`

Rendered evidence was generated under ignored output/cache paths:

- `dist/review-markup/review_markup_probe.pdf`
- `dist/review-markup/review_markup_probe.docx`
- `dist/review-markup/review_markup_probe_build_manifest.json`
- `.cache/active_sources.bde80a89959edefa.md`

Evidence inspection:

- prepared Markdown contains bold addition/note markers and strikeout deletion
  markers;
- `pdftotext dist/review-markup/review_markup_probe.pdf -` shows the bracketed
  review traces in the PDF text;
- `unzip -p dist/review-markup/review_markup_probe.docx word/document.xml`
  shows bold runs for additions/notes and `w:strike` runs for deletions.

Validation commands run sequentially:

```text
python3 -m py_compile scripts/prepare_markdown_sources.py scripts/build_profile.py scripts/validate_build_config.py scripts/profile_schema.py
```

Result: passed.

```text
python3 -m unittest tests/test_prepare_markdown_sources.py tests/test_build_profile.py tests/test_validate_build_config.py
```

Result: passed, 22 tests.

```text
CONFIG=settings/review_markup.yaml make validate-config
```

Result: passed for `review_markup` and `fixture`.

```text
CONFIG=settings/review_markup.yaml make all
```

Result: passed; generated PDF, DOCX, and manifest evidence under
`dist/review-markup/`.

```text
make test-author-injection
```

Result: passed.

```text
make test-figure-modes
```

Result: passed.

```text
make check
```

Result: passed; included 35 Python tests, lint, reference audit, author
injection check, build, and manifest generation.

```text
make check-fixture
```

Result: passed; included fixture lint, reference audit, figure-mode check,
author injection check, fixture build, and fixture contract checks.

Recommendation: proceed with a production-hardening follow-up that formalizes
docs and decides whether bold/strike/bracket markers are sufficient or whether
custom DOCX/PDF styling is needed. Keep true Word Track Changes and
DOCX-to-Markdown import out of that next goal.

## 2026-06-12 - Final Local Status

Status: complete pending orchestrator review.

`git diff --check` passed with no whitespace errors.

Final `git status --short --branch`:

```text
## main...origin/main
 M scripts/build_profile.py
 M scripts/prepare_markdown_sources.py
 M scripts/profile_schema.py
 M scripts/validate_build_config.py
 M tests/test_build_profile.py
 M tests/test_prepare_markdown_sources.py
 M tests/test_validate_build_config.py
?? .DS_Store
?? docs/goals/
?? docs/markdown_review_markup_spike.md
?? settings/review_markup.yaml
?? testbed/manuscript/text/review_markup_probe.md
```

No files were staged. `.DS_Store` remains preserved and unstaged. No fetch,
pull, push, commit, reset, clean, stash, or discard command was run.
