# Goal: Text-Only DOCX Revision Import Candidate

## Objective

Turn the Goal 006 feasibility spike into a constrained experimental candidate
generator for the revised-DOCX route.

Given an original simple Markdown/plain-prose file and a revised DOCX, the
tool should write a separate candidate Markdown file containing Makedoc
review-markup tokens for human review.

## Product Stance

This is not round-tripping and not a production importer.

The candidate generator must never overwrite or modify canonical manuscript
sources. It should refuse unsupported Markdown structures rather than implying
that complex DOCX edits can be safely mapped back to source Markdown.

Native Word Track Changes import remains deferred. Preserve the Goal 006
evidence route, but do not harden it in this goal.

## Scope

Authorized path:

- `/Users/bwbrook/work/makedoc`

Forbidden:

- `/Users/bwbrook/papers/cpe_time_to_extinction`
- Chief of Staff
- Goal Composer
- sibling project repositories
- archive material
- unrelated user files

## Required Work

1. Confirm makedoc starts clean at `bba8be2` on `main...origin/main`.
2. Read required context:
   - `AGENTS.md`
   - `README.md`
   - `docs/docx_review_import_spike.md`
   - `docs/review_markup_external_adoption.md`
   - `scripts/import_docx_review_markup.py`
   - `tests/test_import_docx_review_markup.py`
   - Goal 006 packet/log enough to preserve boundaries.
3. Extend `scripts/import_docx_review_markup.py` with a `revised-candidate`
   CLI mode.
4. Extend `tests/test_import_docx_review_markup.py` with focused positive and
   refusal tests.
5. Update `docs/docx_review_import_spike.md` with the Goal 007 prototype
   status, usage shape, limitations, and next decision.
6. Create this Goal 007 packet with `Goal.md`, `Plan.md`, `Runbook.md`, and
   `Log.md`.
7. Validate with the focused script/test commands, `make test-review-markup`,
   `make check`, and `git diff --check`.
8. Leave changes unstaged and wake the orchestrator.

## Required Behavior

CLI shape:

```sh
python3 scripts/import_docx_review_markup.py revised-candidate \
  --original-path path/to/original.md \
  --revised-docx path/to/revised.docx \
  --output path/to/candidate.md
```

The mode should:

- read original simple Markdown/plain prose;
- extract revised DOCX text through the existing revised-DOCX route;
- map paragraph-by-paragraph;
- emit `{++ inserted ++}`, `{-- deleted --}`, and
  `{~~ old ~> new ~~}` tokens;
- preserve blank-line paragraph separation;
- write only the requested separate candidate file;
- refuse paragraph-count mismatches;
- refuse unsupported Markdown structures conservatively;
- refuse if output resolves to the original path;
- refuse to overwrite an existing output file by default;
- avoid partial output on validation failure.

## Non-Goals

- Production importer.
- CPE access or mutation.
- Native Word automation or GUI Word control.
- Dependency installation.
- Native Track Changes hardening.
- Comments, moves, formatting-only changes, tables, citations, figures,
  references, headings, lists, or complex Markdown mapping.
- Outbound review-markup rendering changes.
- `review_markup.enabled`, profile schema, Make build graph, adoption playbook,
  or manuscript workflow changes.
- Goal 008.

## Acceptance Criteria

- The CLI writes a separate candidate Markdown file for simple prose revised
  DOCX input.
- Unsafe input is refused clearly before writing output.
- Existing Goal 006 `revised` and `track-changes` routes still work.
- Focused tests cover positive and refusal behavior.
- The memo and log accurately state the experimental limitations.
- CPE and unrelated repos are untouched.
