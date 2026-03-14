#!/usr/bin/env python3
"""Render LaTeX preamble for profile-specific formatting."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from build_profile import load_config, resolve_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="settings/build.yaml",
        help="Path to build profile YAML (default: settings/build.yaml).",
    )
    parser.add_argument(
        "--profile",
        default="",
        help="Profile name to render layout for (default: default_profile).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for the generated LaTeX preamble include file.",
    )
    return parser.parse_args()


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


def line_numbering_block(mode: str) -> list[str]:
    if mode == "none":
        return []

    if not _has_tex_package("lineno.sty"):
        print(
            "Warning: LaTeX package 'lineno' not found; line numbering is disabled."
            " Install texlive-latex-extra for line-numbered output.",
            file=sys.stderr,
        )
        return [
            "% Line numbering",
            "\\typeout{Warning: lineno package not found (kpsewhich). Install texlive-latex-extra to enable line numbering.}",
        ]

    lines = [
        "% Line numbering",
        "\\usepackage{lineno}",
        "\\linenumbers",
    ]
    if mode == "page":
        lines.append("\\pagewiselinenumbers")
    elif mode == "section":
        if _has_tex_package("etoolbox.sty"):
            lines.extend([
                "\\usepackage{etoolbox}",
                "\\AtBeginEnvironment{section}{\\resetlinenumber}",
            ])
        else:
            print(
                "Warning: LaTeX package 'etoolbox' not found; section line-number"
                " resets unavailable, so continuous numbering will be used instead.",
                file=sys.stderr,
            )
            lines.append(
                "\\typeout{Warning: etoolbox package not found; section line-number reset unavailable.}"
            )
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

    if not _has_tex_package("geometry.sty"):
        print(
            "Warning: LaTeX package 'geometry' not found; using LaTeX defaults for"
            " margins from profile settings.",
            file=sys.stderr,
        )
        return [
            "% Margins / geometry",
            "\\typeout{Warning: geometry package not found; using LaTeX default margins.}",
        ]

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


def build_block(profile: Any) -> list[str]:
    lines: list[str] = [
        "% Auto-generated by render_pdf_layout.py",
        "% Style controls driven by settings/build.yaml",
    ]
    lines.extend(page_numbers_block(profile.page_numbers))
    lines.extend(line_spacing_block(profile.line_spacing))
    lines.extend(line_numbering_block(profile.line_numbering))
    lines.extend(margins_block(profile))
    lines.extend(heading_layout_block())
    return lines


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    output_path = Path(args.output)

    try:
        config = load_config(config_path)
        profile_name = args.profile.strip() if args.profile else None
        profile = resolve_profile(config, profile_name, config_path=config_path)
    except Exception as exc:  # pragma: no cover - script-level error propagation is intentional
        print(f"Error: {exc}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(build_block(profile)) + "\n"
    output_path.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
