# Log: Review Markup Production Hardening

## 2026-06-13 - Goal Packet Created

Status: ready for `draftsman`.

Makedoc orchestrator created this packet after Barry approved production
hardening for the Goal 001 review-markup feature. The intent is to keep the
feature experimental and default-off while making it documented, testable, and
safe for cautious use by external manuscript repositories.

Baseline before this packet was written:

```text
pwd
/Users/bwbrook/work/makedoc
```

```text
git status --short --branch
## main...origin/main
```

```text
git rev-parse --short HEAD
42802b5
```

```text
git log -1 --oneline
42802b5 Add markdown review markup feasibility spike
```

This Goal 002 packet is orchestrator-authorized untracked state. No
implementation work has started in this log.

Publication boundary: `draftsman` should not stage, commit, push, fetch, pull,
reset, clean, stash, or publish during the implementation pass. Changes should
remain unstaged for orchestrator review.

## 2026-06-13 - Starting State Captured

Status: in progress.

Starting commands were run from `/Users/bwbrook/work/makedoc`.

```text
pwd
/Users/bwbrook/work/makedoc
```

```text
git status --short --branch
## main...origin/main
?? docs/goals/002-review-markup-production-hardening/
```

The only untracked state is the orchestrator-authorized Goal 002 packet.

```text
git rev-parse --short HEAD
42802b5
```

```text
git log -5 --oneline
42802b5 Add markdown review markup feasibility spike
ed849d3 Fix macOS bootstrap portability
62ec7a0 agent: fix(lint): ignore pandoc citekeys in manual-cite scan
096de00 Harden path handling and rebuild checks
4d5e652 Enable YAML metadata in markdown input
```

Required read-first files reviewed before implementation:

- `AGENTS.md`
- `README.md`
- `docs/makedoc_primer_for_agents.md`
- `docs/markdown_review_markup_spike.md`
- `docs/goals/001-markdown-review-markup-feasibility/Goal.md`
- `docs/goals/001-markdown-review-markup-feasibility/Log.md`
- `settings/review_markup.yaml`
- `testbed/manuscript/text/review_markup_probe.md`
- `scripts/prepare_markdown_sources.py`
- `scripts/build_profile.py`
- `scripts/profile_schema.py`
- `scripts/validate_build_config.py`
- `tests/test_prepare_markdown_sources.py`
- `tests/test_build_profile.py`
- `tests/test_validate_build_config.py`
- `Makefile`

Hardening posture:

- keep `review_markup.enabled` experimental and default-off;
- keep the Goal 001 bold/bracket/strike rendering as the
  production-experimental style for now because it is plain Pandoc Markdown and
  works in both DOCX and PDF without new dependencies;
- add a first-class `make test-review-markup` regression target;
- document true Word Track Changes and DOCX-to-Markdown import as out of scope;
- narrowly harden hidden-content behavior by ensuring HTML comment blocks are
  not transformed.

## 2026-06-13 - Hardening Implemented

Status: validation complete.

Changed the review-markup route from spike-only to first-class experimental:

- documented `review_markup.enabled` in `README.md`;
- documented the external-agent authoring contract in
  `docs/makedoc_primer_for_agents.md`;
- added `make test-review-markup`;
- added `scripts/test_review_markup.sh` as the focused regression script;
- added source-prep protection for HTML comment blocks as hidden Markdown
  content;
- added unit coverage for HTML comment protection and the line-local contract.

Styling policy decision: keep the Goal 001 bold/bracket/strike rendering for
now. It is portable plain Pandoc Markdown, creates visible traces in DOCX and
PDF, and avoids dependencies or Word-specific XML. True Word Track Changes,
Review-pane data, and DOCX-to-Markdown import remain out of scope.

`make test-review-markup` checks:

- `tests/test_prepare_markdown_sources.py`;
- `CONFIG=settings/review_markup.yaml make validate-config`;
- prepared Markdown output from `scripts/prepare_markdown_sources.py`;
- transformed addition, deletion, substitution, and reviewer-note traces;
- inline-code and fenced-code literal protections;
- regenerated proof DOCX/PDF outputs through
  `CONFIG=settings/review_markup.yaml make -B all`;
- PDF text markers via `pdftotext`;
- DOCX XML markers and strikeout styling via `unzip -p`.

Generated proof artifacts were created under ignored output paths:

- `dist/review-markup/review_markup_probe_build_manifest.json`
- `dist/review-markup/review_markup_probe.pdf`
- `dist/review-markup/review_markup_probe.docx`

Validation commands run sequentially:

```text
python3 -m unittest tests/test_prepare_markdown_sources.py
```

Result: passed, 12 tests.

```text
make test-review-markup
```

Result: passed; regenerated review-markup proof artifacts and inspected
prepared Markdown, PDF text, and DOCX XML.

```text
CONFIG=settings/review_markup.yaml make validate-config
```

Result: passed for `review_markup` and `fixture`.

```text
CONFIG=settings/review_markup.yaml make -B all
```

Result: passed; regenerated review-markup PDF, DOCX, and manifest.

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

Result: passed; included 37 Python tests, lint, reference audit, author
injection check, build, and manifest generation.

```text
make check-fixture
```

Result: passed; included fixture lint, reference audit, figure-mode check,
author injection check, fixture build, and fixture contract checks.

```text
git diff --check
```

Result: passed.

Final `git status --short --branch`:

```text
## main...origin/main
 M Makefile
 M README.md
 M docs/makedoc_primer_for_agents.md
 M scripts/prepare_markdown_sources.py
 M tests/test_prepare_markdown_sources.py
?? docs/goals/002-review-markup-production-hardening/
?? scripts/test_review_markup.sh
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, dependency installs, external-repo reads, Chief/Goal Composer reads,
or force-added generated artifacts were performed.

Remaining risks:

- Review markup is still line-local and intentionally non-nesting.
- Styling remains visible but conservative; no red/green custom styling or Word
  Review-pane semantics are provided.

Recommended next step: orchestrator review and, if accepted, a publication
closeout. Do not start Goal 003 from this implementation thread.
