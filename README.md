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
- `minimal`: build/check essentials for this repo (`pandoc`, `xelatex`, `python3-yaml`, `ripgrep`, etc.)
- `full`: `minimal` plus heavier optional tools (`libreoffice`, broader TeX extras, hunspell locales, `poppler-utils`)

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
make check
make all
ls -lh dist/
```

Default outputs:
- `dist/manuscript.pdf`
- `dist/manuscript.docx`

Fixture outputs:
- `dist/testbed/fixture_manuscript.pdf`
- `dist/testbed/fixture_manuscript.docx`

## Build Profiles (YAML-Driven)

Build inputs are defined in `settings/build.yaml`.

Current profile layout:
- `default`: active profile used by `make all` and `make check`
- `fixture`: dedicated regression profile used by fixture checks/guard tests

Useful commands:

```bash
make profiles
make profile-show
make PROFILE=fixture all
make PROFILE=fixture check
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
  PROFILE_APPEND=1 \
  PROFILE_SET_DEFAULT=1
```

## Config Schema

Each profile supports:

- `manuscript_sources`: ordered Markdown input files for Pandoc
- `lint_sources`: Markdown files scanned by lint checks
- `bibliography`: YAML bibliography path
- `csl`: CSL file path
- `journal`: optional journal label/metadata
- `csl_search_dirs`: directories scanned by CSL discovery tools
- `output_dir`: output folder
- `output_stem`: output basename (without extension)
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
make check
```

Fixture profile:

```bash
make check-fixture
make check-fixture-guards
make wsl-smoke
```

`check-fixture-guards` asserts expected failures for:
- unknown cite keys
- manual author-year citations
- malformed Markdown tables

`check-fixture` now includes a lightweight fixture golden check (`scripts/fixture_golden_check.py`) that verifies:
- DOCX structure includes expected table and image counts
- PDF remains parseable and contains expected marker headings/text

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`

Jobs:
- `guard-tests`: lint/audit/negative-guard checks
- `build-main`: build active profile outputs + upload artifacts
- `build-fixture`: build fixture outputs, run golden checks, upload artifacts

Dependency caching:
- CI uses cached apt package installs through `awalsh128/cache-apt-pkgs-action` to reduce repeated provisioning time.
