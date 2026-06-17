# CPE Structured DOCX Import Preflight Audit

Date: 2026-06-17

## Purpose

Record the structured DOCX-import preflight result for the canonical CPE
manuscript source without copying manuscript prose into tracked makedoc docs.

This is an evidence note, not importer hardening and not manuscript adoption.

## Evidence

Raw temporary evidence was written under:

```text
/tmp/makedoc-goal012-cpe-preflight/
```

Files:

```text
/tmp/makedoc-goal012-cpe-preflight/cpe-main-preflight.json
/tmp/makedoc-goal012-cpe-preflight/cpe-main-preflight-summary.json
/tmp/makedoc-goal012-cpe-preflight/cpe-main-refusal-refs.json
```

The audited source path was:

```text
/Users/bwbrook/papers/cpe_time_to_extinction/manuscript/text/main.md
```

No CPE prose, title text, heading text, citation text, or figure caption text
is copied into this note.

## Result

Overall status:

```text
REFUSED
```

Counts:

| Metric | Count |
| --- | ---: |
| total blocks | 48 |
| eligible blocks | 23 |
| refused blocks | 25 |

Refusal reasons:

| Reason | Count |
| --- | ---: |
| unsupported Markdown heading | 17 |
| unsupported Markdown Pandoc citation | 8 |

The whole canonical CPE source is correctly unsafe for whole-file
`revised-candidate` under the current simple-prose-only importer policy.

## Refusal References

Line references only; no source prose is recorded.

Heading refusals:

```text
block 1 line 1
block 3 line 5
block 5 line 9
block 7 line 13
block 10 line 19
block 15 line 29
block 21 line 41
block 27 line 53
block 32 line 63
block 34 line 67
block 36 line 71
block 38 line 75
block 40 line 79
block 42 line 83
block 44 line 87
block 46 line 91
block 48 line 95
```

Pandoc citation refusals:

```text
block 9 line 17
block 16 line 31
block 17 line 33
block 19 line 37
block 20 line 39
block 23 line 45
block 24 line 47
block 30 line 59
```

## Product Finding

The structured preflight report gives the expected real-manuscript answer:
whole-file DOCX revision import remains unsafe for canonical manuscript
sources because normal manuscript structure is present.

The 23 eligible blocks show that controlled simple-prose excerpts remain a
plausible path for future approved trials, but only as isolated excerpts copied
to temporary evidence locations and reviewed by a human. The current tool
should not be used directly on the whole canonical CPE source.

## Recommendation

Keep the importer conservative.

Recommended next importer strategy:

1. Keep whole-file canonical manuscript import refused.
2. Preserve `preflight --format json` as the operator/agent decision surface.
3. If further work is desired, run a later explicit goal for a prose-excerpt
   selection workflow that reports eligible ranges and lets a human choose
   approved excerpts without copying prose into tracked docs by default.
4. Do not add support for headings, citations, figures, tables, references, or
   other manuscript structures until there is a specific approved policy and
   fixture set for each structure.

CPE branch-fate recommendation: preserve the existing local CPE pilot branch
until this audit is reviewed. Cleanup, disposal, or manuscript-side
publication should be a separate explicit goal.
