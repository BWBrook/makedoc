# Synthetic Manuscript Testbed Workplan

Last updated: 2026-02-13
Status: implemented (phase-one fixture baseline)

## Purpose
Create a stable, low-complexity fixture manuscript for CI and regression testing so pipeline behavior can be validated independently of bespoke scientific manuscript content.

## Why This Workstream
- Real manuscript drafts contain domain-specific edge cases that can blur whether failures are tooling regressions or content-specific issues.
- A controlled fixture allows deterministic tests for layout components (citations, equations, figures, tables, supplementary elements) and future pipeline changes.
- CI can stay fast and diagnostic by failing on known, intentional test conditions.

## Scope
In scope:
- One synthetic manuscript source with placeholder prose
- Small synthetic bibliography + CSL style wiring
- Dummy figure assets (main + supplementary)
- Dummy table and equation blocks
- Baseline expectations for PDF and DOCX builds
- CI checks that assert fixture pipeline integrity

Out of scope (initially):
- Journal-specific visual perfection
- Exhaustive typography checks
- Multi-journal template matrix

## Proposed Fixture Layout
```text
testbed/
  manuscript/
    text/
      fixture_main.md
      fixture_figures.md
    figures/
      fig1_dummy.png
      fig2_dummy.png
      figS1_dummy.png
  references/
    fixture_refs.yaml
  csl/
    fixture_style.csl
  expected/
    README.md
```

## Minimum Feature Matrix
1. Citations:
- single citation
- multi-citation group
- narrative and parenthetical forms

2. Math:
- inline math
- display equation

3. Tables:
- markdown table with math in cells

4. Figures:
- two main figures with anchors
- one supplementary figure with anchor
- in-text cross-reference links to anchors

5. Build outputs:
- PDF + DOCX generated from multi-source input

## Implementation Milestones
1. Create synthetic content files and assets. `Done`
2. Add Makefile variables/targets for fixture builds. `Done`
3. Add fixture-specific lint and refs-audit checks. `Done`
4. Extend CI to run both primary manuscript checks and fixture checks. `Done`
5. Document expected behavior and known limitations. `Done`

## Implemented Artifacts
- Fixture manuscript sources:
  - `testbed/manuscript/text/fixture_main.md`
  - `testbed/manuscript/text/fixture_figures.md`
- Fixture figures:
  - `testbed/manuscript/figures/fig1_dummy.png`
  - `testbed/manuscript/figures/fig2_dummy.png`
  - `testbed/manuscript/figures/figS1_dummy.png`
- Fixture references and style:
  - `testbed/references/fixture_refs.yaml`
  - `testbed/csl/fixture_style.csl`
- Fixture expectations doc:
  - `testbed/expected/README.md`
- Make targets:
  - `fixture-pdf`, `fixture-docx`, `fixture-all`
  - `fixture-lint`, `fixture-refs-audit`, `check-fixture`
- CI integration:
  - `.github/workflows/ci.yml` runs `make check` and `make check-fixture`

## Acceptance Criteria
- `make check` continues to pass for the real manuscript.
- New fixture target (for example `make check-fixture`) passes in CI.
- Fixture includes all minimum feature matrix components.
- Fixture failures produce clear, actionable diagnostics.

## Suggested Next Commands (future work)
- `make fixture-pdf`
- `make fixture-docx`
- `make fixture-check`
