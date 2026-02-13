# makedoc

Config-driven manuscript build tooling for generating journal-submission outputs (`.pdf` and `.docx`) from Markdown, references, figures, and CSL styles.

This repository now uses a synthetic regression fixture (`testbed/`) as the default build input, so the pipeline is always runnable in isolation.

## Ubuntu/WSL Bootstrap

Use the installer helper for first-time setup on Ubuntu 24.04 (including WSL Ubuntu):

```bash
make deps-estimate-minimal
make deps-install-minimal
make wsl-smoke
```

Optional "full monty" profile with extra tooling:

```bash
make deps-estimate-full
make deps-install-full
```

Install modes:
- `minimal`: build/check essentials for this repo (`pandoc`, `xelatex`, `texlive-xetex`, `texlive-latex-extra`, `python3-yaml`, `ripgrep`, etc.)
- `full`: `minimal` plus heavier optional tools (`libreoffice`, broader TeX extras, hunspell locales, `poppler-utils`)

Notes for line numbering:
- If line numbering is enabled, the LaTeX `lineno` package is required. It is present in `full` mode installs (`texlive-latex-extra`) and is checked before rendering.

Disk-size note:
- both estimate targets run `apt-get -s install ...` and print the host-specific "After this operation..." line, which gives a rough install size for that machine.
- package availability and size can vary across mirrors and preinstalled system state.

Direct script usage is also available:

```bash
scripts/install_ubuntu_deps.sh --mode minimal --estimate-only
scripts/install_ubuntu_deps.sh --mode full --dry-run
```

## Clone in WSL

Two reliable options:

Option A (`https`, quickest):

```bash
sudo apt-get update
sudo apt-get install -y git gh
gh auth login --hostname github.com --git-protocol https --web
mkdir -p ~/git
cd ~/git
git clone https://github.com/BWBrook/makedoc.git
cd makedoc
```

Option B (`ssh`, best long-term ergonomics):

```bash
sudo apt-get update
sudo apt-get install -y git gh openssh-client
[ -f ~/.ssh/id_ed25519.pub ] || ssh-keygen -t ed25519 -C "your_email@example.com"
gh auth login --hostname github.com --git-protocol ssh --web
gh ssh-key add ~/.ssh/id_ed25519.pub --title "$(hostname)-wsl"
ssh -T git@github.com
mkdir -p ~/git
cd ~/git
git clone git@github.com:BWBrook/makedoc.git
cd makedoc
```

## Quick Start

```bash
make validate-config
make check
make all
ls -lh dist/
```

Default outputs:
- `dist/<profile-root>/manuscript.pdf`
- `dist/<profile-root>/manuscript.docx`

`<profile-root>` is derived automatically from manuscript sources:
- If a source path contains a `manuscript/` directory, the containing parent folder name is used (for example `testbed`).
- Otherwise, if sources are inside a git repository, that repository name is used.
- If neither can be inferred, the system falls back to `manuscript-#` under `dist/`.

Fixture outputs:
- `dist/fixture/fixture_manuscript.pdf`
- `dist/fixture/fixture_manuscript.docx`

Fixture-only build:
```bash
make testbed
```
This runs the dedicated fixture profile and writes into `dist/fixture/` only (no files are emitted to the `dist/` root by this path).

Regression checks:
```bash
make test-output-routing
```
Runs a unit-style routing test that validates fixture-only and default output locations.

Figure placement regression:
```bash
make test-figure-modes
```
Verifies the new figure pipeline behavior in `pages`, `inline`, and `captions_page` modes, including:
- ordered `Fig. 1`, `Fig. 2`, `Fig. S1` labels
- supplementary figure ordering
- inline insertion at a placeholder with bottom-positioned captions.

Workspace cleanup:
```bash
make tidy
make clean
make clean-all
```

- `make tidy`: remove only local build scratch artifacts (`test-*` files, `texput.log`, LaTeX scratch artifacts in `.cache/latex`).
- `make clean`: remove generated outputs (`dist/`, `.cache/`) and root scratch logs (`texput.log`, `test-*`).
- `make clean-all`: alias for `make clean tidy`.

## Build Profiles (YAML-Driven)

