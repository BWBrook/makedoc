# Log: PDF Review Markup Legibility Hardening

## 2026-06-14 - Goal Packet Created

Status: ready for `draftsman`.

Makedoc orchestrator created this packet after Goal 003 showed that the
external CPE review-markup pilot was mechanically successful but PDF
deletion/old-wording strikeout was not visually legible enough.

`makedoc` baseline before this packet was written:

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
6d134c6
```

```text
git log -1 --oneline
6d134c6 Record CPE review markup pilot
```

CPE pilot state before this packet was written:

```text
pwd
/Users/bwbrook/papers/cpe_time_to_extinction
```

```text
git status --short --branch
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

```text
git rev-parse --short HEAD
e1b2433
```

The CPE state is expected carryover from Goal 003 and should be preserved.

No implementation work has started in this log.

## 2026-06-14 - Execution Started

Executor: `draftsman`.

Starting state confirmed in `/Users/bwbrook/work/makedoc`:

```text
git status --short --branch
## main...origin/main
?? docs/goals/004-pdf-review-markup-legibility-hardening/
```

```text
git rev-parse --short HEAD
6d134c6
```

Starting state confirmed in `/Users/bwbrook/papers/cpe_time_to_extinction`:

```text
git status --short --branch
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

```text
git rev-parse --short HEAD
e1b2433
```

The preserved CPE Goal 003 pilot state matched expectations. CPE is being used
as evidence-only; no CPE source edits, staging, commits, pushes, fetches,
pulls, resets, cleans, stashes, rebases, or branch switches were performed.

Required read-first files were reviewed before implementation:

- `AGENTS.md`
- `README.md`
- `docs/makedoc_primer_for_agents.md`
- `docs/markdown_review_markup_spike.md`
- `docs/goals/002-review-markup-production-hardening/Goal.md`
- `docs/goals/002-review-markup-production-hardening/Log.md`
- `docs/goals/003-cpe-review-markup-pilot/Goal.md`
- `docs/goals/003-cpe-review-markup-pilot/Log.md`
- `scripts/prepare_markdown_sources.py`
- `scripts/test_review_markup.sh`
- `tests/test_prepare_markdown_sources.py`
- `settings/review_markup.yaml`
- `testbed/manuscript/text/review_markup_probe.md`
- `Makefile`

In CPE, repo-local `AGENTS.md` was read first, followed only by the authorized
evidence files `settings/build.yaml` and
`manuscript/text/main_review_markup_probe.md`.

## 2026-06-14 - Rendering Policy Hardened

Status: validation complete.

Problem reproduced before implementation by rebuilding the existing CPE pilot
and rendering PDF page 2:

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make -B all
pdftoppm -f 2 -l 2 -png -r 240 \
  /Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf \
  /tmp/makedoc-goal004-review/before-cpe-pilot-page
```

Before image:

```text
/tmp/makedoc-goal004-review/before-cpe-pilot-page-02.png
```

Visual finding before change: additions and reviewer notes were readable, but
deleted and old wording appeared mostly as strike lines. The underlying text
was present in extraction/XML, but the rendered PDF page did not meet the
human-readability acceptance bar.

Likely cause: the current pipeline prepares one Markdown source for both PDF
and DOCX, and Pandoc/PDF strikeout rendering can visually obscure short
deleted phrases at normal manuscript scale. DOCX strikeout remained usable,
but preserving DOCX strikeout would require format-aware source preparation or
another build-graph split. That would be broader than needed for this goal.

Chosen rendering policy: use one portable plain-Markdown policy for both PDF
and DOCX:

- additions: bold `[+ added text +]`
- deletions: bold `[- deleted text -]`
- substitutions: bold `[- old text -]` followed by bold `[+ new text +]`
- reviewer notes: bold `[Reviewer note: note text]`

Deletion and old-wording traces intentionally no longer rely on strikeout.
This keeps the feature default-off, keeps source token syntax unchanged, avoids
new dependencies, and makes generated PDFs readable by eye.

Changed makedoc files:

- `scripts/prepare_markdown_sources.py`
- `tests/test_prepare_markdown_sources.py`
- `scripts/test_review_markup.sh`
- `README.md`
- `docs/makedoc_primer_for_agents.md`
- `docs/markdown_review_markup_spike.md`
- `docs/goals/004-pdf-review-markup-legibility-hardening/Log.md`

Implementation notes:

- `apply_review_markup(..., enabled=True)` now emits bold bracketed deletion
  markers instead of strikethrough deletion markers.
- Unit tests pin the new prepared Markdown contract.
- `make test-review-markup` now requires the no-strike deletion policy in
  prepared Markdown, generated PDF text, and DOCX XML.
- DOCX XML checks require review traces to be present and require no
  `<w:strike` or `<ns0:strike` styling for the review-markup proof.
- The shell check was made tolerant of `pdftotext` line wrapping for reviewer
  notes by checking the reviewer-note label and text separately.
- README and the external-agent primer now describe readable bracketed
  deletion markers rather than strikeout deletion.
- The Goal 001 spike memo now has a status note recording that Goal 004
  superseded strikeout deletion rendering.

Generated fixture proof artifacts:

