# Goal: CPE Review Markup External Manuscript Pilot

## Objective

Prove the published `review_markup.enabled` workflow against the real external
manuscript repository at `/Users/bwbrook/papers/cpe_time_to_extinction` without
pushing manuscript changes to `main`.

Success means the CPE manuscript can build through `makedoc` using a dedicated
review-markup pilot profile that produces visible DOCX/PDF review traces, while
the existing `draft` and `submission` profiles remain clean and unaffected.

## Why This Matters

Goals 001 and 002 proved the review-markup feature inside `makedoc`'s own
fixture surface. The next question is whether the workflow feels sane when used
from the kind of external manuscript repo it is meant to serve.

`cpe_time_to_extinction` is a good proving ground because it already uses
`makedoc` in external-path mode, has a full but short draft, and has local
manuscript/build contracts.

## Operating Mode

Bounded cross-repo pilot.

This goal explicitly authorizes work in two local repositories:

- engine/orchestration repo: `/Users/bwbrook/work/makedoc`
- external manuscript pilot repo:
  `/Users/bwbrook/papers/cpe_time_to_extinction`

Do not read or modify other repositories.

## Review Surface

The Makedoc orchestrator will review:

- CPE repo branch/status before and after the pilot;
- the CPE profile/source diff;
- generated CPE DOCX/PDF proof evidence;
- confirmation that ordinary `draft` and `submission` profiles remain clean;
- any `makedoc` docs/goal-log changes;
- validation output and friction notes.

## Scope

In scope:

- In the CPE repo, if and only if the repo is clean, fetch and fast-forward
  `main` to `origin/main`.
- Create a local-only CPE pilot branch, suggested name:
  `codex/makedoc-review-markup-pilot`.
- Add a dedicated CPE review-markup pilot profile to
  `settings/build.yaml`.
- Create a dedicated pilot manuscript source, suggested path:
  `manuscript/text/main_review_markup_probe.md`.
- Base the pilot source on the current full draft so the test exercises a real
  manuscript, not only a toy paragraph.
- Add a tiny, clearly artificial review-markup probe to the pilot source.
- Keep canonical manuscript sources, especially `manuscript/text/main.md`,
  clean of review-markup tokens.
- Build/inspect the CPE review-markup pilot output through `makedoc`.
- Build or inspect ordinary CPE `draft` and `submission` profiles enough to
  prove the pilot did not affect them.
- Record friction notes in this goal `Log.md`.

Out of scope:

- Pushing the CPE repo or any CPE branch.
- Pushing to CPE `main`.
- Committing in the CPE repo.
- Staging in the CPE repo.
- Changing scientific manuscript content except in the dedicated pilot source.
- Editing CPE references, figures, CSL, author metadata, or manuscript
  substance unless a build blocker requires a narrow report.
- Changing `makedoc` engine behavior unless the pilot exposes a genuine
  feature bug; if that happens, stop and report before patching.
- True Word Track Changes.
- DOCX-to-Markdown import.
- External manuscript cleanup or submission polishing.

## Read First

In `/Users/bwbrook/work/makedoc`:

- `AGENTS.md`
- `README.md`
- `docs/makedoc_primer_for_agents.md`
- `docs/markdown_review_markup_spike.md`
- `docs/goals/002-review-markup-production-hardening/Goal.md`
- `docs/goals/002-review-markup-production-hardening/Log.md`
- `Makefile`

In `/Users/bwbrook/papers/cpe_time_to_extinction`, read repo-local
`AGENTS.md` first, then:

- `README.md`
- `docs/makedoc_workflow.md` if present
- `settings/build.yaml`
- `manuscript/text/main.md`
- `manuscript/text/figures.md`
- `Makefile`

## Starting State Checks

Run from `/Users/bwbrook/work/makedoc`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
```

Expected baseline before this packet was written:

```text
## main...origin/main
```

Expected HEAD:

```text
c49a698 Harden review markup documentation and regression checks
```

Run from `/Users/bwbrook/papers/cpe_time_to_extinction`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
git log -5 --oneline
git remote -v
```

Observed baseline before this packet was written:

```text
## main...origin/main
```

Observed HEAD:

```text
e1b2433 Fix macOS manuscript build setup
```

If the CPE repo is dirty before the fast-forward step, stop and report. Do not
clean or stash it.

## CPE Git Policy

Allowed in `/Users/bwbrook/papers/cpe_time_to_extinction` only:

```sh
git fetch --prune origin
git merge --ff-only origin/main
git switch -c codex/makedoc-review-markup-pilot
```

Conditions:

- Run the fetch/fast-forward only if the CPE repo is clean.
- If the fast-forward fails, stop and report.
- If `codex/makedoc-review-markup-pilot` already exists, stop and report
  rather than reusing or deleting it.
- Do not push.
- Do not commit.
- Do not stage.
- Do not reset, clean, stash, rebase, or discard files.

In `/Users/bwbrook/work/makedoc`:

