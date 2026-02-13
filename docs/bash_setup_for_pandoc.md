# Q&A with ChatGPT on pandoc setup

## User
I have a markdown file of a science paper that I've drafted. It includes formula written in LaTeX. It also includes references to literature, currently just inserted as plain text, in other words, author and year with brackets around it, in the appropriate citation point. It's not actually an insert token right now. I also have an export of a Zotero library of the actual references, and I have a CSL file for the journal formatting. How easy or difficult is it in Ubuntu, using tooling such as Pandoc or TeX to put these together into a correctly formatted PDF that can also convert into a Word document? Is this something I could readily get the Codex CLI agent to implement, or am I trying to reinvent a wheel that's already been built?

## ChatGPT
This is mostly a solved problem on Ubuntu: Pandoc already knows how to (a) keep your Markdown + LaTeX maths intact, (b) format citations/bibliography via CSL, and (c) emit both PDF (via a TeX engine) and DOCX directly. The “wheel” you’d be building with Codex is really just the glue: a reproducible build script/Makefile plus (if you want it) a one-off citation-conversion pass.

Pandoc’s citation engine is now built in (`--citeproc`), so you don’t need the older `pandoc-citeproc` filter any more. ([GitHub][1]) With a Zotero export (BibTeX/BibLaTeX or CSL-JSON) and the journal’s `.csl`, you can get correctly formatted in-text citations and a reference list in one command. Quarto is essentially a friendly wrapper around the same Pandoc+citeproc machinery if you ever want a higher-level project structure, but it’s not required. ([Quarto][2])

The one genuinely hard bit in what you described is that your manuscript currently has *human-formatted* placeholders like “(Smith 2021)” rather than *machine-resolvable* citekeys like `[@smith2021]`. Pandoc can only format what it can resolve against your bibliography, so you’ll need to convert those placeholders into Pandoc citations. Once you do that, everything downstream becomes routine.

A practical “happy path” looks like this.

1. Export your Zotero library in a Pandoc-friendly way, ideally with stable citekeys. The most common approach is Zotero + Better BibTeX, which generates and can “pin” citation keys so they don’t drift, and can export BibTeX/BibLaTeX or Better CSL-JSON. ([Retorque][3])

2. Replace citations in the Markdown with Pandoc’s citation syntax. Examples: `[@Smith2021]`, `[@Smith2021; @Jones2019]`, narrative `@Smith2021`, with locators `[@Smith2021, p. 33]`. (Pandoc’s manual documents the exact syntax and edge cases.) ([Pandoc][4])

3. Put bibliography + CSL in the YAML header (or pass on the command line). For example:

```yaml
---
title: "My Paper"
bibliography: refs.json   # or refs.bib
csl: journal.csl
link-citations: true
---
```

4. Build the outputs.

PDF (needs TeX installed; XeLaTeX/LuaLaTeX are common):

```bash
pandoc paper.md \
  --from markdown+tex_math_dollars \
  --citeproc \
  --pdf-engine=xelatex \
  -o paper.pdf
```

DOCX (no TeX required):

```bash
pandoc paper.md \
  --citeproc \
  -o paper.docx
```

If the journal (or you) cares about Word styling (margins, heading styles, caption styles), you use a reference DOCX:

```bash
pandoc --print-default-data-file reference.docx > reference.docx
# edit that in Word/LibreOffice to match the journal template’s styles
pandoc paper.md --citeproc --reference-doc=reference.docx -o paper.docx
```

Pandoc explicitly supports this “reference.docx” workflow. ([Pandoc][5])

On the TeX side, the only recurring pain points are (i) custom LaTeX macros you’ve sprinkled into the Markdown maths (PDF can handle them if you include the right preamble; DOCX generally can’t), and (ii) font/Unicode issues depending on engine. Pandoc documents PDF generation via TeX engines in the manual. ([Pandoc][4])

Where Codex CLI is genuinely useful is in making this frictionless and reproducible: a `Makefile` or `justfile`, a tiny `build.sh`, maybe a `requirements` check that aborts with a clear message if `pandoc`/`xelatex` isn’t installed, and a CI job that proves the manuscript builds. That’s straightforward “plumbing” work for an agent.

