# AGENTS.md

makedoc builds journal-ready PDF and DOCX manuscripts from Markdown, figures, a CSL-YAML bibliography and a YAML build profile, through Pandoc and xelatex. Manuscripts live in their own repositories and call makedoc as a pinned command-line tool.

Read `README.md` first: it is the user-facing reference for commands, profile keys and build behaviour. `docs/makedoc_primer_for_agents.md` is the guide given to agents working in manuscript repositories. `MIGRATING.md` is the v1 to v2 contract with existing users.

## Layout

- `src/makedoc/cli.py`: argument parsing and the commands.
- `src/makedoc/profile.py`, `schema.py`, `validate.py`: profile resolution, allowed keys and config validation.
- `src/makedoc/prepare.py`: the text-level steps only: join the sources, mark each file's directory, expand review markup, and write the settings for the structure filter.
- `src/makedoc/filters/structure.lua`: arranges the parsed document: image paths, author block, figure extraction, numbering and placement, bibliography anchor, page breaks. Structural logic belongs here, on the parsed document, never in regexes over Markdown text.
- `src/makedoc/layout.py`: the LaTeX header for a profile. `filters/unicode_fallback.lua`: fallbacks for characters the PDF font lacks.
- `src/makedoc/markdown_scan.py`: line scanner that skips code and comments, used by lint, the citation audit and review markup (these report line numbers, which the parsed document does not carry).
- `src/makedoc/build.py`: runs Pandoc in two stages (sources to a structured `resolved.json`, then that to PDF and DOCX), collects warnings, moves outputs into place, writes the manifest (`manifest.py`).
- `src/makedoc/docx.py`: post-processes the DOCX to match the profile.
- `src/makedoc/lint.py`, `refs.py`: source lint and citation audit used by `makedoc check`.
- `src/makedoc/csl.py`: citation style search and download.
- `src/makedoc/template/`: the files `makedoc init` writes.
- `testbed/`: a synthetic manuscript, the regression fixture. Its profiles are in `testbed/settings/build.yaml`.
- `tests/`: pytest unit and end-to-end tests.

## Commands

```bash
uv run pytest -q                                            # all tests
uv run makedoc build -c testbed/settings/build.yaml --all   # build the fixture into testbed/build/
uv run makedoc check -c testbed/settings/build.yaml --all
uv run makedoc doctor
```

The system Python may lack PyYAML; always go through `uv run`.

## Rules

1. **Users pin releases, so compatibility is explicit.** Any change to a command, flag, profile key, default, output name or build behaviour that could alter or break an existing manuscript build must be recorded in `CHANGELOG.md` and, if it needs action from users, in `MIGRATING.md` with the exact before and after. Breaking changes wait for a major version.
2. **Never drop content silently.** If makedoc cannot render or place something the author wrote, it fails or warns by name. A green build must mean the outputs contain the manuscript.
3. **Manuscripts stay in their own repositories.** Do not copy manuscript content into this repository, and do not edit a manuscript repository while road-testing unless asked. Keep "the manuscript has a problem" separate from "makedoc has a problem".
4. **The fixture is the regression contract.** When build behaviour changes, update the fixture or its tests in the same commit.
5. **A passing build is not a checked document.** After a change to preparation, layout or DOCX handling, render the fixture and look at the pages.
6. **Scope.** makedoc owns source preparation and building. Word comments, tracked changes and DOCX-to-Markdown reconciliation are outside makedoc; review happens at the source with scrivmark (`docs/docx_review_boundary.md`).

## After a change

- Run `uv run pytest -q`.
- For anything touching `prepare.py`, `layout.py`, `docx.py`, `build.py` or the Lua filter, also build the fixture with `--strict` and inspect the PDF and DOCX.
- Update `README.md` and `docs/makedoc_primer_for_agents.md` when behaviour or a profile key changes, and `CHANGELOG.md` always.

## Releasing

Bump `version` in `pyproject.toml`, date the `CHANGELOG.md` section, tag `vX.Y.Z` and push the tag. Manuscript repositories move to the new tag when they choose.
