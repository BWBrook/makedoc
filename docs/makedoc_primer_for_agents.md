# makedoc primer for agents working in a manuscript repository

You are in a repository that holds a scientific manuscript and want PDF and DOCX outputs from it. makedoc does that. This primer assumes no prior context and covers makedoc 2. For a repository still wired to the v1 Makefile, follow `MIGRATING.md` first.

## 1. The arrangement

- The manuscript, figures, bibliography and build profile live in the manuscript repository.
- makedoc is a command-line tool that the repository calls at a pinned version. Do not copy manuscript files into the makedoc repository, and do not vendor makedoc into the manuscript repository.
- Requirements on the machine: [uv](https://docs.astral.sh/uv/), Pandoc 3 and a TeX distribution with `xelatex`; Poppler (`pdftoppm`) as well if any figure is a PDF. `makedoc doctor` reports what is missing and how to install it.

Invoke makedoc pinned to a release:

```bash
uvx --from git+https://github.com/BWBrook/makedoc@v2.0.0 makedoc <command>
```

The rest of this primer writes `makedoc` for that. Put the prefix in one place, such as a `MAKEDOC` variable in the repository's Makefile, so the pin is changed in one line.

## 2. Starting a new manuscript

```bash
makedoc init manuscript
```

writes this layout, which is the recommended one:

```text
manuscript/
  settings/build.yaml     build profiles; paths in it are relative to this file
  text/main.md            the manuscript
  text/figures.md         one figure per line
  authors.yaml            authors and affiliations
  references/refs.yaml    bibliography
```

Add `figures/` for images and `csl/` for a citation style. Then, from `manuscript/`:

```bash
makedoc check      # config, lint and citation audit; no build
makedoc build      # writes build/manuscript.pdf, .docx and a build manifest
```

File names are conventions. makedoc reads whatever the profile lists.

## 3. File contracts

### 3.1 Manuscript Markdown

```markdown
# Title

<div id="authors"></div>

## Abstract

Text with a citation [@alpha2020].

## Introduction

@beta2021 showed something. Several sources at once [@alpha2020; @gamma2022].

## Results

The pattern is in Fig. [1](#fig-main-1).

## References
```

- **Citations** use Pandoc keys only. `(Smith 2020)` typed by hand fails `makedoc check`.
- **`<div id="authors"></div>`** is replaced by the author block when the profile sets `author_metadata`. Without the placeholder the block follows the first `# Title`.
- **`## References`** receives the bibliography. Without it, the bibliography goes at the end.
- **Page breaks** are inserted after the author block, before the first `Introduction` heading and before `References` (`references_new_page: false` turns the last one off).
- **Symbols.** Type Greek letters, `≤ ≥ ≈ ≠ → ±`, and sub- or superscripts such as `CO₂` and `m⁻²` directly in body text, or write TeX math (`$\alpha \le 0.05$`). Inside code spans only characters the monospace font has will render; anything else fails the build by name.
- **Code blocks, code spans and HTML comments** are never treated as figures, headings or placeholders, and lint skips them. Commenting out a figure line removes the figure.

### 3.2 Figures

A figure is a paragraph that holds only an image. Write one per line, with an attribute block:

```markdown
![Caption of the first figure.](../figures/fig1.png){#fig-main-1 width=90%}

![Caption of a supplementary figure.](../figures/figS1.png){#fig-main-s1 width=85%}
```

- The image path is relative to the Markdown file it is written in.
- `#fig-...` is the link target. Refer to the figure as `Fig. [1](#fig-main-1)`. You write the number; makedoc numbers figures in the order they appear in the sources, so keep the two in step.
- An id ending in `-s<number>` makes the figure supplementary: `Fig. S1`, placed after the main figures.
- The text in `![...]` is the caption.

### 3.3 `authors.yaml`

```yaml
title_note: Optional line under the authors.
authors:
  - name: Jane A. Example
    affiliations: [aff1, aff2]
    corresponding: true
    email: jane@example.org
    orcid: 0000-0000-0000-0000
  - name: John B. Sample
    affiliations: [aff2]
affiliations:
  aff1: Department of Biology, Example University, City, Country
  aff2: Institute of Ecology, Example Centre, City, Country
```

Every author needs at least one affiliation key that exists under `affiliations`. Affiliations are numbered in order of first use.

### 3.4 Bibliography

Pandoc CSL YAML with a top-level `references:` list:

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
    page: 101-118
...
```

Give each entry both `id` and `citation-key`, equal to the `@key` used in the text. Keep one bibliography file per repository.

### 3.5 Citation style

```bash
makedoc csl search "Ecology Letters"
makedoc csl fetch "Ecology Letters" --dest csl
```

Point the profile's `csl` at the file. With no `csl`, Pandoc's default author–date style is used.

## 4. Build profiles

`settings/build.yaml` holds one or more profiles. The full key reference is in the makedoc `README.md`; this is the usual shape for a paper with a draft and a submission layout:

```yaml
default_profile: draft

common: &common
  manuscript_sources:
    - ../text/main.md
    - ../text/figures.md
  author_metadata: ../authors.yaml
  bibliography: ../references/refs.yaml
  csl: ../csl/journal.csl
  output_dir: ../build
  margins: {unit: cm, paper_size: a4, top: 2.0, right: 2.5, bottom: 2.0, left: 2.5}

profiles:
  draft:
    <<: *common
    output_stem: draft
    line_spacing: single
    line_numbering: none
    figures: {placement: inline, caption_position: bottom}

  submission:
    <<: *common
    output_stem: manuscript
    line_spacing: 2
    line_numbering: continuous
    figures: {placement: captions_page}
```

`common` is ignored by makedoc itself; it only carries the YAML anchor. Unknown keys are errors, so a typo is caught by `makedoc check`.

Select profiles with `-p NAME` (repeatable) or `--all`. With neither, `default_profile` is used.

### Figure placement

| `figures.placement` | Result |
| --- | --- |
| `pages` (default) | Figures move after the references, one per page, each as `Fig. 1. Caption` with the image. |
| `captions_page` | A "Figure Captions" page lists all captions; each figure then has its own page with the label only. Common for submission. |
| `inline` | All figures are gathered at `<div id="figures"></div>` in the text (the id is `figures.placeholder_id`). If the placeholder is missing they go at the end, with a warning. |
| `in_place` | Each figure stays where it is written, as `Fig. 1. Caption` with the image. Use it for a draft that reads with figures beside their text. A figure that does not fit the rest of a page starts the next one. |

`figures.caption_position` is `top` or `bottom`. In the PDF a figure's caption and image always share a page, and an image too tall for the page is scaled to fit. With line numbering on, caption lines are numbered and the image is not.

makedoc arranges figures written at the top level of the document. An image inside a fenced div, a list or a table is left to Pandoc, which gives it its own `Figure N:` caption; do not mix that with makedoc's numbering.

Vector figures can be supplied as PDF. The PDF output embeds them as they are, and the DOCX gets a 300 dpi PNG.

### LaTeX additions

A YAML metadata block at the top of a source file can add preamble lines; they come after makedoc's layout:

```markdown
---
header-includes:
  - \usepackage{pdflscape}
---
```

A raw block (```` ```{=latex} ````) in the body is passed to LaTeX and ignored by the DOCX.