The place you might *not* want to fully automate is the citation placeholder conversion. Mapping “(Smith 2021)” → the correct `@Smith2021` key is ambiguous in the real world (same author-year, multiple coauthors, “Smith et al.”, suffixes 2021a/2021b, etc.). A Codex-driven approach can still work well if it’s framed as: build a candidate mapping from your Zotero export (authors+year→key), apply conservative substitutions, and emit a report of unresolved/ambiguous cases for manual fix. That’s usually faster than hand-editing from scratch, but it’s not a push-button guarantee.

Finally, if you care about getting “live” Zotero citation fields inside the DOCX (so collaborators can refresh, change style in Word, etc.), there are existing Better BibTeX/Pandoc filter workflows aimed at that; it’s another example of “wheel already exists”, though it adds moving parts. ([Retorque][6])

[1]: https://github.com/jgm/pandoc/issues/6744?utm_source=chatgpt.com "Treat `--filter pandoc-citeproc` as synonym for `"
[2]: https://quarto.org/docs/authoring/citations.html?utm_source=chatgpt.com "Citations"
[3]: https://retorque.re/zotero-better-bibtex/citing/?utm_source=chatgpt.com "Citation Keys :: Better BibTeX for Zotero"
[4]: https://pandoc.org/MANUAL.html?utm_source=chatgpt.com "Pandoc User's Guide"
[5]: https://pandoc.org/demos.html?utm_source=chatgpt.com "Demos"
[6]: https://retorque.re/zotero-better-bibtex/exporting/pandoc/index.html?utm_source=chatgpt.com "Markdown/Pandoc :: Better BibTeX for Zotero"

## User
Great advice. This sounds very doable. I'm trying to move my workflow to entirely within Ubuntu and repos, so that I can have the code, the data, and the paper all developed within the repo and then set up to automatically generate or regenerate PDF and Word documents as required, so that if I undertake revisions, I don't need to go back and change some hand-edited file in Word. That is, I'm trying to automate my manuscript writing workflow this year and fully move away from using Microsoft Word because I feel like it's a constraint and a bottleneck to me.

## ChatGPT
That workflow is exactly what Pandoc (and, if you want a bit more ergonomics, Quarto) is for: keep a single source of truth in plain text + data/code, and treat PDF/DOCX as build artefacts that can be regenerated deterministically. The “automation” part is not reinventing anything deep; it’s mostly deciding what your repo’s canonical inputs are, then wiring a reproducible build front-end around Pandoc’s existing capabilities.

A clean pattern is: (i) manuscript source in Markdown (or Quarto markdown), (ii) bibliography export committed into the repo (CSL-JSON or BibLaTeX), (iii) journal CSL committed, (iv) a small amount of metadata/preamble glue (YAML + optional `header.tex`), and (v) a one-command build that emits `dist/paper.pdf` and `dist/paper.docx`. The main discipline is to never hand-edit the DOCX; it’s a transient emission for submission or coauthors, not the master copy.

Concretely, a repo layout that scales well looks like:

```text
paper/
  manuscript.md
  meta.yaml
  journal.csl
  refs.json        # or refs.bib
  header.tex       # optional: TeX packages/macros for PDF only
  reference.docx   # optional: Word style template
  figures/         # generated or hand-made figures
  tables/          # generated tables (csv/tex/md)
  dist/            # build outputs (ignored or release-only)
  Makefile
```

Put the stable configuration into `meta.yaml` so the command line stays boring and your agent doesn’t “forget” options:

```yaml
title: "..."
bibliography: refs.json
csl: journal.csl
link-citations: true
# If you want, keep author/affiliation/abstract here too.
```

Then your build wrapper is just a thin layer. A Makefile is enough:

```make
PANDOC ?= pandoc
SRC    = manuscript.md
META   = meta.yaml
DIST   = dist
PDF    = $(DIST)/paper.pdf
DOCX   = $(DIST)/paper.docx

PDF_ENGINE ?= xelatex   # or tectonic

all: pdf docx

$(DIST):
	mkdir -p $(DIST)

pdf: $(PDF)
docx: $(DOCX)

$(PDF): $(SRC) $(META) journal.csl refs.json | $(DIST)
	$(PANDOC) $(SRC) \
	  --metadata-file=$(META) \
	  --citeproc \
	  --pdf-engine=$(PDF_ENGINE) \
	  --include-in-header=header.tex \
	  -o $(PDF)

$(DOCX): $(SRC) $(META) journal.csl refs.json reference.docx | $(DIST)
	$(PANDOC) $(SRC) \
	  --metadata-file=$(META) \
	  --citeproc \
	  --reference-doc=reference.docx \
	  -o $(DOCX)

clean:
	rm -rf $(DIST)
```