- Edits are limited to this Goal 003 packet and its `Log.md`, unless a genuine
  engine bug is discovered and you stop for orchestrator direction.
- Do not commit, push, fetch, pull, reset, clean, stash, or stage files.

## Data, Compute, And Artifact Policy

- Use only the local Mac mini.
- Generated CPE outputs should stay under the CPE repo's ignored `build/`
  directory.
- Generated `makedoc` scratch/output should stay under ignored `.cache/` or
  existing ignored output locations.
- Do not force-add generated PDF/DOCX/manifest files.
- Run Make targets sequentially, never in parallel.

## Required Work

1. Capture starting state for both repos in `Log.md`.
2. Read the required files.
3. If CPE is clean, fetch and fast-forward CPE `main` to `origin/main`.
4. Create the local-only CPE pilot branch.
5. Add a review-markup pilot profile to CPE `settings/build.yaml`, suggested
   profile name:
   `review_markup_pilot`.
6. Create `manuscript/text/main_review_markup_probe.md` by copying the current
   draft source and adding a very small, clearly artificial review-markup probe.
7. Keep `manuscript/text/main.md` free of review-markup tokens.
8. Build the CPE `review_markup_pilot` profile through `makedoc`.
9. Inspect generated CPE PDF/DOCX evidence for visible review traces.
10. Build or inspect CPE `draft` and `submission` profiles enough to confirm
    they still use the clean source and do not emit review tokens.
11. Run the relevant `makedoc` engine regression target:
    `make test-review-markup`.
12. Update `Log.md` with the profile/source choices, validation output,
    artifacts, friction notes, and final statuses for both repos.

## Validation Gates

Run sequentially from `/Users/bwbrook/work/makedoc` unless noted otherwise:

```sh
make test-review-markup
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make validate-config
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make -B all
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=draft make validate-config
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=submission make validate-config
```

Also inspect generated review-markup pilot artifacts. Suggested checks:

```sh
pdftotext /Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf -
unzip -p /Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.docx word/document.xml
```

Then run from the CPE repo:

```sh
rg '\\{\\+\\+|\\{--|\\{~~|\\{>>' manuscript/text/main.md
git diff --check
git status --short --branch
```

The `rg` command should find no review-markup tokens in the canonical main
source. If `rg` exits non-zero because there are no matches, that is the
desired result; report it clearly.

Run from `/Users/bwbrook/work/makedoc`:

```sh
git diff --check -- docs/goals/003-cpe-review-markup-pilot
git status --short --branch
```

If CPE draft/submission rendering is cheap and stable, also run:

```sh
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=draft make -B all
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=submission make -B all
```

If those broaden runtime or fail for unrelated manuscript reasons, stop
widening and report the smallest cause.

## Deliverables

- CPE local pilot branch with unstaged pilot changes only.
- CPE `settings/build.yaml` profile diff for `review_markup_pilot`.
- CPE dedicated pilot source at
  `manuscript/text/main_review_markup_probe.md`.
- Generated CPE review-markup DOCX/PDF evidence under ignored `build/`.
- Updated Goal 003 `Log.md`.
- Final report with both repo statuses, validation, artifacts, friction notes,
  and recommended next step.

## Decision Authority

You may decide:

- exact placement of the tiny artificial review-markup probe inside the pilot
  source;
- exact output folder/stem names, provided they remain under CPE `build/`;
- whether to build CPE `draft`/`submission` outputs or only validate profiles
  if full rendering is slow or not needed;
- whether a discovered issue is a docs friction note or a true engine blocker.

Pause before:

- modifying canonical `manuscript/text/main.md`;
- editing scientific claims in the CPE manuscript;
- changing references, figures, CSL, or author metadata;
- changing `makedoc` engine code;
- committing or pushing in either repo;
- cleaning, stashing, resetting, rebasing, or discarding files;
- reading any repository outside the two authorized paths;
- starting another goal.

## Checkpoint Rules

Send a wake-up to the Makedoc orchestrator if:

- CPE is dirty before the pilot branch is created;
- CPE cannot be fast-forwarded cleanly;
- the pilot branch already exists;
- the external-path review profile cannot be validated;
- DOCX/PDF evidence cannot be generated or inspected;
- clean draft/submission profiles appear affected;
- the work would require one of the pause-before boundaries.

## Stop Conditions

Stop when one of these is true:

- the CPE review-markup pilot evidence and `Log.md` are complete;
- a blocker prevents the pilot without widening scope;
- the work would require one of the pause-before boundaries.

## Final Response Requirements

Report:

- starting and final branch/status/HEAD for both repos;
- whether CPE was fast-forwarded and to what commit;
- CPE pilot branch name;
- CPE files changed or created;
- generated artifact paths;
- validation commands and results;
- confirmation that canonical `manuscript/text/main.md` has no review-markup
  tokens;
- confirmation that no commits, pushes, staging, resets, cleans, stashes,
  rebases, dependency installs, generated artifact force-adds, unrelated repo
  reads, or unrelated edits were performed;
- recommended next step.
