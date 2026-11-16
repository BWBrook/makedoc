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
| `... diagnose` | `$(MAKEDOC) build ... --workdir DIR` keeps `prepared.md`, `resolved.json`, `layout.tex` and the LaTeX log |
| `... deps-install-minimal`, `wsl-smoke` | `$(MAKEDOC) doctor` prints what is missing and an install command |
| `PDF_ENGINE=...`, `PANDOC_FROM=...`, `PANDOC=...` overrides | Removed. v2 always uses `xelatex` and the reader `markdown+yaml_metadata_block+tex_math_dollars+tex_math_single_backslash`. If a repository relied on another engine or reader extension, open an issue before migrating. |
| `-B` or `--always-make` | nothing; every build starts from the sources |
| `... tidy`, `... clean` | nothing; makedoc keeps no cache. Delete your own `output_dir` if you want a clean slate. |
| `LAYOUT_RENDER=...`, `SOURCE_RENDER=...` overrides | Removed, with the scripts they replaced. For LaTeX preamble lines use `header-includes` (below). A custom figure renderer has no replacement; open an issue describing the layout you need. |
| `python <makedoc>/scripts/build_manifest.py ...` | nothing; the build writes the manifest. See "Post-processing the DOCX" below if you re-hashed after a formatter. |
| `python <makedoc>/scripts/prepare_markdown_sources.py`, `render_pdf_layout.py`, or importing them | Removed. `makedoc build --workdir DIR` writes the same intermediates: `prepared.md`, `resolved.json`, `layout.tex`. |

`-c` defaults to `settings/build.yaml` relative to the current directory, so from the directory that holds `settings/` the flag can be omitted.

## Workarounds to delete

| v1 workaround | Why v2 does not need it |
| --- | --- |
| `makedoc.lock.json` and a `check-makedoc` rule comparing `git rev-parse HEAD` | The version is pinned in the `uvx --from ...@TAG` spec. Use a commit hash instead of a tag for an immutable pin. |
| `uv run --no-project --with pyyaml make ...`, or a `.venv` with PyYAML | makedoc is a package; `uvx` supplies its dependencies. |
| `PROFILE_CACHE_DIR=...`, `PDF_ENGINE_OUTPUT_DIR=...` | Each build uses a private temporary directory. |
| `--always-make` / `-B` because figure images were not prerequisites | No incremental state. |
| "Do not run two makedoc builds at once" | Concurrent builds are safe. |
| A glyph scanner for Greek, `≤`, `≈`, arrows, Unicode sub/superscripts | Body text gets LaTeX fallbacks; anything still missing fails the build by name. Characters in code spans still need a monospace font that has them. If the scanner is part of a larger script, remove only that part. |
| `TMPDIR=...` pointed at the makedoc checkout or a build directory | Not needed; the default temporary directory is used and cleaned up. |
| A script that moves standalone page-break paragraphs in the DOCX onto the next paragraph | makedoc now writes `w:pageBreakBefore` itself. |
| A wrapper that hid Pandoc's `Figure N:` caption on figure pages | makedoc prints one label per figure (`Fig. 1. Caption`). |
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
| — | New `figures.placement: in_place`, which leaves each figure where it is written. |