Two practical details matter a lot in day-to-day use. First, PDF builds are the dependency-heavy part if you rely on TeX Live. If you want a lighter, more reproducible PDF toolchain on Ubuntu, `tectonic` as the `--pdf-engine` is often a good fit because it fetches TeX packages on demand and reduces “works on my machine” drift; XeLaTeX/LuaLaTeX are fine too, just heavier to provision. Second, DOCX styling is best handled via `reference.docx` (Pandoc’s “style template”), which keeps you out of Word while still producing something journals recognise.

On citations: once your in-text cites are in Pandoc form (`[@key]`, `@key`, `[@key, p. 33]`, etc.), the CSL+refs export does the rest. The main structural decision is how you keep citekeys stable. Zotero + Better BibTeX with pinned keys is the usual solution, and then you commit the exported `refs.json`/`refs.bib` into the repo. Updating references becomes a deliberate action (“export, commit, rebuild”), which is exactly what you want for reproducibility. The only non-trivial migration step is converting your current human-formatted “(Author year)” placeholders into keys; that’s automatable to a point, but you’ll want the script to produce an ambiguity report rather than silently guessing when author–year collisions exist.

Where Codex CLI shines is making this production-grade quickly: wiring the Makefile, adding `dist/` to `.gitignore`, adding a `make check` target that fails if citations are unresolved, and (if you want it) a CI job that runs `make pdf docx` on every push so you always know the repo state builds. None of this is novel; it’s the same “build artefacts from source” discipline you already apply to code, just pointed at manuscripts.

The only real caveat is feature parity between PDF and DOCX around LaTeX niceties. Standard LaTeX maths usually converts well into Word’s equation format, but custom TeX macros/preamble tricks are PDF-only unless you avoid them or expand them. If you keep the manuscript’s maths reasonably “vanilla” LaTeX and confine PDF-specific hacks to `header.tex`, you’ll generally get clean dual output without needing a baroque pipeline.

## User
What's the potential advantage of quarto markdown versus plain markdown? I use quarto when I'm writing vignettes, for example, in R, but I hadn't thought about a broader use of it in this context.

## ChatGPT
Quarto Markdown (`.qmd`) is, in essence, Pandoc Markdown plus a build system and a bundle of “sensible defaults” and extensions. The advantage isn’t that the underlying prose syntax is radically different; it’s that Quarto gives you a coherent project layer (configuration, rendering, previewing, caching, templates) wrapped around Pandoc’s conversion engine. Quarto itself describes this as “Pandoc markdown … Quarto adds extensions for cross-references … advanced page layout, and more.” ([Quarto][1])

For manuscript writing, the most tangible win is cross-referencing and numbering that works consistently across PDF/Word/HTML. Quarto has first-class cross-references for figures, tables, equations, sections, even theorem-like blocks, with a stable label scheme and automatic numbering. ([Quarto][2]) With “plain Pandoc” you can get there, but you typically end up pulling in extra filters (e.g., pandoc-crossref) and more bespoke wiring; Quarto bakes the feature in.

The next win is centralised, multi-format configuration. Instead of remembering a growing pile of Pandoc flags, you put the choices into YAML and let `quarto render` drive Pandoc. You can specify per-format options cleanly (e.g., XeLaTeX settings for PDF, `reference.docx` for Word) in one place, and Quarto will render all targets from the same source. This sounds small, but it’s the difference between a pipeline you trust and a pipeline you occasionally “patch” by hand.

Where Quarto really earns its keep (and you already use this in vignettes) is the computational document model: code chunks are a first-class citizen and Quarto can manage how results appear, and—crucially for manuscripts—avoid re-running expensive computations every time you tweak wording. Quarto’s “manuscript projects” explicitly target scholarly articles where notebooks or `.qmd` files are the source of content and computations, and where the rendered outputs can include PDF and DOCX alongside a richer record of the analysis. ([Quarto][3]) Even if you don’t care about the “website” aspect, the project scaffold is a decent way to keep analysis + paper tightly coupled without becoming a tangle of ad hoc scripts.

There are also two practical engineering advantages if you’ve ever been bitten by TeX friction. Quarto has its own PDF compilation engine that handles the multi-pass dance and can install LaTeX packages automatically, which reduces the “why did this fail on the other machine?” problem in collaborative or multi-host workflows. ([Quarto][4]) And Quarto can generate PDFs via Typst as an alternative backend (fast, clean output), which is sometimes attractive for internal drafts even if you still need LaTeX for a particular journal template. ([Quarto][5])

