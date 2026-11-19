# makedoc

> **Status:** developed in the open as a working record. This is work in progress: contents may change, and nothing here is peer-reviewed unless stated.

makedoc builds journal-ready PDF and DOCX manuscripts from Markdown sources, figures, a bibliography and a YAML build profile. The manuscript stays in its own repository; makedoc is the build tool it calls.

This is **version 2**. If you have a repository that built with the v1 Makefile, read [MIGRATING.md](MIGRATING.md).

## Install

makedoc needs Pandoc 3 and a TeX distribution with `xelatex`. `makedoc doctor` checks them.

```bash
brew install pandoc texlive poppler            # macOS
sudo apt-get install pandoc texlive-xetex texlive-latex-extra texlive-fonts-recommended lmodern poppler-utils   # Ubuntu
```

Run makedoc with [uv](https://docs.astral.sh/uv/), pinned to a release, with nothing to install or keep in step:

```bash
uvx --from git+https://github.com/BWBrook/makedoc@v2.0.0 makedoc --version
```

The examples below write `makedoc` for that prefix. To put the command on your PATH instead:

```bash
uv tool install git+https://github.com/BWBrook/makedoc@v2.0.0
```

## Quick start

```bash
makedoc init paper            # writes a starter layout into paper/
cd paper
makedoc check                 # validate the config, lint the text, audit citations
makedoc build                 # writes build/manuscript.pdf and build/manuscript.docx
```

`makedoc init` writes:

```text
settings/build.yaml     build profiles
text/main.md            the manuscript
text/figures.md         one figure per line
authors.yaml            authors and affiliations
references/refs.yaml    bibliography (CSL YAML)
```

## Commands

Every command that reads a config takes `-c PATH` (default `settings/build.yaml`). Commands that act on profiles take `-p NAME` (repeatable) or `--all`; with neither, they use the config's `default_profile`.

| Command | What it does |
| --- | --- |
| `makedoc build` | Builds PDF and DOCX and writes a build manifest. `--pdf` or `--docx` builds one format. `--strict` turns warnings into a failing exit code. `--workdir DIR` keeps the intermediate files (`prepared.md`, `resolved.json`, `layout.tex`, LaTeX logs). |
| `makedoc check` | Validates the config, lints the sources and audits citations against the bibliography. Does not build. |
| `makedoc profiles` | Lists the profiles in a config. |
| `makedoc show` | Prints a profile with every path and default resolved. |
| `makedoc init [DIR]` | Writes the starter layout. Refuses to overwrite files. |
| `makedoc doctor` | Checks Pandoc, xelatex and the LaTeX packages makedoc uses. |
| `makedoc csl search JOURNAL` | Lists matching citation styles, local and from the Zotero style repository. |
| `makedoc csl fetch JOURNAL` | Downloads the best match into `./csl` (or `--dest DIR`). |

Exit codes: 0 on success, 1 when a check or build fails.

A build always starts from the sources; there is no incremental state to go stale. Each build uses its own temporary work directory, so builds of different profiles or papers can run at the same time.

## Build profiles

A config holds one or more profiles. Paths are relative to the config file.

```yaml
default_profile: main

profiles:
  main:
    description: Review layout
    manuscript_sources:            # required; concatenated in order
      - ../text/main.md
      - ../text/figures.md
    lint_sources:                  # optional; defaults to manuscript_sources
      - ../text/main.md
    author_metadata: ../authors.yaml          # optional
    bibliography: ../references/refs.yaml     # required
    csl: ../csl/journal.csl                   # optional; Pandoc's default style otherwise
    journal: Journal Name                     # optional label
    output_dir: ../build                      # required
    output_stem: manuscript                   # required; gives manuscript.pdf, manuscript.docx
    page_numbers: lower_right      # lower_right | none
    line_spacing: single           # single | 1.1 | 1.25 | 1.5 | 2
    line_numbering: continuous     # continuous | page | section | none
    references_new_page: true      # page break before the References heading
    figures:
      placement: pages             # pages | captions_page | inline | in_place
      caption_position: top        # top | bottom
      placeholder_id: figures      # the <div id="..."> used by inline placement
    margins:
      unit: cm                     # cm | in
      paper_size: a4               # a4 | letter
      top: 1.5
      right: 1.5
      bottom: 1.5
      left: 1.5
    fonts:                         # optional; PDF fonts, by a name `fc-list` shows
      main: STIX Two Text
      math: STIX Two Math          # also: sans, mono
    review_markup:
      enabled: false               # render CriticMarkup-style tokens as visible traces
```

A top-level `common:` key is ignored by makedoc, so it can hold a YAML anchor shared by several profiles (`<<: *common`). Unknown keys are errors.

## What the build does to the sources

- **Authors.** With `author_metadata` set, an author block with superscript affiliations replaces `<div id="authors"></div>`, or follows the first `# Title` heading if that placeholder is absent. A page break follows it.
- **Sections.** The first `Introduction` heading starts a new page. A `References` heading receives the bibliography, on a new page unless `references_new_page: false`. Without that heading the bibliography follows the text, before any figures placed at the end.
- **Figures.** A figure is a paragraph holding only an image, normally with an attribute block: `![Caption.](../figures/fig1.png){#fig-one width=90%}`. Several such lines in a row, one image per line, are each a figure. Image paths are relative to the Markdown file. An id ending in `-s1`, `-s2`, … marks a supplementary figure. Link to a figure with `Fig. [1](#fig-one)`.
  - `pages`: figures move after the references, one per page, each as `Fig. 1. Caption` with its image; supplementary figures (Fig. S1, …) follow.
  - `captions_page`: a Figure Captions page lists every caption, then each figure follows on its own page with its label only.
  - `inline`: all figures are gathered at `<div id="figures"></div>`.
  - `in_place`: each figure stays where it is written.
  - Each figure has one label and its caption and image share a page. Only top-level figures are arranged; an image inside a fenced div is left to Pandoc. A PDF image is embedded as it is in the PDF and converted to PNG for the DOCX.
- **LaTeX additions.** `header-includes` in a source file's YAML metadata is added to the preamble after makedoc's layout.
- **Unicode.** Greek letters, relations, arrows and Unicode sub- and superscripts typed in body text are rendered through LaTeX fallbacks when the PDF font lacks them. If any character still has no glyph, the build fails and names it; nothing is dropped silently. Code spans use the monospace font and get no fallback.
- **Images.** A 16-bit PNG with an alpha channel fails the PDF build, because xelatex would embed it fully transparent. Re-save it as 8-bit.
- **Code and comments.** makedoc arranges the document after Pandoc has parsed it, so anything inside a code block, a code span or an HTML comment is never treated as a figure, heading or placeholder. Lint and the citation audit skip those regions too.
- **DOCX.** After Pandoc writes the DOCX, makedoc applies the profile's page size, margins, line spacing, line numbering and page numbers, sets headings to black, and fills in title and author metadata.
- **Review markup** (off by default). `{++added++}`, `{--deleted--}`, `{~~old~>new~~}` and `{>>note<<}` on a single line render as bold bracketed traces. This is outbound only; Word comments, tracked changes and DOCX-to-Markdown reconciliation are outside makedoc. Review at the source with scrivmark (`docs/docx_review_boundary.md`).

## Checks

`makedoc check` fails on:

- an invalid config or a missing input file;
- a `[REF]` placeholder;
- a hand-typed author–year citation such as `(Smith 2020)`; use `[@smith2020]`;
- a Markdown table row whose cell count differs from its header;
- a cited key that is not in the bibliography.

Bibliography entries nobody cites are counted but do not fail.

`makedoc build` does not run these checks, so a draft with unfinished citations still builds. It reports Pandoc and LaTeX warnings (an undefined figure link, a missing image), and `--strict` makes them fail.

## Reproducibility

Each build writes `<output_stem>_build_manifest.json` beside the outputs: makedoc, Pandoc and xelatex versions, the manuscript repository's commit, the resolved profile, a SHA-256 for every input (including figure images) and output, and the warnings.

Pin makedoc by release tag, as in the `uvx` command above, or by commit hash for an immutable pin. TeX and Pandoc remain system dependencies; the manifest records which versions ran.

## Development

```bash
git clone git@github.com:BWBrook/makedoc.git && cd makedoc
uv run pytest -q                                              # unit and end-to-end tests
uv run makedoc build -c testbed/settings/build.yaml --all     # build the fixture
```

`testbed/` is a synthetic manuscript used as the regression fixture. [AGENTS.md](AGENTS.md) describes how the repository is organised and what to run after a change. [docs/makedoc_primer_for_agents.md](docs/makedoc_primer_for_agents.md) is the guide for an agent setting up or maintaining a manuscript repository that builds with makedoc.

## Licence

Code is under the MIT licence ([LICENSE](LICENSE)); text and figures are under CC BY-SA 4.0 ([LICENSE-CONTENT](LICENSE-CONTENT)).
