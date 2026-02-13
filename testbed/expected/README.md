# Fixture Expectations

This folder documents behavioral expectations for the synthetic manuscript fixture.

## Current Expectations
- `make check-fixture` succeeds on a properly provisioned environment.
- `make fixture-all` produces:
  - `dist/testbed/fixture_manuscript.pdf`
  - `dist/testbed/fixture_manuscript.docx`
- `make fixture-refs-audit` reports:
  - unknown keys: `0`
- Figure anchors are present in generated output for:
  - `fig-fixture-main`
  - `fig-fixture-richness`
  - `fig-fixture-s1`

## Notes
- This fixture is synthetic by design; textual content is not semantically important.
- Update this file when fixture scope or acceptance conditions change.