Finally, Quarto has a templating/extension story aimed at journals: you can encapsulate a “journal format” (defaults, LaTeX bits, filters) so “switching journals” becomes swapping a format rather than re-tuning a dozen knobs. ([Quarto][6]) That’s the grown-up version of “I have a CSL file”: CSL covers citations, but the journal’s layout quirks often live elsewhere.

If your manuscript is genuinely just text + LaTeX maths + citations, Pandoc alone remains perfectly adequate. Quarto starts to look better the moment you want robust cross-references, multi-file/project organisation, integrated computation with caching, and fewer moving parts in the build glue. In practice, Quarto is often the “boring” choice because it standardises the wheel you’d otherwise end up maintaining yourself.

[1]: https://quarto.org/?utm_source=chatgpt.com "Quarto"
[2]: https://quarto.org/docs/authoring/cross-references.html?utm_source=chatgpt.com "Cross References"
[3]: https://quarto.org/docs/manuscripts/?utm_source=chatgpt.com "Quarto Manuscripts"
[4]: https://quarto.org/docs/output-formats/pdf-engine.html?utm_source=chatgpt.com "PDF Engines"
[5]: https://quarto.org/docs/output-formats/typst.html?utm_source=chatgpt.com "Typst Basics"
[6]: https://quarto.org/docs/journals/formats.html?utm_source=chatgpt.com "Journal Formats"

## User
All right, good. I have a headless Ubuntu server where I do all my development work. All my GitHub repos are on there and all the papers I'll be producing are on that server. So I'd like to check within Bash that I have all of the correct packages installed in Ubuntu, either updating current versions or installing the appropriate machinery for Pandoc, TeX, potentially of various flavours, and Quarto and any other associated tooling, such that codex will immediately have access to plenty of options. Given that this will be system-wide, I can really do a full installation once and then always have that tooling available thereafter. What's your advice on how to go about getting that set up?

## ChatGPT
On a headless Ubuntu box, I’d treat this like setting up a compiler toolchain: install a broad, boring baseline via `apt`, then add the two “fast-moving” pieces (Pandoc and Quarto) from upstream releases so you aren’t hostage to whatever version your Ubuntu release happens to ship. Pandoc explicitly supports installing the latest Linux release via a `.deb` and `dpkg -i`, and notes that PDF generation typically rides on a TeX Live install (on Debian/Ubuntu, via `apt-get install texlive`). ([Pandoc][1]) Quarto’s own server-oriented install docs likewise give you a clean, versioned install under `/opt/quarto/<version>` with a simple symlink, plus `quarto check install` for verification. ([Posit Docs][2])

For TeX you have two sane choices. If you really want “install once, rarely think again”, `texlive-full` is the sledgehammer: large, but it makes mysterious missing-package errors rare. If you’d rather keep disk use sensible, install a curated set that covers virtually all academic papers (LaTeX base + extra packages, fonts, Bib(La)TeX tooling, XeLaTeX/LuaLaTeX, latexmk). Pandoc itself leans towards “install TeX Live via your package manager” for PDF support. ([Pandoc][1])

Here’s a practical, idempotent Bash bootstrap you can run as root (or under sudo) once per machine. It installs the baseline utilities that Pandoc/Quarto commonly end up calling (SVG conversion, PDF utilities, fonts), a broad TeX Live set, then pins Pandoc and Quarto to explicit versions (so your builds are reproducible across time and hosts):

