"""Run Pandoc for one profile and post-process the results."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .docx import normalize_docx
from .layout import render_layout
from .manifest import write_manifest
from .prepare import image_resources, prepare_markdown
from .profile import Profile

log = logging.getLogger("makedoc")

PANDOC_FROM = "markdown+yaml_metadata_block+tex_math_dollars+tex_math_single_backslash"
PDF_ENGINE = "xelatex"
PDF_PASSES = 2  # the second pass settles line numbers and page references
FORMATS = ("pdf", "docx")
FONT_VARIABLES = {"main": "mainfont", "sans": "sansfont", "mono": "monofont", "math": "mathfont"}
UNICODE_FILTER = Path(__file__).parent / "filters" / "unicode_fallback.lua"
MISSING_CHARACTER_RE = re.compile(r"Missing character: There is no (\S+) \((U\+[0-9A-F]+)\)")


class BuildError(Exception):
    """A build failed for a reason the author can act on."""


@dataclass
class BuildResult:
    profile: Profile
    outputs: list[Path]
    manifest: Path
    warnings: list[str] = field(default_factory=list)


def require_tools(formats: tuple[str, ...]) -> None:
    needed = ["pandoc"] + ([PDF_ENGINE] if "pdf" in formats else [])
    missing = [tool for tool in needed if shutil.which(tool) is None]
    if missing:
        raise BuildError(f"Required tool not found on PATH: {', '.join(missing)}. Run `makedoc doctor`.")


def _pandoc_warnings(stderr: str) -> list[str]:
    warnings: list[str] = []
    for line in stderr.splitlines():
        if line.startswith("[WARNING]"):
            warnings.append(line.removeprefix("[WARNING]").strip())
        elif warnings and line.startswith("  "):
            warnings[-1] += " " + line.strip()
    return list(dict.fromkeys(warnings))


def _run_pandoc(args: list[str], label: str) -> list[str]:
    proc = subprocess.run(["pandoc", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise BuildError(f"Pandoc failed while building {label}:\n{proc.stderr.strip()}")
    return _pandoc_warnings(proc.stderr)


def _common_args(profile: Profile, prepared: Path) -> list[str]:
    args = [
        str(prepared),
        "--from", PANDOC_FROM,
        "--citeproc",
        "--bibliography", profile.bibliography,
        f"--resource-path={os.pathsep.join(profile.resource_paths)}",
    ]
    if profile.csl:
        args += ["--csl", profile.csl]
    return args


def invisible_pngs(paths: list[Path]) -> list[Path]:
    """PNG files that xelatex embeds fully transparent: 16 bits per channel with alpha."""
    found = []
    for path in paths:
        if path.suffix.lower() != ".png" or not path.is_file():
            continue
        header = path.read_bytes()[:26]
        if header[:8] == b"\x89PNG\r\n\x1a\n" and header[24] == 16 and header[25] in (4, 6):
            found.append(path)
    return found


def _build_pdf(profile: Profile, prepared: Path, work: Path) -> tuple[Path, list[str]]:
    bad = invisible_pngs(image_resources([Path(item) for item in profile.manuscript_sources]))
    if bad:
        raise BuildError(
            "These PNG files are 16-bit with an alpha channel, which xelatex renders invisible "
            "in the PDF: " + ", ".join(str(path) for path in bad)
            + ". Re-save them as 8-bit, for example `magick in.png -depth 8 out.png`."
        )
    layout = work / "layout.tex"
    layout.write_text(render_layout(profile), encoding="utf-8")
    latex_dir = work / "latex"
    latex_dir.mkdir(exist_ok=True)
    staged = work / "out.pdf"
    args = _common_args(profile, prepared) + [
        f"--include-in-header={layout}",
        f"--lua-filter={UNICODE_FILTER}",
        f"--pdf-engine={PDF_ENGINE}",
        f"--pdf-engine-opt=-output-directory={latex_dir}",
        "-o", str(staged),
    ]
    for key, variable in FONT_VARIABLES.items():
        if key in profile.fonts:
            args += ["-V", f"{variable}={profile.fonts[key]}"]

    warnings: list[str] = []
    for _ in range(PDF_PASSES):
        warnings = _run_pandoc(args, "PDF")

    missing = sorted({m.group(1) + " " + m.group(2) for w in warnings if (m := MISSING_CHARACTER_RE.search(w))})
    if missing:
        raise BuildError(
            "The PDF font has no glyph for these characters, so they would be absent from the PDF: "
            + ", ".join(missing)
            + ". Write them as TeX math (for example $\\le$), or set `fonts.main` in the profile "
            "to a font that has them."
        )
    return staged, warnings


def _build_docx(profile: Profile, prepared: Path, work: Path) -> tuple[Path, list[str]]:
    staged = work / "out.docx"
    warnings = _run_pandoc(_common_args(profile, prepared) + ["-o", str(staged)], "DOCX")
    normalize_docx(staged, profile)
    return staged, warnings


def build_profile(
    profile: Profile,
    config_path: Path,
    formats: tuple[str, ...] = FORMATS,
    workdir: Path | None = None,
) -> BuildResult:
    """Build the requested formats for one profile.

    Intermediates go to `workdir` when given (and are kept), otherwise to a temporary
    directory. Outputs are moved into place only after each format succeeds.
    """
    require_tools(formats)
    capture = _WarningCapture()
    log.addHandler(capture)
    temp: tempfile.TemporaryDirectory[str] | None = None
    try:
        if workdir is None:
            temp = tempfile.TemporaryDirectory(prefix="makedoc-")
            work = Path(temp.name)
        else:
            work = workdir
            work.mkdir(parents=True, exist_ok=True)

        prepared = work / "prepared.md"
        try:
            prepared.write_text(prepare_markdown(profile), encoding="utf-8")
        except ValueError as exc:
            raise BuildError(str(exc)) from exc

        output_dir = Path(profile.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs: list[Path] = []
        warnings: list[str] = []
        builders = {"pdf": (_build_pdf, profile.pdf_out), "docx": (_build_docx, profile.docx_out)}
        for fmt in formats:
            builder, target = builders[fmt]
            try:
                staged, fmt_warnings = builder(profile, prepared, work)
            except ValueError as exc:
                raise BuildError(str(exc)) from exc
            shutil.move(staged, target)
            outputs.append(Path(target))
            warnings.extend(f"{fmt}: {w}" for w in fmt_warnings)

        warnings = capture.messages + warnings
        manifest = write_manifest(profile, config_path, outputs, warnings)
        return BuildResult(profile=profile, outputs=outputs, manifest=manifest, warnings=warnings)
    finally:
        log.removeHandler(capture)
        if temp is not None:
            temp.cleanup()


class _WarningCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())
