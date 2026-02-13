# makedoc

Config-driven manuscript build tooling for generating journal-submission outputs (`.pdf` and `.docx`) from Markdown, references, figures, and CSL styles.

This repository now uses a synthetic regression fixture (`testbed/`) as the default build input, so the pipeline is always runnable in isolation.

## Requirements

- Ubuntu (tested on 24.04 LTS)
- `pandoc`
- `xelatex` (via `texlive-xetex`)
- `python3` + `python3-yaml`
- `ripgrep` (used in checks/CI)

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
```

`check-fixture-guards` asserts expected failures for:
- unknown cite keys
- manual author-year citations
- malformed Markdown tables

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`

Jobs:
- `guard-tests`: lint/audit/negative-guard checks
- `build-main`: build active profile outputs + upload artifacts
- `build-fixture`: build fixture outputs + upload artifacts
