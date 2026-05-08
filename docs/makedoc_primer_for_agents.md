# makedoc Primer for Agents in Other Repos

This primer is for coding agents (or humans) working in a manuscript repository that wants to build journal-ready PDF and DOCX outputs via `makedoc`.

It assumes zero prior context.

## 0. Integration policy (important)

This workflow uses **external-path mode only**.

What that means:

1. The manuscript stays in its own repository.
2. `makedoc` reads manuscript/references/CSL files via paths configured in `settings/build.yaml`.
3. Builds are run from `makedoc` against that external config.

Do **not** implement or rely on copy/sync workflows (for example copying `manuscript/` into `makedoc` before builds).  
Reason: copy/sync introduces drift risk and weakens reproducibility guarantees.

## 1. What makedoc expects

`makedoc` builds manuscript outputs from a profile (YAML config) that points to:

1. Markdown manuscript source files
2. A bibliography YAML file
3. A CSL style file
4. Optional author metadata YAML
5. Optional figure-placement settings and layout settings

The build profile controls where files are, how figures are handled, citation styling, and layout defaults.

## 2. Recommended folder layout in your manuscript repo

Use this layout unless you have a strong reason not to.

```text
<your-repo>/
  manuscript/
    text/
      main.md
      figures.md
    figures/
      fig1.png
      fig2.png
      figS1.png
    authors.yaml
  references/
    refs.yaml
  csl/
    journal-style.csl
  settings/
    build.yaml
```

Notes:

- `main.md` is a recommended name for the primary body file, but it is not required.
- `figures.md` should contain figure markdown blocks only (recommended), though figure lines can exist in any manuscript source.
- `authors.yaml` is optional but recommended when you want structured author block generation.
- `refs.yaml` is a recommended bibliography filename, but it is not required.
- `journal-style.csl` is your journal citation style.
- In external-path mode, profile entries may be absolute or relative to `settings/build.yaml`. Absolute paths remain fine when you want maximum explicitness.

## 3. Authoritative file contracts

### 3.1 `manuscript/text/main.md` (or any primary source filename)

Recommended skeleton:

```markdown
# Your Manuscript Title

<div id="authors"></div>

## Abstract

Your abstract text with citations [@keyOne].

## Keywords

keyword one; keyword two

## Introduction

Narrative citation: @keyTwo demonstrated...
Parenthetical citation: [@keyOne; @keyThree].

## Methods

...

## Results

Reference figures as links to figure IDs, for example Fig. [1](#fig-main-1).

## Discussion

...

## References
```

Important behavior:

1. If `<div id="authors"></div>` exists and `author_metadata` is configured, makedoc injects the generated author block there.
2. If that placeholder is missing, author block injection falls back to right after the first H1 (`# Title`).
3. By default, makedoc inserts page breaks:
   - after the generated author block
   - before first `Introduction`
   - before `References`
4. If `## References` exists, makedoc anchors bibliography there.
5. If no references heading exists, Pandoc appends bibliography at the end.

### 3.2 Citation syntax requirements in markdown

Use Pandoc citekeys only:

- Single: `[@alpha2020]`
- Multiple: `[@alpha2020; @beta2021]`
- Narrative: `@delta2023 showed ...`

Avoid manual citations like `(Smith 2020)`. `makedoc` lint flags these as errors.

### 3.3 `manuscript/text/figures.md`

Use one image per markdown figure line, with attribute block and explicit ID:

```markdown
![Caption for main figure.](../figures/fig1.png){#fig-main-1 width=90%}

![Caption for second figure.](../figures/fig2.png){#fig-main-2 width=85%}

![Caption for supplementary figure.](../figures/figS1.png){#fig-main-s1 width=85%}
```

Rules:

1. Include `{...}` attribute block; this is how makedoc parses IDs and width.
2. Include `#fig-...` in attributes for stable linking.
3. Supplementary detection is ID-based: IDs ending in `-s<number>` (for example `#fig-main-s1`) are treated as supplementary.
4. Alt text (the text inside `![ ... ]`) is used as caption/title text in figure workflows.
5. Relative image paths are resolved from the Markdown file they appear in. Absolute image paths still work.

### 3.4 `manuscript/authors.yaml`

Example:

```yaml
title_note: Optional short note under author line.
authors:
  - name: Jane A. Example
    affiliations: [aff1, aff2]
    corresponding: true
    email: jane@example.org
    orcid: 0000-0000-0000-0000
  - name: John B. Sample
    affiliations: [aff2]
    corresponding: false
    email: john@example.org
    orcid: 0000-0000-0000-0001
affiliations:
  aff1: Department of Biology, Example University, City, Country
  aff2: Institute of Ecology, Example Center, City, Country
```

