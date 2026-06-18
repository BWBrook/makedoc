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

## Goal 013 Eligible Block References

Goal 013 reran the same structured preflight audit after adding
`eligible_blocks_detail` to the JSON report.

Raw and derived evidence was written under:

```text
/tmp/makedoc-goal013-eligible-blocks/
```

Files:

```text
/tmp/makedoc-goal013-eligible-blocks/cpe-main-preflight.json
/tmp/makedoc-goal013-eligible-blocks/cpe-main-preflight-summary.json
/tmp/makedoc-goal013-eligible-blocks/cpe-main-eligible-refs.json
/tmp/makedoc-goal013-eligible-blocks/cpe-main-refusal-refs.json
```

Counts remained unchanged:

| Metric | Count |
| --- | ---: |
| total blocks | 48 |
| eligible blocks | 23 |
| eligible block refs reported | 23 |
| refused blocks | 25 |

Overall status remained:

```text
REFUSED
```

First five eligible references:

```text
block 2 lines 3-3
block 4 lines 7-7
block 6 lines 11-11
block 8 lines 15-15
block 11 lines 21-21
```

Last five eligible references:

```text
block 39 lines 77-77
block 41 lines 81-81
block 43 lines 85-85
block 45 lines 89-89
block 47 lines 93-93
```

Product implication: future excerpt workflows can propose eligible block/line
ranges for human approval without copying manuscript prose by default. Whole
canonical CPE import remains correctly refused.

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

CPE branch-fate recommendation after Goal 013: preserve the existing local CPE
pilot branch through this audit review. Make Goal 014 a separate explicit CPE
branch disposition or cleanup decision; do not combine that with importer
support broadening.

## Goal 014 Pilot Branch Disposition

Goal 014 retired the local CPE pilot branch and worktree side effects after
the review-markup and DOCX-import evidence had been recorded in Makedoc.

Disposition summary:

- confirmed CPE pilot branch `codex/makedoc-review-markup-pilot` had no unique
  commits relative to local `main`;
- restored only `settings/build.yaml` in CPE;
- removed only `manuscript/text/main_review_markup_probe.md`;
- removed ignored pilot generated outputs under `build/review-markup-pilot/`
  when present;
- switched CPE back to local `main`;
- deleted local branch `codex/makedoc-review-markup-pilot` using normal
  non-force branch deletion.

Final CPE state:

```text
## main...origin/main
e1b2433
```

No CPE manuscript prose, review probe text, headings, citations, paragraph
text, or figure captions are copied into this note.
