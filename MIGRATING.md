# Migrating a manuscript repository from makedoc v1 to v2

This is for an agent or person whose repository builds with makedoc v1, the Makefile-driven tool at `~/work/makedoc`. It lists every change that can break a v1 setup and the exact replacement.

**You are on v1 if** your repository runs `make -C <makedoc checkout> CONFIG=... all`, or has a `makedoc.lock.json`, or passes `PROFILE_CACHE_DIR` or `PDF_ENGINE_OUTPUT_DIR`.

Nothing forces the move. v1 is frozen at the tag `v1.0.0`; a repository pinned to it keeps building as long as a checkout of that tag exists. New features and fixes land only in v2.

## What does not change

- The profile YAML. Every v1 key keeps its name, values and meaning, except the two removed keys and the `output_dir: dist` case below.
- Manuscript Markdown conventions: `<div id="authors"></div>`, the `References` heading, figure lines with `{#fig-id width=..}`, `-s1` supplementary ids, citation syntax, review markup tokens.
- `authors.yaml` and the bibliography format.
- Output file names: `<output_stem>.pdf`, `<output_stem>.docx`, `<output_stem>_build_manifest.json` in `output_dir`.

## Steps

1. **Replace the Make calls** with the `makedoc` command (table below).
2. **Delete the workarounds** v1 needed (list below).
3. **Run `makedoc check --all`**. It reports any config key v2 no longer accepts, with the fix.
4. **Run `makedoc build --all`** and read the warnings. v1 hid them; v2 prints them. A build that now fails on a missing glyph was silently dropping that character before.
5. **Look at the PDFs.** Pagination is unchanged for most text, but characters that used to vanish now take space.

## Command map

`MAKEDOC` below stands for however you invoke v2, normally:

```make
MAKEDOC := uvx --from git+https://github.com/BWBrook/makedoc@v2.0.0 makedoc
```

| v1 | v2 |
| --- | --- |
| `make -C $(MAKEDOC) CONFIG=$(CONFIG) all` | `$(MAKEDOC) build -c $(CONFIG)` |
| `... PROFILE=draft all` | `$(MAKEDOC) build -c $(CONFIG) -p draft` |
| one Make call per profile | `$(MAKEDOC) build -c $(CONFIG) --all` or `-p a -p b` |
| `... pdf` / `... docx` | `$(MAKEDOC) build -c $(CONFIG) --pdf` / `--docx` |
| `... manifest` | nothing; every build writes the manifest |
| `... validate-config` | `$(MAKEDOC) check -c $(CONFIG)` (validation is its first step) |
| `... lint-manuscript refs-audit` | `$(MAKEDOC) check -c $(CONFIG)` |
| `... check` | `$(MAKEDOC) check -c $(CONFIG) && $(MAKEDOC) build -c $(CONFIG)` |
| `... profiles` | `$(MAKEDOC) profiles -c $(CONFIG)` |
| `... profile-show` | `$(MAKEDOC) show -c $(CONFIG)` |
| `make -C ~/work/makedoc csl-search JOURNAL="X"` | `$(MAKEDOC) csl search "X"` |
| `... csl-source JOURNAL="X" CSL_DEST_DIR=dir` | `$(MAKEDOC) csl fetch "X" --dest dir` |
| `... profile-scaffold PROFILE_NAME=...` | `$(MAKEDOC) init DIR`, then edit `settings/build.yaml` |
| `... diagnose` | `$(MAKEDOC) build ... --workdir DIR` keeps `prepared.md`, `layout.tex` and the LaTeX log |
| `... deps-install-minimal`, `wsl-smoke` | `$(MAKEDOC) doctor` prints what is missing and an install command |
| `PDF_ENGINE=...`, `PANDOC_FROM=...`, `PANDOC=...` overrides | Removed. v2 always uses `xelatex` and the reader `markdown+yaml_metadata_block+tex_math_dollars+tex_math_single_backslash`. If a repository relied on another engine or reader extension, open an issue before migrating. |
| `-B` or `--always-make` | nothing; every build starts from the sources |

`-c` defaults to `settings/build.yaml` relative to the current directory, so from the directory that holds `settings/` the flag can be omitted.

## Workarounds to delete

