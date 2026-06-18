# Goal: Synthetic End-to-End Review Loop Proof

## Objective

Prove the controlled operator workflow from a revised DOCX import candidate
through visible review-markup rendering using only synthetic fixture material
inside `/Users/bwbrook/work/makedoc`.

The goal answers whether an operator can take a simple revised DOCX, generate
Markdown review tokens, build review-marked PDF/DOCX outputs, and inspect
evidence that imported changes are visible and traceable.

## Scope

Work only inside:

```text
/Users/bwbrook/work/makedoc
```

Do not touch CPE or any other external repository.

## Required Proof

The proof must exercise:

1. synthetic original Markdown with simple prose only;
2. synthetic revised DOCX generated in a temporary workspace;
3. `scripts/import_docx_review_markup.py revised-candidate` writing a separate
   candidate Markdown file with `{++ ++}`, `{-- --}`, and `{~~ ~> ~~}` tokens;
4. review-markup source preparation with `review_markup.enabled: true`;
5. generated PDF and DOCX evidence containing visible/structural bracketed
   review markers.

## Non-Goals

- Real manuscript trials.
- CPE reads or writes.
- Importer support broadening.
- Support for headings, citations, lists, tables, figures, comments,
  formatting-only changes, true Word Track Changes import, or full
  round-tripping.
- Changes to review-markup token syntax or default-off semantics.
- Generated artifact force-adds.
- Staging, commits, pushes, fetches, pulls, resets, cleans, stashes, rebases,
  branch switches, or dependency installs.
- Goal 016.

## Acceptance Criteria

- A rerunnable proof target exists.
- The proof writes generated evidence under an ignored output path.
- Existing importer tests and review-markup tests still pass.
- Operator-facing docs explain the proof without implying production readiness.
- Makedoc changes remain unstaged for orchestrator review.
