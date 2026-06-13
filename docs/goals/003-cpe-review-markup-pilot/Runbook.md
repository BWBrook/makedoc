# Runbook: CPE Review Markup External Manuscript Pilot

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
git log -5 --oneline
git remote -v
```

Record results in `Log.md`.

## CPE Branch Preparation

Only if CPE status is clean:

```sh
git fetch --prune origin
git merge --ff-only origin/main
git switch -c codex/makedoc-review-markup-pilot
```

Stop and wake the orchestrator if any step fails or if the branch already
exists.

## Pilot Profile Shape

Suggested CPE profile:

```yaml
  review_markup_pilot:
    description: Local pilot profile for makedoc review-markup output.
    manuscript_sources:
      - ../manuscript/text/main_review_markup_probe.md
      - ../manuscript/text/figures.md
    lint_sources:
      - ../manuscript/text/main_review_markup_probe.md
      - ../manuscript/text/figures.md
    author_metadata: ../manuscript/authors.yaml
    bibliography: ../references/refs.yaml
    csl: ../csl/cambridge-university-press-author-date-cambridge-a.csl
    journal: Cambridge Prisms Extinction
    csl_search_dirs:
      - ../csl
    output_dir: ../build/review-markup-pilot
    output_stem: cpe_time_to_extinction_review_markup_pilot
    page_numbers: lower_right
    line_spacing: 1.5
    line_numbering: continuous
    review_markup:
      enabled: true
    figures:
      placement: captions_page
      caption_position: top
      placeholder_id: figures
    margins:
      unit: cm
      paper_size: a4
      top: 2.0
      right: 2.5
      bottom: 2.0
      left: 2.5
```

Adjust only if the CPE profile has changed after fast-forwarding.

## Suggested Pilot Probe

Create `manuscript/text/main_review_markup_probe.md` as a copy of
`manuscript/text/main.md`, then add near the start:

```markdown
Pilot-only review-markup probe: {++ inserted pilot text ++}, {-- removed pilot text --}, {~~ old pilot wording ~> revised pilot wording ~~}, and {>> confirm visible review trace output <<}.
```

Keep `manuscript/text/main.md` unchanged.

## Validation Commands

From `/Users/bwbrook/work/makedoc`, sequentially:

```sh
make test-review-markup
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make validate-config
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make -B all
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=draft make validate-config
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=submission make validate-config
```

If cheap and stable, also:

```sh
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=draft make -B all
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=submission make -B all
```

Inspect review artifacts:

```sh
pdftotext /Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf -
unzip -p /Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.docx word/document.xml
```

Expected visible markers include:

```text
[+ inserted pilot text +]
[- removed pilot text -]
[- old pilot wording -] [+ revised pilot wording +]
[Reviewer note: confirm visible review trace output]
```

Expected DOCX XML also includes:

```text
<w:strike
```

From `/Users/bwbrook/papers/cpe_time_to_extinction`:

```sh
rg '\\{\\+\\+|\\{--|\\{~~|\\{>>' manuscript/text/main.md
git diff --check
git status --short --branch
```

From `/Users/bwbrook/work/makedoc`:

```sh
git diff --check -- docs/goals/003-cpe-review-markup-pilot
git status --short --branch
```

## Artifact Policy

Expected generated CPE artifacts:

```text
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.docx
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot_build_manifest.json
```

Do not stage or force-add them.

## Wake-Up Requirement

When done or blocked, send the Makedoc orchestrator
(`019eaf80-3882-7d31-b6a4-3cb4c2ab5699`) a short wake-up using thread tools.
Include:

- completion or blocked status;
- CPE fast-forward result;
- CPE pilot branch name;
- changed files in each repo;
- generated artifact paths;
- validation result;
- final statuses for both repos;
- recommended next step.

Do not begin follow-up work after sending the wake-up.