Outputs that v1 wrote under the makedoc checkout's `dist/<name>/` stay there. Nothing reads them; delete them when the repository has moved.

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
- **Structure is read from the parsed document.** A figure line, placeholder or heading inside an HTML comment, a code block or a code span is never acted on. v1 matched lines of text and could extract a commented-out figure.
- **A standalone image without an attribute block is a figure.** v1 moved only image lines that ended in `{...}`; an image paragraph with no attributes stayed where it was, as a captioned figure in the text. v2 treats any paragraph holding only an image as a figure and places it like the others. If the manuscript relied on the v1 behaviour, set `figures.placement: in_place`: every figure then stays where it is written, labelled `Fig. N.` with its caption.
- **One label per figure.** In `pages` and `inline` placement v1 printed its own `Fig. S1.` and, under the image, Pandoc's `Figure 1: caption`, with numbers that could disagree. v2 prints `Fig. S1. caption` once, above or below the image according to `caption_position`. Caption and image are kept on one page, the image is centred, and an image too tall for the space the caption leaves is scaled down.
- **`header-includes` in the manuscript's YAML metadata reaches the LaTeX preamble.** v1 dropped it without a message. It is added after makedoc's own layout, so it can override it. For LaTeX that works after `\begin{document}`, a raw block (```` ```{=latex} ````) in a source file also works and is ignored by the DOCX.
- **PDF images are converted to 300 dpi PNG for the DOCX**, because Word cannot display a PDF image. The PDF output still embeds the original.
- **Review markup is expanded in figure captions** as well as in body text.
- **DOCX layout follows the profile**: paper size, margins and page numbers, as well as line spacing and numbering. Title and author metadata are filled in.
- **DOCX internals that scripts may match on have changed.** Image alt text (`descr`) is the caption, never the source path, and no local path is written anywhere in the file. Page breaks are `w:pageBreakBefore` on the paragraph that starts the page, not a paragraph of their own. Empty and image-only paragraphs carry `w:suppressLineNumbers`. XML namespace prefixes are the standard ones (`w:`), not `ns0:`. Run any DOCX post-processor you keep against a v2 file and check that it still does its work: one that matches the old shapes can pass while doing nothing.
- **Blinded builds.** A profile without `author_metadata` produces a PDF with an empty Author field and a DOCX with no author; neither format contains local paths or user names.
- **A standalone supplement** (a profile whose figures are all supplementary) no longer gets a "Supplementary Information" divider page.
- **The manifest schema changed.** A script that reads it needs these edits:

  | v1 key | v2 |
  | --- | --- |
  | `git` (state of the makedoc checkout) | removed; `makedoc_version` is the version string |
  | — | `manuscript_git: {sha, dirty}`, the manuscript repository |
  | `tool_versions.make` | removed; `pandoc`, `xelatex`, `python` remain |
  | `profile` | the resolved profile, absolute paths |
  | `inputs[]`, `outputs[]` | unchanged shape: `path`, `exists`, `size_bytes`, `sha256`. `inputs` now includes every figure image. |
  | — | `warnings`: the build's warnings |
- **`make check` no longer exists as one step.** `makedoc check` does not build; run `makedoc build` after it.

## Post-processing the DOCX

The manifest is written during the build, so its DOCX hash describes the file makedoc produced. If the repository then runs its own formatter or sanitiser over the DOCX, record the final file's hash in the repository's own provenance; makedoc does not re-hash.

## Intermediate files

`makedoc build --workdir DIR` keeps `prepared.md`, `resolved.json`, `layout.tex` and `latex/` (the xelatex log and aux files). With more than one profile each gets `DIR/<profile>/`. These names are stable within makedoc 2 and may be read by repository scripts, for example a page-length audit. Rebuild from the sources to change the output; do not edit the intermediates.

## Pins, old snapshots and collaborators

- A repository pinned to a v1 commit keeps building from a checkout of that commit. `v1.0.0` is the last v1 state; older pinned commits that archived replays depend on are tagged `v1-pin-<sha>` so they stay reachable.
- Tooling that replays an archived snapshot by mounting a makedoc checkout should stay on its v1 commit for those snapshots. Migrate only the live build.
- Every machine that builds needs `uv`, Pandoc, xelatex and network access to GitHub on the first run (uvx caches makedoc afterwards). Tell collaborators before the pin changes.

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

`check` and `build` act on `default_profile` alone unless given `--all` or `-p`.

To test an unreleased makedoc from a local checkout, override the variable:

```bash
make MAKEDOC="uv run --project ~/work/makedoc makedoc"
```

## If something else breaks

Open an issue at <https://github.com/BWBrook/makedoc/issues> with the command, the output and the profile. If the problem is a v1 behaviour that this document does not list, that is a gap in this document and will be fixed here.
