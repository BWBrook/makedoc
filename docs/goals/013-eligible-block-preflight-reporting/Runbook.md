# Runbook: Eligible-Block Preflight Reporting

## Preconditions

Makedoc:

```sh
cd /Users/bwbrook/work/makedoc
git status --short --branch
git rev-parse --short HEAD
git log -5 --oneline
```

Expected:

```text
## main...origin/main
cd47925
```

CPE, after reading CPE `AGENTS.md`:

```sh
cd /Users/bwbrook/papers/cpe_time_to_extinction
git status --short --branch
git rev-parse --short HEAD
```

Expected:

```text
## codex/makedoc-review-markup-pilot
 M settings/build.yaml
?? manuscript/text/main_review_markup_probe.md
e1b2433
```

## CPE Audit Command

Run from makedoc:

```sh
python3 scripts/import_docx_review_markup.py preflight \
  --original-path /Users/bwbrook/papers/cpe_time_to_extinction/manuscript/text/main.md \
  --format json \
  > /tmp/makedoc-goal013-eligible-blocks/cpe-main-preflight.json
```

Derived evidence should remain under:

```text
/tmp/makedoc-goal013-eligible-blocks/
```

## Validation

Run sequentially from makedoc:

```sh
python3 -m py_compile scripts/import_docx_review_markup.py
python3 -m unittest tests/test_import_docx_review_markup.py
make test-review-markup
make check
git diff --check
```

## Stop Conditions

Stop and wake the orchestrator if:

- makedoc or CPE starting state differs materially;
- CPE preflight unexpectedly reports `SAFE_TO_ATTEMPT` for the whole canonical
  source;
- validation fails for a reason outside this goal;
- completing the goal would require CPE mutation, importer support broadening,
  dependency installation, staging, committing, pushing, or Goal 014 work.
