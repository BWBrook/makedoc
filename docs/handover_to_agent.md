# Handover To New Agent

Last updated: 2026-03-06
Primary repo path: `/home/bwbrook/work/makedoc`

## What This Repo Is

`makedoc` is a config-driven manuscript build system for generating journal-submission PDF and DOCX outputs from:

- Markdown manuscript sources
- figure assets
- Pandoc-style YAML bibliography
- CSL style files
- optional author metadata YAML

The repo has two working modes:

1. maintain the build system itself
2. build external manuscript repositories via absolute-path profile configs

The in-repo default build target is the synthetic regression fixture under `testbed/`.

## Start Here

Read these files first:

1. `AGENTS.md`
2. `README.md`
3. `docs/plan.md`
4. `docs/builder_notes.md`
5. `docs/makedoc_primer_for_agents.md`

That sequence gives you:

- repo operating rules
- canonical commands
- completed phases
- implementation evidence
- the external-manuscript onboarding contract

## Current Repo State

- Active repo path is `/home/bwbrook/work/makedoc`
- There is an uncommitted repo-local `AGENTS.md`
- This handover note is also currently uncommitted
- At the time of writing, `git status --short` shows only:
  - `?? AGENTS.md`
  - `?? docs/handover_to_agent.md`

Recent commit tip:

- `32bbcdc Updated primer`

Recent important commits:

- `5269ba5 Add author/page-flow defaults and strengthen manuscript prep tests`
- `8e937cc Split fixture config/output and refine captions-page figure rendering`
- `7e0c5e7 Add layout diagnostics and docs for line numbers and margins`
- `17a6a2b feat: normalize source merge for references placement and hardening`

## What Is Working

Core build system is in a strong state.

Implemented and documented:

- profile-driven build configs
- active/fixture profile split
- output routing to `dist/<profile-root>/`
- bibliography anchoring at `## References`
- author metadata injection with fallback after title
- page-number, line-spacing, line-numbering, and margin controls
- figure placement modes:
  - `pages`
  - `inline`
  - `captions_page`
- diagnostics and build manifests
- Ubuntu/WSL dependency installer
- profile scaffolding helper
- synthetic fixture + golden/guard checks

Canonical checks that should pass in this repo:

```bash
make validate-config
make check
make check-fixture
make check-fixture-guards
```

## Important Behavioral Rules

### 1. External-path mode only

For real manuscripts, the system is intended to build other repos by reference.

- manuscript content stays in its own repo
- `makedoc` consumes it via `CONFIG=/abs/path/to/other-repo/settings/build.yaml`
- do not introduce copy/sync workflows

### 2. External path semantics

For external manuscript repos:

- relative profile paths resolve from the external config file directory
- relative figure image `src` paths in markdown resolve from the Markdown file they appear in
- absolute paths still work and remain the clearest option when multiple tools touch the same repo

### 3. Do not parallelize top-level Make runs

Do not run:

```bash
make check & make check-fixture
```

at the same time.

The build still uses shared scratch/output locations such as `.cache/latex` and `dist/`, so concurrent top-level invocations can interfere with one another. Run the main checks sequentially.

## Most Relevant Recent Work

### External manuscript primer

`docs/makedoc_primer_for_agents.md` was written as the onboarding contract for agents working in other manuscript repositories.

It now explicitly covers:

- external-path-only policy
- config-relative profile paths
- non-required naming conventions (`main.md` and `refs.yaml` are conventions only)
- draft vs submission lint policy
- canonical bibliography file guidance
- source-relative image path guidance in external figure markdown

### Real-world road test

We road-tested the system against:

- `/home/bwbrook/papers/insurance_hypothesis/paper`

That exercise was valuable because it exposed real-world edge cases rather than synthetic ones.

We fixed issues in the manuscript repo, not in `makedoc`, including:

- figure image paths that did not match the manuscript's own source-relative layout
- malformed markdown table cell with raw `|`
- title heading cleanup
- DOCX-math warning caused by `\Bigl` / `\bigl`

After those fixes, both draft and submission profiles built cleanly.

Road-test commands that passed:

```bash
CONFIG=/home/bwbrook/papers/insurance_hypothesis/paper/settings/build.yaml make validate-config
CONFIG=/home/bwbrook/papers/insurance_hypothesis/paper/settings/build.yaml make check
CONFIG=/home/bwbrook/papers/insurance_hypothesis/paper/settings/build.yaml make all
CONFIG=/home/bwbrook/papers/insurance_hypothesis/paper/settings/build.yaml PROFILE=ih_submission make validate-config
CONFIG=/home/bwbrook/papers/insurance_hypothesis/paper/settings/build.yaml PROFILE=ih_submission make check
CONFIG=/home/bwbrook/papers/insurance_hypothesis/paper/settings/build.yaml PROFILE=ih_submission make all
```

This also confirmed that the current primer guidance is mostly sound.

## Features Still Being Tweaked Or Worth Improving

These are not blockers, but they are the most natural next improvements.

### 1. Better concurrency hygiene in the Makefile

Current state:

- top-level Make invocations should be run sequentially because shared `.cache` files can race

Potential improvement:

- refactor cache/intermediate generation so `make check` and `make check-fixture` are safe under concurrent invocation

### 2. More direct Zotero export onboarding

Current state:

- bibliography contract is documented
- Pandoc YAML with `references:` is expected

Potential improvement:

- add a helper script to convert Zotero `CSL JSON` into repo-compatible YAML bibliography format

### 3. Word-template tuning

Still explicitly out of scope in the main plan:

- journal-specific Word style template (`reference.docx`) tuning

This may become the next major frontier once the current build system is considered stable enough.

## Known Sharp Edges

- Panel-level figure references (for example `1A`, `1B`) still link to whole-figure anchors by design.
- Relative profile paths are now config-relative and relative markdown image paths are source-relative; prefer absolute paths only when you want extra explicitness across tools.
- The default fixture remains the regression contract; do not casually edit it without rerunning fixture checks.

## Canonical Commands

Main repo checks:

```bash
make validate-config
make check
make all
```

Fixture checks:

```bash
make check-fixture
make check-fixture-guards
make fixture-contract-check
```

Targeted regressions:

```bash
make test-output-routing
make test-figure-modes
make test-author-injection
```

Diagnostics:

```bash
make manifest
make fixture-manifest
make show-manifest
make diagnose
make fixture-diagnose
```

## Suggested Working Pattern For The Next Agent

When you start a new session:

1. read `AGENTS.md`
2. read `docs/handover_to_agent.md`
3. read `docs/plan.md`
4. skim `docs/builder_notes.md`
5. run:

```bash
git status --short
git log --oneline -n 10
make validate-config
```

If the task touches build behavior, then also run:

```bash
make test-author-injection
make test-figure-modes
make check
make check-fixture
```

Run them sequentially, not in parallel.

## If You Need To Explain The Project Quickly

Short version:

`makedoc` is a reusable manuscript-build engine. It uses YAML profiles to point at manuscript assets, prepares markdown with author/reference/figure normalization, renders PDF + DOCX via Pandoc, and protects itself with a synthetic fixture plus targeted regression tests.
