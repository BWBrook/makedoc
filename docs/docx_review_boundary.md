# DOCX Review Boundary

Status: accepted 2026-08-03

## Decision

Makedoc is a source-driven manuscript builder. It owns Markdown preparation,
bibliography/CSL handling, citation and reference checks, and PDF/DOCX output.
It does not own DOCX comments, native Word Track Changes, or DOCX-to-Markdown
source reconciliation.

No current tool of Barry's owns a DOCX review workflow. Wordmark, the project
that was to provide one, was abandoned on 3 November 2026. Two things replaced
it: scrivmark, which keeps tracked changes and comment threads on the
Markdown, Quarto or LaTeX files that Makedoc builds from, and agents working
directly in Word by computer use when a document must be reviewed there.

Makedoc's optional `review_markup` feature is outbound only: Markdown tokens
can be rendered as visible traces in generated PDF/DOCX outputs. That feature
does not create Word Review-pane revisions and should not be treated as a
DOCX import path.

Makedoc once carried an experimental DOCX-import prototype; it was removed and
is not coming back.
