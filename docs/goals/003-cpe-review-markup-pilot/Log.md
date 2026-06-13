# Log: CPE Review Markup External Manuscript Pilot

## 2026-06-13 - Goal Packet Created

Status: ready for `draftsman`.

Makedoc orchestrator created this packet after Barry approved using
`/Users/bwbrook/papers/cpe_time_to_extinction` as the first external manuscript
pilot for the review-markup workflow.

`makedoc` baseline before this packet was written:

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
c49a698
```

```text
git log -1 --oneline
c49a698 Harden review markup documentation and regression checks
```

CPE baseline before this packet was written:

```text
pwd
/Users/bwbrook/papers/cpe_time_to_extinction
```

```text
git status --short --branch
## main...origin/main
```

```text
git rev-parse --short HEAD
e1b2433
```

```text
git log -5 --oneline
e1b2433 Fix macOS manuscript build setup
96fd390 Draft time to extinction explainer
0e25785 Initial manuscript scaffold
```

```text
git remote -v
origin	git@github.com:BWBrook/cpe_time_to_extinction.git (fetch)
origin	git@github.com:BWBrook/cpe_time_to_extinction.git (push)
```

CPE has a repo-local `AGENTS.md`, and it was present/read during orchestrator
orientation for this packet. CPE has `draft` and `submission` profiles in
`settings/build.yaml`, both using `manuscript/text/main.md` and
`manuscript/text/figures.md`.

Safety decision: the pilot should not insert review-markup tokens into the
canonical `manuscript/text/main.md`. Instead, it should create a dedicated
pilot source copied from the full draft and point a dedicated
`review_markup_pilot` profile at that source.

Publication boundary: no commits, pushes, or staging in either repo during the
implementation pass. CPE may be fetched/fast-forwarded and switched to a
local-only pilot branch if and only if it is clean.

## 2026-06-13 - Execution Started

Executor: `draftsman`.

Starting state confirmed in `/Users/bwbrook/work/makedoc`:

```text
pwd
/Users/bwbrook/work/makedoc
```

```text
git status --short --branch
## main...origin/main
?? docs/goals/003-cpe-review-markup-pilot/
```

```text
git rev-parse --short HEAD
c49a698
```

Starting state confirmed in `/Users/bwbrook/papers/cpe_time_to_extinction`:

```text
git status --short --branch
## main...origin/main
```

```text
git rev-parse --short HEAD
e1b2433
```

Read CPE repo-local `AGENTS.md` before other CPE project files. Then read only
the packet-authorized CPE files: `README.md`, `docs/makedoc_workflow.md`,
`settings/build.yaml`, `manuscript/text/main.md`,
`manuscript/text/figures.md`, and `Makefile`.

CPE local pilot branch did not already exist. Authorized branch-prep sequence:

```text
git fetch --prune origin
```

completed with no output.

```text
git merge --ff-only origin/main
Already up to date.
```

```text
git switch -c codex/makedoc-review-markup-pilot
Switched to a new branch 'codex/makedoc-review-markup-pilot'
```

## 2026-06-13 - Pilot Implemented And Validated

Implemented the CPE pilot as a local-only branch:
`codex/makedoc-review-markup-pilot`.

CPE edits made:

- Added `manuscript/text/main_review_markup_probe.md`, copied from the full
  draft with one pilot-only review-markup probe inserted after the abstract.
- Added a `review_markup_pilot` profile to `settings/build.yaml`, using the
  pilot source, existing `figures.md`, existing author metadata, existing
  bibliography, existing CSL, and ignored output directory
  `../build/review-markup-pilot`.

Canonical CPE `manuscript/text/main.md` was not modified.

Sequential validation results:

```text
make test-review-markup
PASS
```

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make validate-config
Build config validation passed for selected profile(s): review_markup_pilot
Build config validation passed for selected profile(s): fixture
```

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=review_markup_pilot make -B all
PASS
```

Generated pilot proof artifacts:

```text
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.pdf
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot.docx
/Users/bwbrook/papers/cpe_time_to_extinction/build/review-markup-pilot/cpe_time_to_extinction_review_markup_pilot_build_manifest.json
```

Pilot artifact inspection:

```text
pdftotext .../cpe_time_to_extinction_review_markup_pilot.pdf -
Pilot-only review-markup probe: [+ inserted pilot text +]
[Reviewer note: confirm visible review trace output]
[+ revised pilot wording +]
```

```text
unzip -p .../cpe_time_to_extinction_review_markup_pilot.docx word/document.xml
[+ inserted pilot text +] appears in bold run properties.
[- removed pilot text -] appears with strike properties.
[- old pilot wording -] appears with strike properties.
[+ revised pilot wording +] appears in bold run properties.
[Reviewer note: confirm visible review trace output] appears in bold run properties.
```

Ordinary profile checks:

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=draft make validate-config
Build config validation passed for selected profile(s): draft
Build config validation passed for selected profile(s): fixture
```

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=submission make validate-config
Build config validation passed for selected profile(s): submission
Build config validation passed for selected profile(s): fixture
```

Extra ordinary-profile builds were run because the manuscript build is small:

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=draft make -B all
PASS
```

```text
CONFIG=/Users/bwbrook/papers/cpe_time_to_extinction/settings/build.yaml PROFILE=submission make -B all
PASS
```

Canonical source cleanliness:

```text
rg '\{\+\+|\{--|\{~~|\{>>' manuscript/text/main.md
no matches
```

Whitespace checks:

```text
cd /Users/bwbrook/papers/cpe_time_to_extinction
git diff --check
PASS
```

```text
cd /Users/bwbrook/work/makedoc
git diff --check -- docs/goals/003-cpe-review-markup-pilot
PASS
```

Final CPE status after implementation:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
```

Final makedoc status after implementation:

```text
## main...origin/main
?? docs/goals/003-cpe-review-markup-pilot/
```

No makedoc engine code was changed. No files were staged, committed, pushed,
reset, cleaned, stashed, rebased, or discarded. No dependency installs were
run. Generated proof artifacts remained under ignored CPE `build/` paths.

## 2026-06-13 - Orchestrator Review Finding

The Makedoc orchestrator reviewed the CPE pilot diff, reran the core
validation ladder, inspected DOCX XML, and rendered page 2 of the pilot PDF.

Fresh orchestrator checks passed:

- `make test-review-markup`
- CPE `PROFILE=review_markup_pilot` validate-config and forced build
- CPE `PROFILE=draft` validate-config and forced build
- CPE `PROFILE=submission` validate-config and forced build
- canonical CPE `manuscript/text/main.md` review-token scan had no matches
- CPE `git diff --check`
- makedoc Goal 003 diff check

Finding: the external-path pilot is mechanically successful. The CPE
`review_markup_pilot` profile and isolated pilot source worked as intended,
the canonical CPE draft/submission profiles remained clean and unaffected, and
the generated DOCX review traces are strong. In DOCX, additions and reviewer
notes are visibly traceable, and deletion/old-wording strikeout is usable.

Usability caveat: PDF additions and reviewer notes are readable, but PDF
deletion and old-wording strikeout are not visually legible enough. In the
rendered PDF, deleted/old wording appears mostly as strike lines rather than
as readable bracketed deleted words. This does not invalidate the external
pilot, but it is a material limitation for wider manuscript review use.

Recommendation: before broader external manuscript adoption, create a focused
engine hardening goal for PDF deletion-legibility and review-markup styling
policy. That goal should evaluate a PDF-specific rendering policy for
deletions/old wording while preserving the strong DOCX behavior and keeping
true Word Track Changes and DOCX-to-Markdown import out of scope unless Barry
explicitly expands the feature.
