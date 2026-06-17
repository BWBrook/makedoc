# Plan: CPE Structured DOCX Import Preflight Audit

## Intent

Use Goal 011's structured preflight JSON to measure how the current
simple-prose-only importer policy behaves on the canonical CPE manuscript
source.

## Steps

1. Preflight makedoc repository state.
2. Read CPE `AGENTS.md`, then preflight CPE repository state.
3. Read current makedoc import/operator context.
4. Run structured preflight against CPE canonical `manuscript/text/main.md`.
5. Store raw JSON and derived summaries under `/tmp/makedoc-goal012-cpe-preflight/`.
6. Parse status, block counts, refusal reason counts, and refusal references.
7. Record evidence in Goal 012 docs/log without copying CPE prose.
8. Write a concise durable audit note.
9. Run validation.
10. Wake the orchestrator and stop.

## Expected Outcome

Expected outcome: the whole canonical CPE source should be `REFUSED` because it
contains normal manuscript structure such as headings and citations.

A useful secondary outcome is quantifying how many blocks are already eligible
simple prose, which informs whether future controlled excerpt-based trials are
worth pursuing.
