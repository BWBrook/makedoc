# Runbook: CPE Pilot Branch Disposition

## Makedoc Guard

```sh
cd /Users/bwbrook/work/makedoc
git status --short --branch
git rev-parse --short HEAD
```

Expected:

```text
## main...origin/main
efb07e0
```

## CPE Guard

Read CPE `AGENTS.md` first, then:

```sh
cd /Users/bwbrook/papers/cpe_time_to_extinction
git status --short --branch
git status --porcelain=v1 --untracked-files=all
git rev-parse --short HEAD
git branch --show-current
git rev-list --left-right --count main...codex/makedoc-review-markup-pilot
```

Expected:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
e1b2433
codex/makedoc-review-markup-pilot
0  0
```

Stop before cleanup if the guard differs.

## Cleanup Commands

Use only after the guard matches:

```sh
git restore -- settings/build.yaml
rm -f manuscript/text/main_review_markup_probe.md
if [ -d build/review-markup-pilot ]; then
  rm -rf build/review-markup-pilot
fi
git status --short --branch
git switch main
git branch -d codex/makedoc-review-markup-pilot
```

Do not use `git reset`, `git clean`, `git stash`, `git rebase`, force deletion,
fetch, pull, push, or CPE builds.

## Validation

Makedoc only:

```sh
cd /Users/bwbrook/work/makedoc
git diff --check
```

Final CPE checks:

```sh
cd /Users/bwbrook/papers/cpe_time_to_extinction
git status --short --branch
git rev-parse --short HEAD
git branch --list codex/makedoc-review-markup-pilot
test ! -e manuscript/text/main_review_markup_probe.md
test ! -e build/review-markup-pilot
```
