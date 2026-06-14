# Markdown Review Markup Feasibility Spike

Date: 2026-06-12

Status note, 2026-06-14: Goal 004 replaced strikeout deletion rendering with
bold bracketed deletion markers because rendered PDF strikeout made deleted
words difficult to read by eye. The source token syntax remains unchanged.

## Decision

Human-editable Markdown review markup is feasible as an experimental `makedoc`
source-preparation step for visibly traceable DOCX/PDF output.

The recommended next step is a production-hardening goal, not a workflow
redesign. The route works well enough to keep source of truth in Markdown and
show visible additions, deletions, substitutions, and reviewer notes in
generated outputs. It should remain clearly separate from true Microsoft Word
Track Changes and DOCX-to-Markdown import.

## What Was Implemented

The spike adds a default-off profile option:

```yaml
review_markup:
  enabled: true
```

When enabled, `scripts/prepare_markdown_sources.py` converts a small
CriticMarkup-like syntax into ordinary Pandoc Markdown:

| Source syntax | Prepared Markdown output |
| --- | --- |
| `{++ added text ++}` | `**[+ added text +]**` |
| `{-- deleted text --}` | `**[- deleted text -]**` |
| `{~~ old text ~> new text ~~}` | `**[- old text -]** **[+ new text +]**` |
| `{>> reviewer note <<}` | `**[Reviewer note: reviewer note]**` |

The transform runs after figure extraction, skips fenced code blocks and inline
code spans, and is disabled for ordinary profiles unless explicitly enabled.

## Evidence

Fixture/config added for the spike:

- `settings/review_markup.yaml`
- `testbed/manuscript/text/review_markup_probe.md`

Rendered evidence generated locally:

- `dist/review-markup/review_markup_probe.pdf`
- `dist/review-markup/review_markup_probe.docx`
- `dist/review-markup/review_markup_probe_build_manifest.json`
- prepared source: `.cache/active_sources.bde80a89959edefa.md`

Observed prepared Markdown includes:

```markdown
**[+ inserted review text +]**
**[- removed review text -]**
**[- outdated wording -]** **[+ revised wording +]**
**[Reviewer note: reviewer asks for a clearer transition]**
```

PDF text extraction showed the bracketed review traces in the rendered PDF.
DOCX XML showed bold runs for additions, deletions, substitution sides, and
reviewer notes.

## Validation

All commands were run sequentially from `/Users/bwbrook/work/makedoc`.

```text
python3 -m py_compile scripts/prepare_markdown_sources.py scripts/build_profile.py scripts/validate_build_config.py scripts/profile_schema.py
```

Passed.

```text
python3 -m unittest tests/test_prepare_markdown_sources.py tests/test_build_profile.py tests/test_validate_build_config.py
```

Passed: 22 tests.

```text
CONFIG=settings/review_markup.yaml make validate-config
```

Passed for `review_markup` and `fixture`.

```text
CONFIG=settings/review_markup.yaml make all
```

Passed and generated the review-markup PDF/DOCX/manifest evidence.

```text
make test-author-injection
make test-figure-modes
make check
make check-fixture
```

All passed. `make check` ran 35 Python tests; `make check-fixture` completed
fixture lint, reference audit, build, and contract checks.

## Limitations

- This is visible review markup, not true Word Track Changes.
- It does not create entries in Word's Review pane.
- It does not import DOCX edits back into Markdown.
- The current transform is line-local and intentionally simple; markup tokens
  should stay on one source line.
- The rendering uses robust Pandoc Markdown styling rather than red/green
  colour. A production goal should decide whether to add reference DOCX/LaTeX
  styling for stronger redline-like appearance.
- Nested review markup is not supported.

## Recommendation

Proceed with a follow-up production-hardening goal:

1. Formalize the `review_markup` profile schema and docs.
2. Decide whether bold bracketed markers are sufficient or whether custom
   DOCX/PDF styling should be added.
3. Add a first-class Make target for the review-markup rendering probe if the
   feature will remain in the regression suite.
4. Expand parser tests only as far as the agreed authoring contract requires.

Do not pursue true Word Track Changes or DOCX-to-Markdown import in the next
goal; keep those as separate future investigations.
