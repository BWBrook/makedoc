# Fixture Expectations

This folder documents behavioral expectations for the synthetic manuscript fixture.

## Current Expectations
- `make check-fixture` succeeds on a properly provisioned environment.
- `make check-fixture-guards` succeeds by asserting expected failures on edge-case fixtures.
- `make fixture-contract-check` succeeds against the golden contract file.
- `make fixture-all` produces:
  - `dist/testbed/fixture_manuscript.pdf`
  - `dist/testbed/fixture_manuscript.docx`
  - `dist/testbed/build_manifest.json`
- `make fixture-refs-audit` reports:
  - unknown keys: `0`
- Figure anchors are present in generated output for:
  - `fig-fixture-main`
  - `fig-fixture-richness`
  - `fig-fixture-s1`
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
- Per-profile override path can be set in `settings/build.yaml` via `golden_contract`.

## Notes
- This fixture is synthetic by design; textual content is not semantically important.
- Update this file when fixture scope or acceptance conditions change.
