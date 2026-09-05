# Makedoc Successor Handover

Updated: 2026-09-05

This is a cold-start briefing, not a project history. Verify live Git state and
current instructions before acting.

## Product Promise

Makedoc is Barry Brook's private, config-driven alternative to Overleaf for
scientific manuscripts. Its primary job is to turn Markdown manuscript sources,
figures, author metadata, a Pandoc-style YAML bibliography, and a CSL style into
submission-ready PDF and DOCX files.

The intended workflow is flexible but regimented:

- each manuscript remains in its own repository;
- Makedoc supplies the reusable build engine;
- a manuscript-local YAML profile defines inputs and output policy;
- validation catches consequential source/configuration problems;
- PDF and DOCX outputs are inspected as real submission artefacts.

Everything else must earn its complexity against that promise.

## Current State

Immediately before this handover was written, `/Users/bwbrook/work/makedoc`
was clean on `main...origin/main` at `7749004` (`Decompose profile resolution
helpers`). Recheck rather than assuming this remains current.

The core workflow is working and covered by a synthetic regression fixture. It
supports:

- YAML build profiles and external manuscript paths;
- config-relative input paths and source-relative figure paths;
- Markdown preparation, author injection, bibliography/CSL handling, and
  citation/reference checks;
- PDF and DOCX generation through Pandoc/LaTeX;
- page, margin, spacing, line-numbering, output-routing, and figure-placement
  controls;
- targeted diagnostics, manifests, and regression checks;
- optional, default-off outbound review markup that renders visible editorial
  traces in PDF/DOCX.

The synthetic `testbed/` is the in-repo regression contract. Real manuscript
content must not be copied into this repository.

## Decisions Already Made

### Keep Makedoc focused

Makedoc owns source-driven manuscript preparation and document building. It
does **not** own DOCX comments, native Word Track Changes, or DOCX-to-Markdown
reconciliation. Those belong to the separate Wordmark project. See
`docs/docx_review_boundary.md`.

The retained `review_markup` feature is outbound only. Do not revive the
deleted DOCX importer or blur this boundary without a new substantive product
decision with Barry.

### Prefer a lean private tool

This repository currently serves Barry, not a public compatibility ecosystem.
Do not preserve obsolete paths for hypothetical consumers, add ceremonial
ledgers, or grow exhaustive tests around low-consequence edge cases. Git is the
archive.

The recent simplification removed about 6,300 lines of DOCX-import machinery
and its historical goal packets (`6810123`), deleted redundant dependency
compatibility paths (`56fa410`), and decomposed the profile resolver without
changing its outputs (`7749004`). The remaining large source-preparation code
was judged coherent enough to leave alone until real usage reveals a concrete
maintenance problem.

Further indiscriminate trimming is unlikely to pay. Develop from observed
workflow friction now.

## Working Contract With Barry

> Rigour at the scientific decision boundary; proportional engineering
> everywhere else.

Use Barry's attention selectively. Consult him when a choice could materially
change scientific validity, manuscript integrity, product direction, public or
irreversible action, or a consequential trade-off. Make routine, reversible,
testable engineering decisions independently.

Deliver the smallest coherent end-to-end capability that answers the current
question. Prespecify tests that could change the decision, protect source data
and Git state, perform one focused self-review/repair pass, and stop when more
work would mainly add polish. State residual uncertainty openly.

Two personal skills express this operating style and should be used when
relevant:

- `/Users/bwbrook/.codex/skills/twilight-laboratory/SKILL.md` for substantial
  scientific or research-development programmes, staged evidence, human review
  boundaries, and meaningful reporting horizons;
- `/Users/bwbrook/.codex/skills/kill-your-darlings/SKILL.md` for audits or
  simplification when features, checks, compatibility, or scaffolding are
  outgrowing present value.

Do not invoke either as ceremony. Apply only the parts needed for the task.

## Immediate Direction

The next high-value tranche is a real-manuscript submission-workflow proof.
Barry is selecting a substantially advanced manuscript that is representative
enough to expose genuine issues in citations, references, figures, tables,
profiles, and rendered outputs.

Once Barry identifies the manuscript:

1. Read that repository's instructions and report its exact Git state before
   mutation.
2. Keep manuscript changes separate from Makedoc engine changes.
3. Run the ordinary author path: configuration review, `validate-config`, draft
   build/check, submission-profile build/check where present, then visual
   inspection of PDF and DOCX.
4. Classify findings as manuscript-specific defects, onboarding/documentation
   friction, genuine Makedoc defects, worthwhile missing capability, or exotic
   cases that should remain unsupported.
5. Fix only clear high-value problems inside the authority Barry grants for the
   pilot. Produce a short ranked development recommendation from observed use.

Do not manufacture a torture suite or start speculative framework work before
the manuscript exposes a need. Review markup is proven well enough for now;
Word-template tuning, Zotero helpers, and Make concurrency work are
possibilities, not approved priorities.

## Bootstrap

Read, in order:

1. `AGENTS.md`
2. this handover
3. `README.md`
4. `docs/makedoc_primer_for_agents.md`
5. `docs/docx_review_boundary.md`

Use `docs/plan.md` and `docs/builder_notes.md` as detailed historical and
technical references, not as an automatically approved roadmap.

Start with:

```bash
git status --short --branch
git rev-parse --short HEAD
git log -10 --oneline
make validate-config
```

For an engine change, select checks by the changed risk. The usual broad local
gate is:

```bash
make check
make check-fixture
```

Run top-level Make invocations sequentially because shared `.cache/` and
`dist/` paths can interfere. For a real external manuscript, follow the command
forms and repository-boundary rules in `docs/makedoc_primer_for_agents.md`.

Visual success matters: a green build does not establish that a PDF or DOCX is
submission-ready. Inspect the rendered artefacts and keep observed output
quality separate from assumptions about the pipeline.
