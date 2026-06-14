# Review Markup External Adoption Playbook

This playbook is for safely piloting `review_markup.enabled` in an external
manuscript repository that builds through `makedoc`.

## Purpose

Use this workflow when authors or reviewers need visible Markdown-origin review
traces in generated PDF and DOCX outputs while keeping canonical manuscript
sources and submission profiles clean.

The workflow supports:

- additions: `{++ added text ++}` -> bold `[+ added text +]`
- deletions: `{-- deleted text --}` -> bold `[- deleted text -]`
- substitutions: `{~~ old text ~> new text ~~}` -> bold `[- old text -]` and
  bold `[+ new text +]`
- reviewer notes: `{>> note text <<}` -> bold `[Reviewer note: note text]`

Non-goals:

- not true Microsoft Word Track Changes;
- not Word Review-pane data;
- not DOCX-to-Markdown import;
- not a clean submission-output workflow unless Barry or the target journal
  deliberately asks for visible markup in submission files.

## Safe External Pilot Pattern

Start from a clean manuscript repository if possible. If the repo is already
dirty, stop and decide whether the dirty state is expected before adding a
review pilot.

Use an isolated review profile and an isolated source file:

1. Create a local review branch, or otherwise record that the pilot is
   deliberately local-only.
2. Copy the canonical manuscript source to a dedicated pilot source, for
   example `manuscript/text/main_review_markup_probe.md`.
3. Add review tokens only to the pilot source. Do not put review tokens into
   canonical `manuscript/text/main.md` or submission-ready sources.
4. Add a dedicated profile such as `review_markup_pilot` in the external
   `settings/build.yaml`.
5. Enable review markup only in that profile:

   ```yaml
   review_markup:
     enabled: true
   ```

6. Keep ordinary `draft` and `submission` profiles pointed at canonical clean
   sources.
7. Validate the review profile and ordinary profiles separately.

Example profile shape:

```yaml
review_markup_pilot:
  description: Local pilot profile for visible review-markup output.
  manuscript_sources:
    - ../manuscript/text/main_review_markup_probe.md
    - ../manuscript/text/figures.md
  lint_sources:
    - ../manuscript/text/main_review_markup_probe.md
    - ../manuscript/text/figures.md
  author_metadata: ../manuscript/authors.yaml
  bibliography: ../references/refs.yaml
  csl: ../csl/journal-style.csl
  output_dir: ../build/review-markup-pilot
  output_stem: manuscript_review_markup_pilot
  review_markup:
    enabled: true
```

Adjust author metadata, bibliography, CSL, layout, and figure settings to match
the target manuscript repo. Generated output should normally stay under an
ignored build directory.

## Authoring Rules

Keep review tokens simple:

- keep each token on one source line;
- do not nest review tokens;
- avoid review tokens inside inline code spans, fenced code blocks, HTML
  comments, figure image lines, and any source intended for clean submission;
- use reviewer notes for comments that should be visible in generated output;
- use ordinary Markdown comments or issue trackers for notes that should not
  appear in generated output.

Review markup is intentionally visible in generated files. It is not hidden
editorial metadata.

## Validation Checklist

Run commands from `/Users/bwbrook/work/makedoc` unless noted otherwise.

First, verify the feature itself:

```sh
make test-review-markup
```

Validate and build the external review profile:

```sh
CONFIG=/abs/path/to/manuscript-repo/settings/build.yaml PROFILE=review_markup_pilot make validate-config
CONFIG=/abs/path/to/manuscript-repo/settings/build.yaml PROFILE=review_markup_pilot make -B all
```

Validate ordinary manuscript profiles separately:

```sh
CONFIG=/abs/path/to/manuscript-repo/settings/build.yaml PROFILE=draft make validate-config
CONFIG=/abs/path/to/manuscript-repo/settings/build.yaml PROFILE=submission make validate-config
```

If cheap and stable, also build ordinary profiles:

```sh
CONFIG=/abs/path/to/manuscript-repo/settings/build.yaml PROFILE=draft make -B all
CONFIG=/abs/path/to/manuscript-repo/settings/build.yaml PROFILE=submission make -B all
```

From the manuscript repo, confirm the canonical source has no review tokens:

```sh
rg '\{\+\+|\{--|\{~~|\{>>' manuscript/text/main.md
```

No matches is the desired result.

Inspect generated evidence:

- PDF text extraction should include bracketed review traces, but this is not
  sufficient by itself.
- Render the relevant PDF page to an image and inspect it by eye. Deleted and
  old wording must be readable in the page image.
- DOCX should show useful visible review traces for additions, deletions,
  substitutions, and notes.

Example PDF image rendering:

```sh
mkdir -p /tmp/makedoc-review-markup
pdftoppm -f 2 -l 2 -png -r 240 \
  /abs/path/to/manuscript-repo/build/review-markup-pilot/manuscript_review_markup_pilot.pdf \
  /tmp/makedoc-review-markup/review-pilot-page
```

Adjust the page number and output stem for the manuscript.

## Evidence And Artifact Policy

Generated PDF, DOCX, manifest, text extraction, XML extraction, and rendered
page images are evidence artifacts. They are normally ignored outputs, not
source history.

Record enough evidence for review:

- external branch/status and HEAD;
- review profile name;
- dedicated pilot source path;
- output artifact paths;
- validation commands and results;
- rendered PDF page-image path and visual conclusion;
- confirmation that canonical clean sources remain token-free.

Do not force-add generated artifacts unless Barry or the orchestrator explicitly
asks for an archival evidence commit.

## CPE Pilot Disposition

The first real external pilot used
`/Users/bwbrook/papers/cpe_time_to_extinction` on local branch
`codex/makedoc-review-markup-pilot`.

Current disposition decision for Goal 005: preserve that CPE branch unchanged
as local evidence. Do not commit it, push it, discard it, reset it, clean it,
or convert it into manuscript history during Goal 005.

The preserved state is useful because it records:

- a dedicated `review_markup_pilot` profile in CPE `settings/build.yaml`;
- an isolated pilot source at
  `manuscript/text/main_review_markup_probe.md`;
- generated review-markup PDF/DOCX/manifests under ignored
  `build/review-markup-pilot/`;
- a real external-manuscript proof that canonical `main.md` can remain clean.

Later options, each requiring explicit approval:

- keep the branch as a local regression/evidence branch;
- remove the local branch and generated artifacts after evidence is no longer
  needed;
- formalize a manuscript-side review profile in CPE history;
- repeat the adoption pattern in another manuscript repo.

## Decision Gates

Accept an external pilot when:

- review profile validation and build pass;
- ordinary draft/submission profiles still validate or build as expected;
- canonical manuscript sources remain token-free;
- PDF deletion and old-wording traces are readable by eye in rendered page
  images;
- DOCX traces are visible enough for human review;
- generated artifacts are recorded but not force-added by default.

Ask Barry or the orchestrator before:

- putting review tokens into canonical manuscript sources;
- weakening submission profile validation;
- committing a manuscript-side review profile;
- deleting or publishing a preserved pilot branch;
- changing scientific manuscript content while creating a review pilot;
- accepting visible markup in a journal submission output.

Open a separate DOCX-to-Markdown import spike only if Barry wants generated
DOCX edits or comments reconciled back into Markdown. That is a different
problem from visible generated review traces.
