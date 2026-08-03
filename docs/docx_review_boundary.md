# DOCX Review Boundary

Status: accepted 2026-08-03

## Decision

Makedoc is a source-driven manuscript builder. It owns Markdown preparation,
bibliography/CSL handling, citation and reference checks, and PDF/DOCX output.
It does not own DOCX comments, native Word Track Changes, or DOCX-to-Markdown
source reconciliation.

Wordmark owns the DOCX review workflow. Use Wordmark to inspect and edit DOCX
review state, collect comments and revisions, and produce guarded source-edit
proposals for human approval.

Makedoc's optional `review_markup` feature is outbound only: Markdown tokens
can be rendered as visible traces in generated PDF/DOCX outputs. That feature
does not create Word Review-pane revisions and should not be treated as a
DOCX import path.

The experimental Makedoc DOCX-import prototype and its synthetic evidence were
retired from the active tree after Wordmark's overlapping, source-aware review
workflow was identified. Their implementation history remains available in
Git; no duplicate holding copy is maintained here.
