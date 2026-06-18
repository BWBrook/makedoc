# DOCX Review Import Operator Note

Use `revised-candidate` when you have a simple prose source file and a revised
DOCX, and you want a separate Markdown candidate containing visible Makedoc
review-markup tokens for human review.

This tool is experimental. It is not a production importer, not Word
round-tripping, and not native Track Changes import.

## Preconditions

Use only simple prose paragraphs separated by blank lines.

Do not use this mode on canonical manuscript sources that contain headings,
front matter, thematic breaks, citations, lists, figures, tables, references,
raw HTML, code blocks, or existing review markup. Those structures are
deliberately refused because the tool cannot safely map revised DOCX text back
onto real manuscript Markdown.

Always write to a separate candidate path. Never point `--output` at the
original source.

Human review is required before any candidate text is copied or adapted into a
manuscript source file.

## Workflow

Run preflight on the original Markdown or plain-prose source before attempting
candidate generation:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path path/to/original_simple_prose.md
```

Text is the default human-readable format. For agents or automation, request
structured JSON:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path path/to/original_simple_prose.md \
  --format json
```

Both formats list block counts, eligible simple-prose paragraphs, refused
blocks, line references, refusal reasons, and an overall status. JSON also
includes `eligible_blocks_detail`, a prose-free list of eligible block and line
ranges for future human-approved excerpt selection. Neither format copies
manuscript prose into the report by default.

Preflight exits 0 when the report is produced, even if the source contains
refused blocks. Treat that as a successful safety report, not permission to
work around the refusal.

Only run `revised-candidate` when preflight reports:

```text
Overall status: SAFE_TO_ATTEMPT
```

## Command

Run from the `makedoc` repository:

```sh
python3 scripts/import_docx_review_markup.py revised-candidate \
  --original-path path/to/original_simple_prose.md \
  --revised-docx path/to/revised.docx \
  --output path/to/review_candidate.md
```

By default the command refuses to overwrite an existing output file. Use a new
candidate path for each run unless there is an explicit reason to replace an
older candidate.

## Safe Output Handling

Treat the candidate file as evidence, not source truth.

1. Inspect the full candidate file.
2. Compare it with the original source and the revised DOCX text.
3. Confirm every token reflects an intended edit.
4. Copy or adapt tokens manually only after review.
5. Keep canonical manuscript sources unchanged unless a later explicit goal or
   human decision authorizes adoption.

## Review Checklist

Before accepting any candidate text, check:

- paragraph count and ordering match the original source;
- review tokens are in the intended paragraphs;
- insertions, deletions, and substitutions reflect intended edits;
- scientific meaning is unchanged except for intended revisions;
- unsupported structures were not silently transformed;
- canonical manuscript source was not overwritten.

## Refusal Policy

A refusal is a successful safety outcome.

If the tool refuses a source because it contains a citation, heading, list,
figure, table, front matter, thematic break, code block, raw HTML, existing
review markup, paragraph-count mismatch, or existing output path, do not work
around the refusal by weakening the source. Choose one of these instead:

- simplify the source into a temporary prose-only fixture;
- make the change manually in Markdown;
- open a later, explicitly scoped hardening goal for that structure.

## Real Manuscript Trials

CPE or any other real manuscript trial requires a later explicit goal and
approved example material. Do not run this importer against real manuscript
repositories during ordinary maintenance or publication closeout.

Goal 009 proved that a tiny approved CPE simple-prose excerpt can pass the
current workflow when copied into `/tmp` and reviewed as evidence. That does
not authorize routine manuscript-repo use; it only supports a later explicitly
scoped real-manuscript trial.