```bash
#!/usr/bin/env bash
set -euo pipefail

# ---- 0) OS baseline ----
sudo apt-get update
sudo apt-get -y upgrade

sudo apt-get install -y \
  build-essential make git \
  curl wget ca-certificates gnupg jq \
  unzip zip \
  python3 python3-venv python3-pip python3-yaml python3-pygments \
  ghostscript poppler-utils \
  librsvg2-bin \
  fonts-dejavu fonts-liberation

# ---- 1) TeX Live (choose ONE approach) ----

# Option A: "I never want TeX package surprises" (big install)
# sudo apt-get install -y texlive-full

# Option B: Broad but not insane (usually plenty for papers)
sudo apt-get install -y \
  texlive \
  texlive-latex-base texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended texlive-fonts-extra lmodern \
  texlive-bibtex-extra biber \
  texlive-xetex texlive-luatex latexmk \
  texlive-science texlive-publishers

# ---- 2) Pandoc (upstream .deb) ----
# Pandoc recommends using the installer for the latest release; Linux provides a .deb
# installed via dpkg. :contentReference[oaicite:3]{index=3}
PANDOC_VERSION="3.1.13"   # set what you want to standardise on
ARCH="$(dpkg --print-architecture)"  # typically amd64
TMPDIR="$(mktemp -d)"
curl -L -o "${TMPDIR}/pandoc.deb" \
  "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-${ARCH}.deb"
sudo dpkg -i "${TMPDIR}/pandoc.deb"
rm -rf "${TMPDIR}"

# ---- 3) Quarto (versioned install under /opt + symlink) ----
# This mirrors Posit's Linux server guidance. :contentReference[oaicite:4]{index=4}
QUARTO_VERSION="1.8.27"  # set your standard
sudo mkdir -p "/opt/quarto/${QUARTO_VERSION}"
curl -L -o /tmp/quarto.tar.gz \
  "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz"
sudo tar -zxvf /tmp/quarto.tar.gz -C "/opt/quarto/${QUARTO_VERSION}" --strip-components=1
rm /tmp/quarto.tar.gz
sudo ln -sf "/opt/quarto/${QUARTO_VERSION}/bin/quarto" /usr/local/bin/quarto

# ---- 4) Sanity checks ----
pandoc --version
xelatex --version || true
lualatex --version || true
biber --version
quarto check install
```

If you also want a “second PDF engine option” that doesn’t depend on a giant TeX tree, Tectonic is the usual candidate: it’s a single executable, and the official docs describe both a one-liner installer and direct release downloads; you can drop the binary into `/usr/local/bin`. ([Tectonic][3]) In practice, I’d still keep TeX Live installed because journals and edge-case LaTeX packages occasionally want the traditional ecosystem, but having `tectonic` available gives you a fast fallback for many manuscripts.

Once the above is in place, Codex can assume `pandoc`, `quarto`, `latexmk`, `xelatex/lualatex`, and `biber` exist everywhere, and can standardise each paper repo with a tiny Makefile/justfile that emits `dist/paper.pdf` and `dist/paper.docx` deterministically (with the versions you pinned in the bootstrap).

[1]: https://pandoc.org/installing.html "Pandoc - Installing pandoc"
[2]: https://docs.posit.co/resources/install-quarto.html "Install Quarto – Posit Docs"
[3]: https://tectonic-typesetting.github.io/book/latest/installation/ "Installing Tectonic - The Tectonic Typesetting System"

---

Note: I have run the shell commands listed above and success was reported:
LuaTeX is Copyright 2022 Taco Hoekwater and the LuaTeX Team.

biber version: 2.19
Quarto 1.8.27
[✓] Checking Quarto installation......OK
      Version: 1.8.27
      Path: /opt/quarto/1.8.27/bin

