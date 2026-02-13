# Fixture Expectations

This folder documents behavioral expectations for the synthetic manuscript fixture.

## Current Expectations
- `make check-fixture` succeeds on a properly provisioned environment.
- `make check-fixture-guards` succeeds by asserting expected failures on edge-case fixtures.
- `make fixture-contract-check` succeeds against the golden contract file.
- `make fixture-all` produces:
  - `dist/fixture/fixture_manuscript.pdf`
  - `dist/fixture/fixture_manuscript.docx`
  - `dist/fixture/fixture_manuscript_build_manifest.json`
- `make fixture-refs-audit` reports:
  - unknown keys: `0`
- Figure anchors are present in generated output for:
  - `fig-fixture-main`
  - `fig-fixture-richness`
  - `fig-fixture-s1`
- Figures are rendered on dedicated pages by default with `Fig. 1`, `Fig. 2`, `Fig. S1` labels.
- Edge-case fixtures produce expected outcomes:
  - unknown citation key -> refs-audit failure
  - manual author-year citation -> lint failure
  - malformed table row -> lint failure

## Golden Contract
- Contract file: `testbed/expected/golden_contract.yaml`
- Contract keys currently tracked:
  - `expect_tables`
  - `expect_drawings`
  - `min_pdf_pages`
  - `required_text`
- Per-profile override path can be set via `golden_contract` in `settings/build.yaml` (active profile) or `settings/fixture.yaml` (fixture profile).

## Notes
- This fixture is synthetic by design; textual content is not semantically important.
- Update this file when fixture scope or acceptance conditions change.