## 5. Checks, warnings and what a green build means

`makedoc check` fails on an invalid config, a missing input file, a `[REF]` placeholder, a hand-typed author–year citation, a table row with the wrong number of cells, or a cited key missing from the bibliography. Uncited bibliography entries are counted, not failed.

`makedoc build` does not run those checks, so drafts with unfinished citations still build. It prints every Pandoc and LaTeX warning as `warning [profile]: ...`. Use `--strict` for a submission build so that a warning is a failure.

A build fails, and writes no output for that format, when a character has no glyph in the PDF font, an image file is missing from a figure line, a PNG is 16-bit with alpha, or a required LaTeX package is absent.

A passing build means the pipeline ran. It does not mean the document is right. Open the PDF and the DOCX: look at tables that might overflow the page, figure sizes, the reference list, and the title page.

## 6. Reproducibility

Each build writes `<output_stem>_build_manifest.json` in the output directory with the makedoc, Pandoc and xelatex versions, the manuscript repository's commit, the resolved profile, SHA-256 hashes of every input (figure images included) and output, and the warnings.

The makedoc version is fixed by the tag in the `uvx --from ...@TAG` spec; use a commit hash there for an immutable pin. To move to a newer makedoc, change the pin, rebuild, inspect the outputs, and commit the pin change with them.

## 7. A wrapper Makefile

```make
MAKEDOC := uvx --from git+https://github.com/BWBrook/makedoc@v2.0.0 makedoc

.PHONY: all check
all:
	$(MAKEDOC) build --all --strict

check:
	$(MAKEDOC) check --all
```

Run it from the directory that holds `settings/`, or pass `-c path/to/build.yaml`.

## 8. Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `citation key 'x' is not in the bibliography` | Typo in the key, or the entry is missing. Fix the text or add the entry. |
| `Possible manual author-year citation` on a line that is not a citation | The lint matches `(Capitalised … 2020)`. Reword, or keep that file out of `lint_sources`. |
| `The PDF font has no glyph for these characters` | The character is in a code span, or is outside the fallback set. Use TeX math, or set `fonts.main` / `fonts.mono` to a font that has it. |
| `PNG files are 16-bit with an alpha channel` | xelatex would render them invisible. Re-save as 8-bit: `magick in.png -depth 8 out.png`. |
| `Image file not found` | A relative image path is resolved from the Markdown file's directory. Fix the path. |
| `Hyper reference 'fig-x' ... undefined` | The text links to a figure id that no figure line defines. |
| Author block missing | `author_metadata` is not set in the selected profile, or there is neither the placeholder nor a `# Title` heading. |
| Inline figures appear at the end | The `<div id="figures"></div>` placeholder is missing or its id differs from `figures.placeholder_id`. |
| Review markup shows as literal `{++ ++}` | `review_markup.enabled` is not `true` in the selected profile, or the token spans more than one line. |
| Need to see what makedoc did to the sources | `makedoc build --workdir /tmp/work` keeps `prepared.md` (joined sources), `resolved.json` (the arranged document; view it with `pandoc -f json -t markdown resolved.json`), `layout.tex` and the LaTeX log. |
| Unknown profile key error naming `golden_contract` or `edgecases` | v1 keys. Delete them; see `MIGRATING.md`. |

## 9. Review markup (optional)

With `review_markup: {enabled: true}` in a profile, these single-line tokens render as bold bracketed traces in both outputs:

| Source | Meaning |
| --- | --- |
| `{++ added text ++}` | addition |
| `{-- deleted text --}` | deletion |
| `{~~ old ~> new ~~}` | substitution |
| `{>> note <<}` | reviewer note |

Tokens cannot nest or span lines. This produces visible traces only. It does not create Word tracked changes. For tracked changes and comment threads on the Markdown sources, use scrivmark.

## 10. Reporting a makedoc problem

Separate the two cases before changing anything. A malformed table, an unknown citation key or a missing figure is the manuscript's problem: fix it in the manuscript repository. Wrong figure order, a broken link that the sources define correctly, bad DOCX layout or a crash is makedoc's problem: report it at <https://github.com/BWBrook/makedoc/issues> with the command, the output and the profile, and do not work around it silently in the manuscript repository.