Build inputs are split across:
- `settings/build.yaml` for active manuscript profiles (`make all`, `make check`)
- `settings/fixture.yaml` for fixture/testbed checks (`make fixture-all`, `make check-fixture`, CI fixture job)

Current profile layout:
- `default` in `settings/build.yaml`: active profile used by `make all` and `make check`
- `fixture` in `settings/fixture.yaml`: dedicated regression profile used by fixture checks/guard tests

Useful commands:

```bash
make profiles
make profile-show
make fixture-all
make check-fixture
```

Scaffold a new profile snippet:

```bash
make profile-scaffold PROFILE_NAME=my_ms
```

Scaffold and append a real profile using paths from another repository:

```bash
make profile-scaffold \
  PROFILE_NAME=my_ms \
  PROFILE_MAIN=/path/to/other-repo/manuscript/text/main.md \
  PROFILE_FIGS=/path/to/other-repo/manuscript/text/figures.md \
  PROFILE_BIB=/path/to/other-repo/references/refs.yaml \
  PROFILE_CSL=/path/to/other-repo/csl/oikos.csl \
  PROFILE_PAGE_NUMBERS=lower_right \
  PROFILE_LINE_SPACING=single \
  PROFILE_LINE_NUMBERING=continuous \
  PROFILE_FIGURE_PLACEMENT=pages \
  PROFILE_FIGURE_CAPTION_POSITION=top \
  PROFILE_FIGURE_PLACEHOLDER_ID=figures \
  PROFILE_PAPER_SIZE=a4 \
  PROFILE_MARGIN_UNIT=cm \
  PROFILE_MARGIN_TOP=1.5 \
  PROFILE_MARGIN_RIGHT=1.5 \
  PROFILE_MARGIN_BOTTOM=1.5 \
  PROFILE_MARGIN_LEFT=1.5 \
  PROFILE_APPEND=1 \
  PROFILE_SET_DEFAULT=1
```

## Config Schema

Each profile supports:

- `manuscript_sources`: ordered Markdown input files for Pandoc
- `lint_sources`: Markdown files scanned by lint checks. If omitted, this defaults to `manuscript_sources`.
- `bibliography`: YAML bibliography path
- `csl`: CSL file path
- `journal`: optional journal label/metadata
- `csl_search_dirs`: directories scanned by CSL discovery tools
- `output_dir`: output folder
- `dist` values are auto-routed to `dist/<profile-root>`.
- `output_stem`: output basename (without extension)
- `golden_contract`: optional fixture/contract expectations file used by structure checks
- `page_numbers`: page-numbering mode for PDF output (`lower_right`, `none`)
- `line_spacing`: line spacing mode (`single`, `1.5`, `2`)
- `line_numbering`: line-numbering mode (`continuous`, `page`, `section`, `none`)
- `figures`:
  - `placement`: `pages` (default, one figure per page after references),
    `inline`, or `captions_page`
  - `caption_position`: `top` (default) or `bottom`
  - `placeholder_id`: placeholder `<div id="..."></div>` identifier used for inline placement
- `margins`:
  - `unit`: `cm` (default) or `in`
  - `paper_size`: `a4` (default) or `letter`
  - `top`, `right`, `bottom`, `left`: numeric margin values in selected unit
  - defaults in this repo are `1.5` for every side (metric A4)
- These styling controls apply to PDF generation paths.
- Defaults are metric:
  - paper size: `a4`
  - units: `cm`
  - margins: `1.5` all around
- U.S. profile examples can switch to US units with:

  ```yaml
  margins:
    unit: in
    paper_size: letter
    top: 1.0
    right: 1.0
    bottom: 1.0
    left: 1.0
  ```
- `References` placement behavior:
  - If any source markdown file contains a heading matching `References` (case-insensitive), the build inserts a `<div id="refs"></div>` anchor immediately after that heading in the prepared markdown pipeline, so Pandoc places the bibliography there.
  - If no such heading exists, Pandoc appends the bibliography at the end of the document.
  - The behavior is implemented while concatenating sources: `scripts/prepare_markdown_sources.py` builds `$(PROFILE_CACHE_DIR)/<profile>_sources.md` and normalizes it before handing it to Pandoc.
