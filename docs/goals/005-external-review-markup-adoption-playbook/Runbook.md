# Runbook: External Review Markup Adoption Playbook

## Starting Commands

From `/Users/bwbrook/work/makedoc`:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
git log -1 --oneline
```

Expected:

```text
## main...origin/main
e4be37c
e4be37c Make review markup deletions PDF-readable
```

In CPE, read `AGENTS.md` first, then run only:

```sh
pwd
git status --short --branch
git rev-parse --short HEAD
git diff --stat -- settings/build.yaml
```

Expected:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
e1b2433
```

## Permitted CPE Evidence

After reading CPE `AGENTS.md`, only inspect:

```sh
sed -n '1,130p' settings/build.yaml
sed -n '1,70p' manuscript/text/main_review_markup_probe.md
rg '\{\+\+|\{--|\{~~|\{>>' manuscript/text/main.md
find build/review-markup-pilot -maxdepth 1 -type f -print 2>/dev/null | sort
```

For the `rg` token scan, no matches is the desired result.

Do not run CPE builds for Goal 005.

## Makedoc Edits

Create:

```text
docs/review_markup_external_adoption.md
docs/goals/005-external-review-markup-adoption-playbook/Goal.md
docs/goals/005-external-review-markup-adoption-playbook/Plan.md
docs/goals/005-external-review-markup-adoption-playbook/Runbook.md
docs/goals/005-external-review-markup-adoption-playbook/Log.md
```

Update, if useful:

```text
README.md
docs/makedoc_primer_for_agents.md
```

Do not change engine code, tests, fixtures, Make targets, schema, rendering
semantics, or generated artifacts for this goal.

## Validation

Run sequentially from `/Users/bwbrook/work/makedoc`:

```sh
make test-review-markup
git diff --check
```

If only Markdown docs and goal files changed, do not run broader builds unless
a concrete reason appears and is recorded.

## Wake-Up

Wake the Makedoc orchestrator thread
`019eaf80-3882-7d31-b6a4-3cb4c2ab5699` with:

- complete or blocked status;
- changed files;
- CPE inspection performed;
- CPE final status;
- validation results;
- whether any CPE artifacts were regenerated;
- recommended next step.

Stop after the wake-up.
