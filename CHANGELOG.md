# Changelog

## 2.0.0 (unreleased)

makedoc becomes an installable command-line tool. [MIGRATING.md](MIGRATING.md) gives the v1 to v2 steps.

### Changed

- The Makefile and `scripts/` are replaced by the `makedoc` command: `build`, `check`, `profiles`, `show`, `init`, `doctor`, `csl`.
- A manuscript repository pins makedoc by release tag or commit in its `uvx` invocation, not by the HEAD of a shared checkout.
- Authors, figures, the bibliography anchor and page breaks are arranged on the document after Pandoc has parsed it (a Lua filter), not by matching lines of Markdown. Code blocks, code spans and HTML comments can no longer be mistaken for structure.
- A paragraph holding only an image is a figure whether or not it has an attribute block. Review markup is expanded in figure captions.
- Every build starts from the sources in a private temporary directory. Builds can run concurrently, and there is no cache to go stale.
- `output_dir` is always relative to the config file. The v1 routing of `output_dir: dist` into the makedoc checkout is gone.
- Pandoc and LaTeX warnings are printed and recorded in the manifest. `--strict` makes them fail the build.
- A character the PDF font cannot render fails the build. v1 dropped it from the PDF.
- A 16-bit PNG with an alpha channel fails the PDF build. xelatex embeds such an image fully transparent, so v1 produced a blank figure.
- A missing LaTeX package (`lineno`, `geometry`, `etoolbox`) fails the build. v1 warned and built without the feature.
- DOCX output takes paper size, margins and page numbers from the profile, and carries title and author metadata.
- `csl` is optional.

### Added

- LaTeX fallbacks for Greek letters, relations, arrows and Unicode sub- and superscripts in body text.
- `fonts` profile key for the PDF main, sans, mono and math fonts.
- `makedoc init` starter layout and `makedoc doctor` environment check.
- `--all` and repeatable `-p` to act on several profiles in one call.
- Manifest records the makedoc version, the manuscript repository's commit, figure image hashes and warnings.
- A top-level `common:` config key for YAML anchors.

### Fixed

- In-text figure links were dead in the PDF in `captions_page` mode.
- The fixture figures were 16-bit RGBA PNGs and invisible in every fixture PDF; they are now 8-bit.
- An empty bibliography is accepted when nothing is cited.
- `line_numbering: section` never restarted the numbers.
- A document with a YAML title block ignored `page_numbers` on its first page.
- Without a `References` heading, end-of-document figures came before the bibliography.
- The citation audit truncated keys containing `/`, `&` or `?`.
- Captions containing a bracketed citation, and image paths with a title or angle brackets, escaped image checks.
- A mistyped optional profile value was silently replaced by the default.
- DOCX images could overflow the text area set by the profile margins.
- Figure lines and citations inside HTML comment blocks were extracted and linted.
- A standalone supplement received a "Supplementary Information" divider page.

### Removed

- Profile keys `golden_contract` and `edgecases` (they served makedoc's own tests).
- `make-vars`, the profile cache, `profile-scaffold`, `diagnose`, the dependency installer and the `wsl-smoke` target.
- GitHub Actions annotations from lint output.

## 1.0.0

The Makefile-driven tool, frozen at tag `v1.0.0`.
