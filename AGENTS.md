# AGENTS.md

## Purpose

`makedoc` is a config-driven manuscript build system. It generates journal-submission PDF and DOCX outputs from Markdown manuscript sources, figure assets, bibliography YAML, and CSL styles.

This repository has two jobs:

1. Maintain the build system itself (`Makefile`, `scripts/`, `settings/`, docs).
2. Act as the build engine for external manuscript repositories via profile configs.

The default in-repo input is the synthetic regression fixture under `testbed/`.

## First Reads

Before changing anything substantial, read these in order:

1. `README.md`
2. `docs/plan.md`
3. `docs/builder_notes.md`
4. `docs/makedoc_primer_for_agents.md`

If the task is about external manuscript onboarding or road-testing another repo, `docs/makedoc_primer_for_agents.md` is mandatory reading.

## Repo Layout

- `Makefile`: canonical entrypoint for builds, checks, scaffolding, dependency helpers, and diagnostics.
- `scripts/`: profile resolution, source preparation, lint/audit checks, layout normalization, diagnostics, fixture checks.
- `settings/build.yaml`: active/default profile config.
- `settings/fixture.yaml`: dedicated fixture/regression profile config.
- `testbed/`: synthetic fixture manuscript, figures, references, expected contract data.
- `docs/`: plan, builder notes, onboarding docs, primer for external-repo agents.

## Core Rules

### 1. External-path mode only

For real manuscripts, this project standardizes on external-path mode.

- Manuscript content stays in its own repository.
- `makedoc` consumes it via `CONFIG=/abs/path/to/other-repo/settings/build.yaml`.
- Do not introduce copy/sync workflows that mirror manuscript files into `makedoc`.

### 2. External relative paths are now safe

For external configs:

- relative profile paths resolve from the external config file directory
- relative figure image `src` paths inside manuscript Markdown resolve from the Markdown file they appear in
- absolute paths remain preferred when teams want maximum explicitness across tools and scripts

### 3. Do not parallelize top-level Make runs

Do not run `make check` and `make check-fixture` in parallel. The current build still uses shared scratch/output locations such as `.cache/latex` and `dist/`, so concurrent top-level invocations can interfere with one another.

Run them sequentially:

```bash
make check
make check-fixture
```

### 4. Keep fixture protections healthy

The fixture is not disposable demo content. It is the regression contract for the build system.

If you change build behavior, update:

- relevant scripts
- the fixture config or fixture content if needed
- tests and docs

and rerun the appropriate checks.

## Canonical Commands

### Main checks

```bash
make validate-config
make check
make all
```

### Fixture checks

```bash
make check-fixture
make check-fixture-guards
make fixture-contract-check
```

### Targeted regressions

```bash
make test-output-routing
make test-figure-modes
make test-author-injection
```

### Diagnostics and manifests

```bash
make manifest
make fixture-manifest
make show-manifest
make diagnose
make fixture-diagnose
```

### External manuscript build

```bash
CONFIG=/abs/path/to/other-repo/settings/build.yaml make validate-config
CONFIG=/abs/path/to/other-repo/settings/build.yaml make check
CONFIG=/abs/path/to/other-repo/settings/build.yaml make all
```

If the external config has multiple profiles, select one with `PROFILE=<name>`.

## When You Change Something

### If you modify source-prep, figure placement, references, authors, or layout behavior

Run, at minimum:

```bash
make test-author-injection
make test-figure-modes
make check
make check-fixture
```

### If you modify output routing or profile resolution

Run, at minimum:

```bash
make test-output-routing
make validate-config
make check
make check-fixture
```

### If you modify docs only

Read for consistency:

- `README.md`
- `docs/makedoc_primer_for_agents.md`

Update both when behavior or policy changes.

## External Manuscript Policy

When road-testing an external manuscript repo:

1. Validate config first.
2. Run draft profile before strict/submission profile if both exist.
3. Treat manuscript-repo content problems and `makedoc` pipeline problems separately.

Examples of manuscript-repo issues:

- malformed markdown tables
- unresolved or manual citations
- missing or broken figure paths
- malformed bibliography YAML

Examples of `makedoc` issues:

- incorrect path resolution behavior
- bad figure ordering or placement
- broken profile resolution
- DOCX or PDF normalization regressions

Do not silently edit an external manuscript repository unless the user asked you to edit it too.

## Bibliography Contract

`makedoc` expects a Pandoc-style YAML bibliography with a top-level `references:` list.

Best practice:

- each entry has both `id` and `citation-key`
- those values match the in-text `@citekey`

The filename is not important; the YAML structure is.

## Notes for Future Agents

- Default profile uses `testbed/` and should remain runnable in isolation.
- `docs/makedoc_primer_for_agents.md` is the canonical onboarding document for agents working in manuscript repos.
- If you harden the external workflow, update the primer at the same time.
- If a user asks for a road test against another repo, preserve a clear distinction between fixing `makedoc` and fixing the target manuscript repository.

## Done Criteria

For most code changes, "done" means:

1. relevant files updated
2. relevant checks run successfully
3. docs updated if behavior or policy changed
4. final response includes what changed, what was verified, and any remaining risks