- Figure behavior in `scripts/prepare_markdown_sources.py` is profile-driven:
  - `placement=pages` (default): figure markdown is extracted from the manuscript sources and added after references, with one `\clearpage` between figures and default heading text (`Fig. 1`, `Fig. 2`, ...; supplementary figures are placed after main figures as `Fig. S1`, ...). Supplementary figures are prefixed with a `## Supplementary Information` heading.
  - `placement=inline`: extracted figure blocks are injected at `<div id="<placeholder_id>"></div>`, then removed from source locations.
  - `placement=captions_page`: creates a dedicated `## Figure Captions` page with one plain caption line per figure (no bullets), then appends each figure on successive pages with label-only titles (`Fig. X.`) and image-only blocks (no repeated caption under the image). Supplementary figures are grouped after a `## Supplementary Information` heading.
  - captions in `pages`/`inline` modes are generated as `**Fig. X.**` / `**Fig. S1.**`; underlying image elements continue to carry their source alt text.
- `edgecases` (optional):
  - `unknown_cite`
  - `manual_cite`
  - `malformed_table`

Example external-repo wiring:

```yaml
default_profile: my_ms
profiles:
  my_ms:
    manuscript_sources:
      - /path/to/other-repo/manuscript/text/main.md
      - /path/to/other-repo/manuscript/text/figures.md
    lint_sources:
      - /path/to/other-repo/manuscript/text/main.md
      - /path/to/other-repo/manuscript/text/figures.md
    bibliography: /path/to/other-repo/references/refs.yaml
    csl: /path/to/other-repo/csl/journal-style.csl
    journal: Journal Name
    csl_search_dirs:
      - /path/to/other-repo/csl
      - csl
    output_dir: dist
    output_stem: manuscript
    page_numbers: lower_right
    line_spacing: single
    line_numbering: continuous
    figures:
      placement: captions_page
      caption_position: top
      placeholder_id: figures
    margins:
      unit: cm
      paper_size: a4
      top: 1.5
      right: 1.5
      bottom: 1.5
      left: 1.5
```

## CSL Search and Sourcing by Journal

Search for matching styles:

```bash
make csl-search JOURNAL="Oikos"
```

Resolve a style path (local-first, otherwise download best Zotero match into `csl/`):

```bash
make csl-source JOURNAL="Ecology Letters"
```

Optional destination override:

```bash
make csl-source JOURNAL="Ecology Letters" CSL_DEST_DIR="path/to/csl"
```

## Quality Gates

Main profile:

```bash
make validate-config
make check
```

Fixture profile:

```bash
make check-fixture
make check-fixture-guards
make fixture-contract-check
make wsl-smoke
```

`check-fixture-guards` asserts expected failures for:
- unknown cite keys
- manual author-year citations
- malformed Markdown tables

`check-fixture` now includes a lightweight fixture contract check (`scripts/fixture_golden_check.py`) that verifies:
- DOCX structure includes expected table and image counts
- PDF remains parseable and contains expected marker headings/text

Contract source:
- defaults to `testbed/expected/golden_contract.yaml`
- can be overridden per profile via `golden_contract` in `settings/build.yaml` (active) or `settings/fixture.yaml` (fixture)

## Reproducibility and Diagnostics

Generate build manifests:

```bash
make manifest
make fixture-manifest
make show-manifest
```

Manifest outputs:
- `dist/<profile-root>/manuscript_build_manifest.json` (active profile)
- `dist/fixture/fixture_manuscript_build_manifest.json` (fixture profile)

Collect diagnostics bundles (useful for CI failures and local triage):

```bash
make diagnose
make fixture-diagnose
```

Default diagnostics root:
- `dist/diagnostics/<timestamp>_<profile>/`
- includes metadata, profile snapshot, manifest copy (if present), source excerpts, and logs

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`

Jobs:
- `guard-tests`: config validation + lint/audit/negative-guard checks
- `build-main`: build active profile outputs + manifest + upload artifacts
- `build-fixture`: build fixture outputs + manifest + contract checks + upload artifacts
- both build jobs collect and upload diagnostics bundles when failures occur

Dependency caching:
- CI uses cached apt package installs through `awalsh128/cache-apt-pkgs-action` to reduce repeated provisioning time.