Schema notes:

1. `affiliations` must be a non-empty mapping.
2. `authors` must be a non-empty list.
3. Every `authors[*].affiliations` entry must reference an existing affiliation key.
4. Output renders names with superscript affiliation numbers (for example `Jane Example*^1,2^`).

### 3.5 `references/refs.yaml`

Example:

```yaml
---
references:
  - id: alpha2020
    citation-key: alpha2020
    type: article-journal
    title: Example paper title
    author:
      - family: Alpha
        given: Alice
    issued:
      - year: 2020
    container-title: Example Journal
    volume: '12'
    issue: '3'
    page: 101-118
...
```

Rules:

1. Root key should be `references:` containing a list.
2. Each entry should include at least one citation key field: `citation-key` or `id`.
3. Best practice: set both `id` and `citation-key` to the same value.
4. Markdown `@citekeys` must exactly match these keys.

Filename policy:

1. `refs.yaml` is only a convention, not a parser requirement.
2. Choose one canonical bibliography filename in the manuscript repo.
3. Point profile key `bibliography` at that canonical file.
4. Avoid maintaining duplicate bibliography files with the same content, because they drift.

### 3.6 `csl/journal-style.csl`

- Place the chosen journal CSL file here.
- Point profile key `csl` to this path.
- Optional: maintain `csl_search_dirs` for discovery/sourcing workflows.

## 4. Build profile template (`settings/build.yaml`)

Use this as your starting point. In external-path mode, profile entries may be absolute or relative to `settings/build.yaml`.

```yaml
default_profile: my_ms

profiles:
  my_ms:
    description: Active manuscript profile
    manuscript_sources:
      - ../manuscript/text/main.md
      - ../manuscript/text/figures.md
    # Optional. If omitted, defaults to manuscript_sources.
    lint_sources:
      - ../manuscript/text/main.md
      - ../manuscript/text/figures.md

    author_metadata: ../manuscript/authors.yaml
    bibliography: ../references/refs.yaml
    csl: ../csl/journal-style.csl
    journal: Journal Name
    csl_search_dirs:
      - ../csl

    output_dir: dist
    output_stem: manuscript

    page_numbers: lower_right      # lower_right | none
    line_spacing: single           # single | 1.1 | 1.25 | 1.5 | 2
    line_numbering: continuous     # continuous | page | section | none

    figures:
      placement: pages             # pages | inline | captions_page
      caption_position: top        # top | bottom
      placeholder_id: figures      # used by inline mode

    margins:
      unit: cm                     # cm | in
      paper_size: a4               # a4 | letter
      top: 2.0
      right: 2.5
      bottom: 2.0
      left: 2.5
```

## 5. Figure placement modes and what they do

### 5.1 `placement: pages` (default)

- Figures are extracted from manuscript sources.
- Figures are appended after references.
- One page break per figure.
- Captions render as `**Fig. X.**` + image.
- Supplementary figures are grouped after `## Supplementary Information`.

### 5.2 `placement: inline`

- Figures are extracted and inserted at `<div id="<placeholder_id>"></div>`.
- If placeholder is missing, figures are appended at end with a warning.
- Caption position can be `top` or `bottom`.

### 5.3 `placement: captions_page`

- Adds a `## Figure Captions` page after references.
- Lists caption lines there (one per figure).
- Then adds figure pages with label only (`Fig. 1.`), image only.
- Supplementary section appears after main figures.

## 6. Behavior that surprises new users

1. `lint_sources` defaults to `manuscript_sources` if omitted.
2. References are page-broken by default.
3. Introduction is page-broken by default.
4. Heading spacing is normalized in prepared markdown for `##` headings.
5. If `output_dir` is `dist`, makedoc auto-routes output to a Make-safe subfolder (`dist/<profile-root>/`) inferred from manuscript paths/repo/fallback.
6. If `output_dir` is any other relative path, it resolves relative to `settings/build.yaml`.
7. Relative paths in profile entries are resolved from the config file directory, and relative image paths in markdown are resolved from the source Markdown file they appear in.

## 7. Lint and audit expectations (must pass)

`makedoc` quality gates include:

1. `lint-manuscript`:
   - fails on unresolved `[REF]`
   - fails on likely manual author-year citations `(Name 2020)`
   - fails on malformed markdown table row counts
2. `refs-audit`:
   - fails if manuscript cites keys missing from bibliography
   - reports unused bibliography keys as non-fatal

Practical implication: convert all citations to Pandoc citekeys before expecting `make check` to pass.

Interim drafting policy:

