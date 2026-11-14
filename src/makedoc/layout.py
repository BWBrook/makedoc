"""Render LaTeX preamble for profile-specific formatting."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


def page_numbers_block(mode: str) -> list[str]:
    if mode == "lower_right":
        return [
            "% Page numbering (lower-right).",
            "\\makeatletter",
            "\\def\\ps@makedoclowerright{%",
            "  \\def\\@oddhead{}%",
            "  \\def\\@evenhead{}%",
            "  \\def\\@oddfoot{\\hfill\\thepage}%",
            "  \\def\\@evenfoot{\\hfill\\thepage}%",
            "  \\def\\@mkboth##1##2{}%",
            "}",
            "\\pagestyle{makedoclowerright}",
            "\\makeatother",
        ]
    if mode == "none":
        return [
            "% Page numbering disabled.",
            "\\pagestyle{empty}",
        ]
    raise ValueError(f"Unsupported page number mode: {mode}")


def line_spacing_block(mode: str) -> list[str]:
    mapping = {
        "single": "1",
        "1.1": "1.05",
        "1.25": "1.125",
        "1.5": "1.25",
        "2": "2",
    }
    command = mapping.get(mode)
    if command is None:
        raise ValueError(f"Unsupported line spacing: {mode}")
    return [
        "% Line spacing",
        "\\AtBeginDocument{% line spacing block",
        f"  \\linespread{{{command}}}%",
        "  \\selectfont",
        "}",
    ]


def _has_tex_package(package_name: str) -> bool:
    kpsewhich_candidates: list[str] = []
    for engine in ("xelatex", "pdflatex", "lualatex"):
        tex_engine = shutil.which(engine)
        if not tex_engine:
            continue
        engine_kpsewhich = str(Path(tex_engine).with_name("kpsewhich"))
        if Path(engine_kpsewhich).is_file():
            kpsewhich_candidates.append(engine_kpsewhich)

    if not kpsewhich_candidates:
        candidate = shutil.which("kpsewhich")
        if candidate:
            kpsewhich_candidates.append(candidate)

    if not kpsewhich_candidates:
        return False

    try:
        for kpsewhich in kpsewhich_candidates:
            result = subprocess.run(
                [kpsewhich, package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                text=True,
            )
            if (result.stdout or "").strip():
                return True
    except OSError:
        return False

    return False


def _require_tex_package(name: str, purpose: str) -> None:
    if not _has_tex_package(f"{name}.sty"):
        raise ValueError(
            f"LaTeX package '{name}' is required for {purpose} but was not found. "
            "Run `makedoc doctor` for install hints."
        )


def line_numbering_block(mode: str) -> list[str]:
    if mode == "none":
        return []

    _require_tex_package("lineno", "line numbering")

    lines = [
        "% Line numbering",
        "\\usepackage{lineno}",
        "\\linenumbers",
    ]
    if mode == "page":
        lines.append("\\pagewiselinenumbers")
    elif mode == "section":
        _require_tex_package("etoolbox", "per-section line numbering")
        lines.extend([
            "\\usepackage{etoolbox}",
            "\\AtBeginEnvironment{section}{\\resetlinenumber}",
        ])
    elif mode == "continuous":
        pass
    else:
        raise ValueError(f"Unsupported line numbering mode: {mode}")
    return lines


def _format_length(value: float, unit: str) -> str:
    as_text = f"{value:g}"
    return f"{as_text}{unit}"


def margins_block(profile: Any) -> list[str]:
    if not hasattr(profile, "margins"):
        return []

    _require_tex_package("geometry", "page margins")

    margins = profile.margins
    unit = getattr(margins, "unit", "cm")
    paper_size = getattr(margins, "paper_size", "a4")
    top = getattr(margins, "top", 1.5)
    right = getattr(margins, "right", 1.5)
    bottom = getattr(margins, "bottom", 1.5)
    left = getattr(margins, "left", 1.5)

    return [
        "% Margins / geometry",
        (
            "\\usepackage["
            f"{paper_size}paper, "
            f"top={_format_length(float(top), unit)}, "
            f"bottom={_format_length(float(bottom), unit)}, "
            f"left={_format_length(float(left), unit)}, "
            f"right={_format_length(float(right), unit)}"
            "]{geometry}"
        ),
    ]


def heading_layout_block() -> list[str]:
    return [
        "% Block-style lower-level headings",
        "\\makeatletter",
        (
            "\\renewcommand\\paragraph{\\@startsection{paragraph}{4}{\\z@}"
            "{-3.25ex \\@plus -1ex \\@minus -.2ex}"
            "{0.8ex \\@plus .2ex}"
            "{\\normalfont\\normalsize\\bfseries}}"
        ),
        (
            "\\renewcommand\\subparagraph{\\@startsection{subparagraph}{5}{\\z@}"
            "{-3.25ex \\@plus -1ex \\@minus -.2ex}"
            "{0.8ex \\@plus .2ex}"
            "{\\normalfont\\normalsize\\bfseries}}"
        ),
        "\\makeatother",
    ]


def unicode_fallback_block() -> list[str]:
    return [
        "% Used by filters/unicode_fallback.lua: the font's own glyph if present, else a fallback.",
        "\\newcommand{\\makedocchar}[2]{\\iffontchar\\font\"#1 \\char\"#1\\relax\\else#2\\fi}",
    ]


def build_block(profile: Any) -> list[str]:
    lines: list[str] = [
        "% Generated by makedoc from the build profile.",
        "% Support explicit source pagination with \\Needspace.",
        "\\usepackage{needspace}",
    ]
    lines.extend(page_numbers_block(profile.page_numbers))
    lines.extend(line_spacing_block(profile.line_spacing))
    lines.extend(line_numbering_block(profile.line_numbering))
    lines.extend(margins_block(profile))
    lines.extend(heading_layout_block())
    lines.extend(unicode_fallback_block())
    return lines


def render_layout(profile: Any) -> str:
    return "\n".join(build_block(profile)) + "\n"


