# Log: External Review Markup Adoption Playbook

## 2026-06-14 - Execution Started

Status: in progress.

Executor: `draftsman`.

Starting state confirmed in `/Users/bwbrook/work/makedoc`:

```text
pwd
/Users/bwbrook/work/makedoc
```

```text
git status --short --branch
## main...origin/main
```

```text
git rev-parse --short HEAD
e4be37c
```

```text
git log -1 --oneline
e4be37c Make review markup deletions PDF-readable
```

CPE `AGENTS.md` was read before any CPE inspection.

Starting state confirmed in `/Users/bwbrook/papers/cpe_time_to_extinction`:

```text
pwd
/Users/bwbrook/papers/cpe_time_to_extinction
```

```text
git status --short --branch
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

```text
git rev-parse --short HEAD
e1b2433
```

Permitted CPE evidence inspection:

```text
git diff --stat -- settings/build.yaml
 settings/build.yaml | 33 +++++++++++++++++++++++++++++++++
 1 file changed, 33 insertions(+)
```

Read only these CPE files after `AGENTS.md`:

- `settings/build.yaml`
- `manuscript/text/main_review_markup_probe.md`

The CPE profile includes a dedicated `review_markup_pilot` profile pointing at
`../manuscript/text/main_review_markup_probe.md` and
`../manuscript/text/figures.md`, with `review_markup.enabled: true`, and output
under `../build/review-markup-pilot`.

The CPE pilot source contains the artificial probe:

```text
Pilot-only review-markup probe: {++ inserted pilot text ++}, {-- removed pilot text --}, {~~ old pilot wording ~> revised pilot wording ~~}, and {>> confirm visible review trace output <<}.
```

Canonical CPE source token scan:

```text
rg '\{\+\+|\{--|\{~~|\{>>' manuscript/text/main.md
```

Result: no matches, which is desired.

Existing ignored CPE pilot outputs were observed:

```text
build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.docx
build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf
build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot_build_manifest.json
```

No CPE source files were edited. No CPE build artifacts were regenerated. No
CPE staging, commits, pushes, fetches, pulls, resets, cleans, stashes, rebases,
branch switches, renames, or reconciliation were performed.

## 2026-06-14 - Playbook Implemented And Validated

Status: complete.

Changed makedoc files:

- `docs/review_markup_external_adoption.md`
- `README.md`
- `docs/makedoc_primer_for_agents.md`
- `docs/goals/005-external-review-markup-adoption-playbook/Goal.md`
- `docs/goals/005-external-review-markup-adoption-playbook/Plan.md`
- `docs/goals/005-external-review-markup-adoption-playbook/Runbook.md`
- `docs/goals/005-external-review-markup-adoption-playbook/Log.md`

No engine code, rendering semantics, profile schema, Make targets, tests,
fixtures, or generated artifact policy were changed.

Playbook contents:

- purpose and non-goals for visible Markdown-origin review traces;
- safe external pilot pattern using an isolated profile and isolated pilot
  source;
- authoring rules for additions, deletions, substitutions, and reviewer notes;
- validation checklist with feature check, external profile validation/build
  patterns, ordinary profile checks, canonical token scan, PDF visual
  inspection, and DOCX visible-trace expectations;
- evidence and artifact policy;
- CPE branch disposition decision;
- decision gates for acceptance, manuscript-facing judgment, and possible
  future DOCX-to-Markdown import work.

README and external-agent primer now point to the playbook without duplicating
the full recipe.

Validation:

```text
make test-review-markup
```

Result: passed. This regenerated makedoc's ignored review-markup fixture proof
outputs under `dist/review-markup/` as part of the existing regression target.

```text
git diff --check
```

Result: passed.

No CPE builds were run for Goal 005, and no CPE artifacts were regenerated.

Final makedoc status:

```text
## main...origin/main
 M README.md
 M docs/makedoc_primer_for_agents.md
?? docs/goals/005-external-review-markup-adoption-playbook/
?? docs/review_markup_external_adoption.md
```

Final CPE status:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

Final CPE HEAD:

```text
e1b2433
```

No files were staged. No commits, pushes, fetches, pulls, resets, cleans,
stashes, rebases, dependency installs, generated artifact force-adds, CPE
source edits, CPE artifact regeneration, CPE branch switching, native Word
Track Changes work, DOCX-to-Markdown import work, or Goal 006 work were
performed.

Recommended next step: orchestrator review of the playbook and Goal 005 packet.
If accepted, perform a bounded publication closeout for the makedoc docs/goal
files only, leaving the CPE pilot branch preserved until Barry or the
orchestrator gives an explicit later disposition instruction.
