# Runbook: PDF Review Markup Legibility Hardening

## Starting Commands

From `/Users/bwbrook/work/makedoc`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
```

From `/Users/bwbrook/papers/cpe_time_to_extinction`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
```

Record results in `Log.md`.

## CPE Boundary

CPE is evidence-only for this goal. Expected status:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

Do not edit, stage, commit, push, fetch, pull, reset, clean, stash, rebase, or
switch branches in CPE. Regenerating ignored `build/` outputs is allowed.

## Useful Artifact Commands

Fixture review-markup build:

```sh
CONFIG=settings/review_markup.yaml make -B all
pdftotext dist/review-markup/review_markup_probe.pdf -
unzip -p dist/review-markup/review_markup_probe.docx word/document.xml
```

CPE pilot build:

```sh
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make -B all
pdftotext /Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf -
unzip -p /Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.docx word/document.xml
```

PDF page-image evidence, example:

```sh
mkdir -p /tmp/makedoc-goal004-review
pdftoppm -f 2 -l 2 -png -r 240 \
  /Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf \
  /tmp/makedoc-goal004-review/cpe-pilot-page
```

Adjust the page number if the review probe moves. Report the actual image path.

## Validation Ladder

Run sequentially from `/Users/bwbrook/work/makedoc`:

```sh
python3 -m unittest tests/test_prepare_markdown_sources.py
make test-review-markup
CONFIG=settings/review_markup.yaml make validate-config
CONFIG=settings/review_markup.yaml make -B all
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make validate-config
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make -B all
make test-author-injection
make test-figure-modes
make check
make check-fixture
git diff --check
```

From CPE, check canonical source cleanliness:

```sh
rg '\{\+\+|\{--|\{~~|\{>>' manuscript/text/main.md
```

No matches is the desired result.

## Log Requirements

Record in `Log.md`:

- starting repo states;
- root-cause or likely-cause finding;
- chosen rendering policy;
- files changed;
- exact validation commands and results;
- fixture artifact paths;
- CPE artifact paths;
- rendered PDF page-image path;
- visual conclusion: deletion/old-wording text readable or not;
- final statuses for `makedoc` and CPE;
- remaining risks.

## Wake-Up Requirement

When done or blocked, wake the Makedoc orchestrator
(`019eaf80-3882-7d31-b6a4-3cb4c2ab5699`) and stop.