[✓] Checking tools....................OK
      TinyTeX: (TeX Live (https://tug.org/texlive) version 2025)
      Chromium: (not installed)

[✓] Checking LaTeX....................OK
      Using: Installation From Path
      Path: /usr/bin
      Version: 2023

[✓] Checking Chrome Headless....................OK
      Chrome:  (not detected)

[✓] Checking basic markdown render....OK

---

## Other advice from a separate ChatGPT thread (I haven't actioned this yet)

Here’s a tight, opinionated setup for a headless Ubuntu “paper server” that installs current Pandoc + Quarto from official binaries, lets you pick a TeX engine (TinyTeX, Tectonic, or TeX Live), and includes a reproducible Bash “doctor” to verify versions/filters and write a pin-able manifest.

---

# A) Quick install (Ubuntu, system-wide)

```bash
# 0) Base tools
sudo apt update && sudo apt install -y wget curl jq ca-certificates build-essential unzip perl git python3 python3-pip

# 1) Pandoc (official .deb from GitHub)
DEB_URL=$(curl -sL https://api.github.com/repos/jgm/pandoc/releases/latest \
  | jq -r '.assets[] | select(.name|test("linux.*amd64.*deb")) | .browser_download_url')
curl -L "$DEB_URL" -o /tmp/pandoc.deb
sudo dpkg -i /tmp/pandoc.deb || sudo apt -f install -y
pandoc --version

# 2) Quarto (official .deb)
curl -LO https://quarto.org/download/latest/quarto-linux-amd64.deb
sudo dpkg -i quarto-linux-amd64.deb || sudo apt -f install -y
quarto --version
```

### Choose ONE TeX path (you can add others later)

**TinyTeX** (smallest, great default; user-scoped, no sudo):

```bash
wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh
echo 'export PATH="$HOME/.TinyTeX/bin/$(uname -m | sed s/x86_64/x86_64-linux/):$PATH"' >> ~/.bashrc
source ~/.bashrc
tlmgr --version
```

**Tectonic** (single binary; deterministic CI):

```bash
curl -LO "https://github.com/tectonic-typesetting/tectonic/releases/latest/download/tectonic-x86_64-unknown-linux-gnu.tar.gz"
tar -xzf tectonic-*-linux-gnu.tar.gz
sudo cp tectonic-*/tectonic /usr/local/bin/
tectonic --version
```

**TeX Live** (max compatibility; system-wide):

```bash
cd /tmp
curl -L -o install-tl-unx.tar.gz https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
zcat < install-tl-unx.tar.gz | tar xf -
cd install-tl-*
sudo perl ./install-tl --no-interaction --scheme=small
# Add to PATH (adjust YYYY):
echo 'export PATH="/usr/local/texlive/$(date +%Y)/bin/x86_64-linux:$PATH"' | sudo tee -a /etc/profile.d/texlive.sh
source /etc/profile.d/texlive.sh
tlmgr --version
```

---

# B) Which TeX to pick?

* **TinyTeX** — ~200–400 MB; easiest + small; good for most Quarto/Pandoc builds.
* **Tectonic** — single binary; reproducible; best when sources are self-contained.
* **TeX Live** — full compatibility; heavier; best when you need obscure packages.

**Recommendation for your server:** start with **TinyTeX**; add **Tectonic** for CI‑strict papers; keep **TeX Live** available if journals/packages get esoteric.

---

# C) “Doctor” script (verifies versions, citeproc, crossref, LaTeX engines; writes a pin-able manifest)

Save as `~/bin/paper-doctor.sh`, then `chmod +x ~/bin/paper-doctor.sh` and run it (optionally pass an output dir).

```bash
#!/usr/bin/env bash
set -euo pipefail
OUT_DIR=${1:-./paper-doctor-output}
mkdir -p "$OUT_DIR"
which_or_none(){ command -v "$1" >/dev/null 2>&1 && command -v "$1" || echo "(not found)"; }

{ echo "== binary versions =="; echo "date: $(date --utc +%Y-%m-%dT%H:%M:%SZ)"; echo;
  echo "pandoc: $(pandoc --version 2>/dev/null | head -n1 || echo 'absent')";
  echo "quarto: $(quarto --version 2>/dev/null | head -n1 || echo 'absent')";
  echo "tectonic: $(tectonic --version 2>/dev/null || echo 'absent')";
  echo "pdflatex: $(pdflatex --version 2>/dev/null | head -n1 || echo 'absent')";
  echo "xelatex: $(xelatex --version 2>/dev/null | head -n1 || echo 'absent')";
  echo "lualatex: $(lualatex --version 2>/dev/null | head -n1 || echo 'absent')";
  echo "tlmgr: $(tlmgr --version 2>/dev/null | head -n1 || echo 'absent')";
  echo "tinytex dir: ${HOME}/.TinyTeX -> $( [ -d "$HOME/.TinyTeX" ] && echo present || echo not-present );";
  echo "pandoc-crossref: $(which_or_none pandoc-crossref)";
} > "$OUT_DIR/versions.txt"

TEST_MD=$(mktemp -t doctor-test-XXXX.md)
cat > "$TEST_MD" <<'MD'
---
title: Test
bibliography: test.bib
---

This cites @doe2020.
MD
cat > test.bib <<'BIB'
@article{doe2020, title={Toy}, author={Doe, J}, year={2020}}
BIB

if pandoc --version >/dev/null 2>&1; then
  if pandoc "$TEST_MD" -o /dev/null --citeproc >/dev/null 2>&1; then
    echo "citeproc: OK" >> "$OUT_DIR/versions.txt"
  else
    echo "citeproc: FAIL or not supported by this pandoc build" >> "$OUT_DIR/versions.txt"
  fi
else
  echo "pandoc: not present, skipping citeproc test" >> "$OUT_DIR/versions.txt"
fi
rm -f "$TEST_MD" test.bib

cat > "$OUT_DIR/min.tex" <<'TEX'
\documentclass{article}\begin{document}Hello\end{document}
TEX
for engine in pdflatex xelatex lualatex tectonic; do
  if command -v "$engine" >/dev/null 2>&1; then
    echo -n "$engine: " >> "$OUT_DIR/latex-test.txt"
    if [ "$engine" = tectonic ]; then
      (cd "$OUT_DIR" && tectonic min.tex >/dev/null 2>&1 && echo "OK" >> latex-test.txt) || echo "FAIL" >> "$OUT_DIR/latex-test.txt"
    else
      (cd "$OUT_DIR" && $engine -interaction=batchmode min.tex >/dev/null 2>&1 && echo "OK" >> latex-test.txt) || echo "FAIL" >> "$OUT_DIR/latex-test.txt"
    fi
  fi
done

if command -v jq >/dev/null 2>&1; then
  echo "Creating manifest with release asset URLs (if available)..." > "$OUT_DIR/manifest.txt"
  PANDOC_JSON=$(curl -s https://api.github.com/repos/jgm/pandoc/releases/latest || true)
  PANDOC_DEB=$(echo "$PANDOC_JSON" | jq -r '.assets[]?.browser_download_url | select(test("linux.*amd64.*deb"))' | head -n1)
  if [ -n "$PANDOC_DEB" ]; then
    echo "pandoc_deb: $PANDOC_DEB" >> "$OUT_DIR/manifest.txt"
    curl -L --silent "$PANDOC_DEB" -o /tmp/pandoc.deb
    sha256sum /tmp/pandoc.deb | awk '{print $1}' >> "$OUT_DIR/manifest.txt"
    rm -f /tmp/pandoc.deb
  else
    echo "pandoc_deb: (not found via API)" >> "$OUT_DIR/manifest.txt"
  fi
  QUARTO_JSON=$(curl -s https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest || true)
  QUARTO_DEB=$(echo "$QUARTO_JSON" | jq -r '.assets[]?.browser_download_url | select(test("linux.*amd64.*deb"))' | head -n1)
  if [ -n "$QUARTO_DEB" ]; then
    echo "quarto_deb: $QUARTO_DEB" >> "$OUT_DIR/manifest.txt"
    curl -L --silent "$QUARTO_DEB" -o /tmp/quarto.deb
    sha256sum /tmp/quarto.deb | awk '{print $1}' >> "$OUT_DIR/manifest.txt"
    rm -f /tmp/quarto.deb
  else
    echo "quarto_deb: (not found via API)" >> "$OUT_DIR/manifest.txt"
  fi
else
  echo "jq not found; skipping release manifest creation" >> "$OUT_DIR/versions.txt"
fi

printf "Doctor run complete; outputs in %s\n" "$OUT_DIR"
ls -lah "$OUT_DIR"
```

> Tip: commit `paper-doctor-output/versions.txt` and `manifest.txt` in each repo (or a shared infra repo) so CI can pin exact assets.

---

# D) Nice-to-haves (system-wide once)

```bash
# pandoc-crossref (filter for figures/tables/eq labels)
CROSS_URL=$(curl -s https://api.github.com/repos/lierdakil/pandoc-crossref/releases/latest \
  | jq -r '.assets[] | select(.name|test("linux.*amd64")) | .browser_download_url' | head -n1)
curl -L "$CROSS_URL" -o /tmp/pandoc-crossref.tar.xz
mkdir -p /tmp/pcr && tar -xJf /tmp/pandoc-crossref.tar.xz -C /tmp/pcr
sudo install /tmp/pcr/pandoc-crossref /usr/local/bin/pandoc-crossref
pandoc-crossref --version | head -n1

# CSL styles & templates cache (optional quality-of-life)
mkdir -p ~/.pandoc/csl ~/.pandoc/templates
```

---

# E) Quarto vs “plain” Markdown (quick answer)

* **Quarto** adds project-aware builds, cross‑format publishing (PDF, Word, HTML), built‑in citations/CSL, figure/table numbering, filters, and native support for R/Python/Julia execution. Great for repos where **code + data + paper** live together and you want repeatable renders and CI.
* **Plain Markdown + Pandoc** is fine for simple docs, but you’ll end up hand‑wiring project workflow, filters, and outputs.