```text
/Users/bwbrook/work/makedoc/dist/review-markup/review_markup_probe.pdf
/Users/bwbrook/work/makedoc/dist/review-markup/review_markup_probe.docx
/Users/bwbrook/work/makedoc/dist/review-markup/review_markup_probe_build_manifest.json
```

Generated CPE pilot proof artifacts:

```text
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.docx
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot_build_manifest.json
```

Supporting inspection artifacts:

```text
/tmp/makedoc-goal004-review/fixture_prepared_after.md
/tmp/makedoc-goal004-review/fixture_pdf_after.txt
/tmp/makedoc-goal004-review/fixture_docx_after.xml
/tmp/makedoc-goal004-review/cpe_prepared_after.md
/tmp/makedoc-goal004-review/cpe_pdf_after.txt
/tmp/makedoc-goal004-review/cpe_docx_after.xml
```

Rendered PDF page-image evidence after change:

```text
/tmp/makedoc-goal004-review/after-cpe-pilot-page-02.png
```

Visual conclusion after change: the CPE rendered PDF page now shows
`[- removed pilot text -]` and `[- old pilot wording -]` as readable bold
bracketed text by eye. Additions and reviewer notes remain readable.

Artifact inspection summary:

```text
/tmp/makedoc-goal004-review/fixture_prepared_after.md
**[- removed review text -]**
**[- outdated wording -]** **[+ revised wording +]**
```

```text
/tmp/makedoc-goal004-review/fixture_pdf_after.txt
[- removed review text -]
[- outdated wording -] [+ revised wording +]
[Reviewer note:
```

```text
/tmp/makedoc-goal004-review/fixture_docx_after.xml
[- removed review text -]
[- outdated wording -]
[+ revised wording +]
[Reviewer note: reviewer asks for a clearer transition]
```

`rg -n "w:strike|ns0:strike" /tmp/makedoc-goal004-review/fixture_docx_after.xml`
returned no matches.

```text
/tmp/makedoc-goal004-review/cpe_prepared_after.md
**[- removed pilot text -]**
**[- old pilot wording -]** **[+ revised pilot wording +]**
```

```text
/tmp/makedoc-goal004-review/cpe_pdf_after.txt
[- removed pilot text -]
[- old pilot wording -] [+ revised pilot wording +]
[Reviewer note: confirm visible review trace
```

```text
/tmp/makedoc-goal004-review/cpe_docx_after.xml
[- removed pilot text -]
[- old pilot wording -]
[+ revised pilot wording +]
[Reviewer note: confirm visible review trace output]
```

`rg -n "w:strike|ns0:strike" /tmp/makedoc-goal004-review/cpe_docx_after.xml`
returned no matches.

Validation commands run sequentially from `/Users/bwbrook/work/makedoc`:

```text
python3 -m unittest tests/test_prepare_markdown_sources.py
```

Result: passed, 12 tests.

```text
make test-review-markup
```

Result: passed. The first post-edit run exposed that `pdftotext` may wrap the
reviewer-note label and text across lines; `scripts/test_review_markup.sh` was
updated to check those pieces separately, and the final run passed.

```text
CONFIG=settings/review_markup.yaml make validate-config
```

Result: passed for `review_markup` and `fixture`.

```text
CONFIG=settings/review_markup.yaml make -B all
```

Result: passed; regenerated fixture review-markup PDF, DOCX, and manifest.

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make validate-config
```

Result: passed for `review_markup_pilot` and `fixture`.

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make -B all
```

Result: passed; regenerated CPE pilot PDF, DOCX, and manifest under ignored
CPE `build/` paths.

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
injection, default build, and manifest generation.

```text
make check-fixture
```

Result: passed; included fixture lint, reference audit, figure-mode check,
author injection, fixture build, and fixture contract checks.

```text
git diff --check
```

Result: passed.

CPE canonical source cleanliness:

```text
rg '\{\+\+|\{--|\{~~|\{>>' manuscript/text/main.md
```

Result: no matches, which is the desired result.

Final makedoc status:

```text
## main...origin/main
 M README.md
 M docs/makedoc_primer_for_agents.md
 M docs/markdown_review_markup_spike.md
 M scripts/prepare_markdown_sources.py
 M scripts/test_review_markup.sh
 M tests/test_prepare_markdown_sources.py
?? docs/goals/004-pdf-review-markup-legibility-hardening/
```

Final CPE status:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

Final CPE HEAD:

```text
e1b2433
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, rebases, dependency installs, generated artifact force-adds, native
Word Track Changes work, DOCX-to-Markdown import work, CPE source edits, or
Goal 005 work were performed.

Remaining risks:

- DOCX no longer uses strikeout for deletions; instead it uses the same bold
  bracketed deletion markers as PDF. This is less redline-like than DOCX
  strikeout but remains visibly traceable and avoids a format-specific build
  split.
- The review-markup parser remains intentionally line-local and non-nesting.
- The rendering remains black/plain Markdown rather than colour-styled.

Recommended next step: orchestrator review of the compact engine/docs/test
diff and the rendered CPE PDF page image. If accepted, proceed to bounded
publication closeout for Goal 004. Do not start wider manuscript adoption from
this implementation pass.