| v1 workaround | Why v2 does not need it |
| --- | --- |
| `makedoc.lock.json` and a `check-makedoc` rule comparing `git rev-parse HEAD` | The version is pinned in the `uvx --from ...@TAG` spec. Use a commit hash instead of a tag for an immutable pin. |
| `uv run --no-project --with pyyaml make ...`, or a `.venv` with PyYAML | makedoc is a package; `uvx` supplies its dependencies. |
| `PROFILE_CACHE_DIR=...`, `PDF_ENGINE_OUTPUT_DIR=...` | Each build uses a private temporary directory. |
| `--always-make` / `-B` because figure images were not prerequisites | No incremental state. |
| "Do not run two makedoc builds at once" | Concurrent builds are safe. |
| A glyph scanner for Greek, `≤`, `≈`, arrows, Unicode sub/superscripts | Body text gets LaTeX fallbacks; anything still missing fails the build by name. Characters in code spans still need a monospace font that has them. |
| A script that repairs DOCX page size, margins, page numbers or metadata | makedoc applies the profile's layout to the DOCX. Keep a script only for styling makedoc does not offer, and say so in a comment. |

## Config changes

| v1 | v2 |
| --- | --- |
| `output_dir: dist` wrote to `<makedoc checkout>/dist/<inferred-name>/` | `output_dir` is always relative to the config file. `dist` now means `settings/dist/`. Set the directory you want, for example `../build`. |
| `output_dir: dist/<name>` wrote inside the makedoc checkout | Same rule: relative to the config file. |
| `golden_contract:` | Removed. Delete the key. |
| `edgecases:` | Removed. Delete the key. |
| `csl:` required | Optional. Without it Pandoc's default author–date style is used. |
| top-level keys other than `default_profile`, `profiles` rejected | `common:` is also accepted, for YAML anchors. |
| `csl_search_dirs:` searched by `make csl-search` | Still searched: `makedoc csl search` and `csl fetch` read the default profile of `-c CONFIG` (default `settings/build.yaml`) when that file exists. Add other directories with `--dir`. |
| — | New optional `fonts:` mapping (`main`, `sans`, `mono`, `math`) for the PDF. |

## Behaviour changes

- **Warnings are shown.** Pandoc and LaTeX warnings print as `warning [profile]: ...` and are stored in the manifest. `--strict` makes them fail.
- **Missing glyphs fail the PDF build** instead of producing a PDF with characters absent.
- **16-bit PNGs with alpha fail the PDF build.** xelatex renders them invisible; v1 gave a blank figure. Re-save as 8-bit (`magick in.png -depth 8 out.png`).
- **Missing LaTeX packages fail the build.** v1 printed a warning and built without line numbers or margins.
- **Figure links work in `captions_page` mode.** v1 produced dead links in the PDF there.
- **Invalid optional values are errors.** v1 ignored a mistyped value such as `references_new_page: fales` or a list given for `author_metadata` and used the default; v2 reports the key.
- **An image whose file is missing fails the build**, for absolute paths as well as relative ones.
- **Without a `References` heading, the bibliography precedes end-of-document figures.** v1 put it after them.
- **Per-section line numbering now restarts at each section.** In v1 `line_numbering: section` never reset.
- **DOCX images wider than the text area are scaled down** to fit the profile's margins.
- **Citation keys containing `/`, `&`, `?` and similar** are read in full by the citation audit (for example DOI-style keys).
- **HTML comment blocks are inert.** A figure line or citation inside `<!-- ... -->` is no longer extracted or linted.
- **DOCX layout follows the profile**: paper size, margins and page numbers, as well as line spacing and numbering. Title and author metadata are filled in.
- **A standalone supplement** (a profile whose figures are all supplementary) no longer gets a "Supplementary Information" divider page.
- **The manifest** drops the makedoc repository's git state and Make version, and adds `makedoc_version`, the manuscript repository's commit, figure image hashes and the build warnings.
- **`make check` no longer exists as one step.** `makedoc check` does not build; run `makedoc build` after it.

## A v2 wrapper Makefile

For a repository with `settings/build.yaml` beside the Makefile and several profiles:

```make
MAKEDOC := uvx --from git+https://github.com/BWBrook/makedoc@v2.0.0 makedoc

.PHONY: all check
all:
	$(MAKEDOC) build --all

check:
	$(MAKEDOC) check --all
```

To test an unreleased makedoc from a local checkout, override the variable:

```bash
make MAKEDOC="uv run --project ~/work/makedoc makedoc"
```

## If something else breaks

Open an issue at <https://github.com/BWBrook/makedoc/issues> with the command, the output and the profile. If the problem is a v1 behaviour that this document does not list, that is a gap in this document and will be fixed here.