1. For day-to-day drafting, it is acceptable to run `make all` while citation cleanup is in progress.
2. Keep `make check` as the strict gate for submission-ready builds.
3. Prefer a two-profile approach:
   - `draft` profile for permissive iteration (for example reduced `lint_sources`)
   - `submission` profile for full strict checks
4. Do not weaken the submission profile just to accommodate temporary draft-state citations.

## 8. Agent setup checklist for a fresh manuscript repo

Use this sequence when onboarding a repository.

1. Create directories: `manuscript/text`, `manuscript/figures`, `references`, `csl`, `settings`.
2. Create a primary manuscript file (for example `manuscript/text/main.md` or `manuscript/text/draft_ms_v2.md`) with title, abstract, intro, and `## References` heading.
3. Create `manuscript/text/figures.md` with figure lines using explicit `#fig-...` IDs.
4. Create one canonical bibliography YAML file in `references/` with valid citekeys.
5. Place CSL file in `csl/`.
6. Create `manuscript/authors.yaml` (if author injection is desired).
7. Create `settings/build.yaml` profile using either absolute paths or config-relative paths.
8. Ensure markdown cites use `@citekey` syntax only.
9. Run validations/build from makedoc repo:

```bash
make validate-config CONFIG=/abs/path/to/your-repo/settings/build.yaml
make check CONFIG=/abs/path/to/your-repo/settings/build.yaml
make all CONFIG=/abs/path/to/your-repo/settings/build.yaml
```

Policy reminder: do not copy manuscript files into `makedoc`; keep a single source of truth in the manuscript repo and build by reference.

## 9. Common failure modes and fixes

### Problem: unknown citation key errors

Fix:

1. Search for each unknown `@key` in markdown.
2. Add matching entry in `refs.yaml` or fix typo.
3. Re-run `make check`.

### Problem: author block not inserted

Fix:

1. Confirm `author_metadata` path is set and file exists.
2. Confirm either `<div id="authors"></div>` exists or markdown starts with `# Title`.
3. Validate author YAML schema (non-empty `authors`, non-empty `affiliations`, valid affiliation IDs).

### Problem: figure references not linkable

Fix:

1. Ensure figure line has attribute block with `#fig-id`.
2. Ensure in-text links target exact same anchor (for example `[1](#fig-main-1)`).
3. Keep figure lines out of code fences.

### Problem: inline figure placement does nothing

Fix:

1. Confirm `figures.placement: inline`.
2. Confirm placeholder exists and ID matches `figures.placeholder_id`.

### Problem: references appear at document end instead of your section

Fix:

1. Add heading `## References` in manuscript source.
2. Do not put it inside code fences.

### Problem: relative paths in external config behave inconsistently

Fix:

1. Make relative profile entries relative to the external `settings/build.yaml` file.
2. Re-run `make validate-config` to confirm the resolved files exist.

### Problem: figures compile but images are missing in PDF/DOCX

Fix:

1. Use source-relative image `src` paths in figure markdown lines (for example `../figures/fig1.png` from `manuscript/text/figures.md`) or use absolute paths.
2. Verify each resolved path exists on disk and is readable.
3. Rebuild and check for Pandoc warnings like `Could not fetch resource ...`.

### Problem: multiple bibliography files exist (`refs.yaml` and another copy)

Fix:

1. Pick one canonical bibliography file.
2. Update profile key `bibliography` to point to that file.
3. Remove duplicate copies or clearly mark one as generated and non-editable.

## 10. FAQ: decisions for external-repo agents

### Q: Are relative paths in external config resolved relative to that config file?

Yes. Relative profile paths are interpreted from the external config file directory.

### Q: Are relative image paths in markdown resolved from the source file?

Yes. Relative image paths are interpreted from the Markdown file they appear in.

### Q: Is `main.md` required?

No. `makedoc` accepts any filenames listed in `manuscript_sources`. `main.md` is a naming convention only.

### Q: During drafting, should lint failures be tolerated or should lint be scoped?

Recommended: use a draft/submission split. Keep strict checks in a submission profile, and use a draft profile (or `make all`) during early writing when manual citations/placeholders still exist.

### Q: Should both `refs.yaml` and another bibliography copy be kept?

No, unless there is a strong compatibility reason. Prefer one canonical bibliography file and point profile `bibliography` to it.

## 11. Minimal working example (single profile)

If you just need a first-pass baseline:

1. Use the folder layout in Section 2.
2. Use the file templates in Section 3.
3. Use the profile template in Section 4.
4. Run the three commands in Section 8.

That is enough to get a reproducible manuscript build pipeline with PDF + DOCX output and quality gates.
