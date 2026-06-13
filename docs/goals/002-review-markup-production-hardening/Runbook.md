# Runbook: Review Markup Production Hardening

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
docs/makedoc_primer_for_agents.md
docs/markdown_review_markup_spike.md
docs/goals/001-markdown-review-markup-feasibility/Goal.md
docs/goals/001-markdown-review-markup-feasibility/Log.md
settings/review_markup.yaml
testbed/manuscript/text/review_markup_probe.md
scripts/prepare_markdown_sources.py
scripts/build_profile.py
scripts/profile_schema.py
scripts/validate_build_config.py
tests/test_prepare_markdown_sources.py
tests/test_build_profile.py
tests/test_validate_build_config.py
Makefile
```

## Implementation Notes

- Keep `review_markup.enabled` disabled by default.
- Preserve ordinary manuscript output for profiles that omit `review_markup`.
- Do not support nested or multiline review-markup tokens in this goal.
- Do not transform review-markup-looking text inside inline code, fenced code
  blocks, hidden/raw blocks, or figure image lines.
- Prefer plain Pandoc Markdown output over DOCX-specific hacks.
- Keep true Word Track Changes and DOCX-to-Markdown import out of scope.
- If styling changes, verify both DOCX and PDF behavior and keep the change
  small enough to remain portable.

## Suggested Focused Target Shape

Preferred target:

```sh
make test-review-markup
```

Preferred script path if a script is useful:

```text
scripts/test_review_markup.sh
```

Suggested checks for that target:

```sh
CONFIG=settings/review_markup.yaml make validate-config
python3 scripts/prepare_markdown_sources.py \
  --config settings/review_markup.yaml \
  --output <temporary-prepared-markdown>
CONFIG=settings/review_markup.yaml make -B all
pdftotext dist/review-markup/review_markup_probe.pdf -
unzip -p dist/review-markup/review_markup_probe.docx word/document.xml
```

Use temporary files where practical. Do not force-add generated files.

## Validation Ladder

Run sequentially:

```sh
python3 -m unittest tests/test_prepare_markdown_sources.py tests/test_build_profile.py tests/test_validate_build_config.py
make test-review-markup
CONFIG=settings/review_markup.yaml make validate-config
CONFIG=settings/review_markup.yaml make -B all
make test-author-injection
make test-figure-modes
make check
make check-fixture
git diff --check
```

If you do not add `make test-review-markup`, replace that command with the
focused review-markup validation you did choose and explain the decision in
`Log.md`.

## Artifact Policy

Generated evidence may exist under ignored paths such as:

```text
dist/review-markup/
.cache/
```

Report generated artifacts in the final response, but do not stage or
force-add them.

## Wake-Up Requirement

When done or blocked, send the Makedoc orchestrator
(`019eaf80-3882-7d31-b6a4-3cb4c2ab5699`) a short wake-up using thread tools.
Include:

- completion or blocked status;
- changed files;
- validation result;
- generated proof artifact paths, if any;
- final git status;
- recommended next step.

Do not begin follow-up work after sending the wake-up.
