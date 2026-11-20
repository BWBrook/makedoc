"""Run Pandoc for one profile and post-process the results."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from .docx import normalize_docx
from .layout import render_layout
from .manifest import write_manifest
import yaml

from .prepare import prepare_markdown, structure_metadata
from .profile import Profile
from .report import collect_warnings, warn

PANDOC_FROM = "markdown+yaml_metadata_block+tex_math_dollars+tex_math_single_backslash"
PDF_ENGINE = "xelatex"
PDF_PASSES = 2  # the second pass settles line numbers and page references
FORMATS = ("pdf", "docx")
FONT_VARIABLES = {"main": "mainfont", "sans": "sansfont", "mono": "monofont", "math": "mathfont"}
FILTERS = Path(__file__).parent / "filters"
STRUCTURE_FILTER = FILTERS / "structure.lua"
UNICODE_FILTER = FILTERS / "unicode_fallback.lua"
FILTER_ERROR_PREFIX = "[makedoc-error] "
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
        reported = [
            line.removeprefix(FILTER_ERROR_PREFIX)
            for line in proc.stderr.splitlines()
            if line.startswith(FILTER_ERROR_PREFIX)
        ]
        if reported:
            raise BuildError("\n".join(reported))
        raise BuildError(f"Pandoc failed while building {label}:\n{proc.stderr.strip()}")
    return _pandoc_warnings(proc.stderr)


def _resolve(profile: Profile, work: Path) -> tuple[Path, list[str]]:
    """Parse the sources once and arrange them for the profile; both formats build from this."""
    prepared = work / "prepared.md"
    prepared.write_text(prepare_markdown(profile), encoding="utf-8")
    settings = work / "structure.yaml"
    settings.write_text(yaml.safe_dump(structure_metadata(profile), allow_unicode=True), encoding="utf-8")
    resolved = work / "resolved.json"
    warnings = _run_pandoc(
        [
            str(prepared),
            "--from", PANDOC_FROM,
            "--to", "json",
            f"--metadata-file={settings}",
            f"--lua-filter={STRUCTURE_FILTER}",
            "-o", str(resolved),
        ],
        "the document structure",
    )
    return resolved, warnings


def document_images(resolved: Path) -> list[Path]:
    """Local image files used by the resolved document, in order of first use."""
    found: list[Path] = []

    def visit(node: object) -> None:
        if isinstance(node, dict):
            if node.get("t") == "Image":
                path = Path(node["c"][2][0])
                if path.is_absolute() and path.resolve() not in found:
                    found.append(path.resolve())
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(json.loads(resolved.read_text(encoding="utf-8"))["blocks"])
    return found


def _common_args(profile: Profile, resolved: Path) -> list[str]:
    args = [
        str(resolved),
        "--from", "json",
        "--citeproc",
        "--bibliography", profile.bibliography,
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


def _build_pdf(profile: Profile, resolved: Path, work: Path) -> tuple[Path, list[str]]:
    bad = invisible_pngs(document_images(resolved))
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
    args = _common_args(profile, resolved) + [
        # Not --include-in-header: that would discard the manuscript's own header-includes.
        "--metadata", f"makedoc-layout={layout}",
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
            + ". In body text, write them as TeX math (for example $\\le$) or set `fonts.main` "
            "to a font that has them. In a code span, set `fonts.mono` or remove them."
        )
    return staged, warnings


def _with_raster_images(resolved: Path, work: Path) -> Path:
    """Word cannot display PDF images, so give the DOCX a 300 dpi PNG of each one."""
    document = json.loads(resolved.read_text(encoding="utf-8"))
    converted: dict[str, str] = {}

    def visit(node: object) -> None:
        if isinstance(node, dict):
            if node.get("t") == "Image" and node["c"][2][0].lower().endswith(".pdf"):
                source = node["c"][2][0]
                if source not in converted:
                    converted[source] = _rasterize(Path(source), work / "raster" / str(len(converted)))
                node["c"][2][0] = converted[source]
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(document["blocks"])
    if not converted:
        return resolved
    target = work / "resolved_docx.json"
    target.write_text(json.dumps(document), encoding="utf-8")
    return target


def _rasterize(source: Path, stem: Path) -> str:
    if not shutil.which("pdftoppm"):
        warn(f"pdftoppm (Poppler) is not installed, so {source.name} stays a PDF image, which Word "
             "cannot display. Install Poppler or supply a PNG.")
        return str(source)
    stem.parent.mkdir(exist_ok=True)
    proc = subprocess.run(
        ["pdftoppm", "-png", "-r", "300", "-singlefile", str(source), str(stem)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise BuildError(f"Could not convert {source} to PNG for the DOCX:\n{proc.stderr.strip()}")
    return f"{stem}.png"


def _build_docx(profile: Profile, resolved: Path, work: Path) -> tuple[Path, list[str]]:
    staged = work / "out.docx"
    resolved = _with_raster_images(resolved, work)
    warnings = _run_pandoc(_common_args(profile, resolved) + ["-o", str(staged)], "DOCX")
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
    with collect_warnings() as own_warnings, _work_directory(workdir) as work:
        try:
            resolved, structure_warnings = _resolve(profile, work)
        except ValueError as exc:
            raise BuildError(str(exc)) from exc

        Path(profile.output_dir).mkdir(parents=True, exist_ok=True)
        outputs: list[Path] = []
        pandoc_warnings: list[str] = []
        builders = {"pdf": (_build_pdf, profile.pdf_out), "docx": (_build_docx, profile.docx_out)}
        for fmt in formats:
            builder, target = builders[fmt]
            try:
                staged, fmt_warnings = builder(profile, resolved, work)
            except ValueError as exc:
                raise BuildError(str(exc)) from exc
            shutil.move(staged, target)
            outputs.append(Path(target))
            pandoc_warnings.extend(f"{fmt}: {w}" for w in fmt_warnings)

        warnings = own_warnings + structure_warnings + pandoc_warnings
        manifest = write_manifest(profile, config_path, outputs, warnings, document_images(resolved))
        return BuildResult(profile=profile, outputs=outputs, manifest=manifest, warnings=warnings)


@contextmanager
def _work_directory(workdir: Path | None) -> Iterator[Path]:
    if workdir is not None:
        workdir.mkdir(parents=True, exist_ok=True)
        yield workdir
        return
    with tempfile.TemporaryDirectory(prefix="makedoc-") as temp:
        yield Path(temp)
