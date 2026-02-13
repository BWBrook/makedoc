#!/usr/bin/env python3
"""Prepare concatenated markdown for build.

The source pipeline now normalizes figure blocks and reference placement:
if an author-supplied ``References`` heading exists, we inject the
Pandoc-style anchor div (`<div id="refs"></div>`) at that location so the
bibliography is rendered there.

Figure policy is driven by profile settings:
- `placement=pages` (default): extracted figure blocks are appended after references
  on dedicated figure pages, with one page break per figure. Supplementary figures
  are inserted after main figures and separated by a `Supplementary Information` heading.
- `placement=inline`: extracted figure blocks are inserted at a configurable
  placeholder (`<div id="<placeholder_id>"></div>`), if present.
- `placement=captions_page`: adds a dedicated "Figure Captions" page and then
  successive figure pages with title text only. Supplementary figures are appended
  after a `Supplementary Information` heading.
- `caption_position` controls whether a figure caption sits above or below the image.
- figures with IDs ending in `-s<number>` are treated as supplementary and rendered
  after main figures.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from build_profile import load_config, resolve_profile


REFERENCE_SECTION_RE = re.compile(r"^(?P<prefix>#{1,6})\s+references\b", re.IGNORECASE)
FIGURE_LINE_RE = re.compile(
    r"""^(?P<prefix>\s*)!\[(?P<alt>.*?)\]\((?P<src>[^)\n]+)\)\{(?P<attrs>[^\}]*)\}\s*$"""
)
FIGURE_ID_RE = re.compile(r"#(?P<id>[\w.-]+)")
SUPPLEMENTARY_ID_RE = re.compile(r"-s\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class FigureBlock:
    raw: str
    figure_id: str
    title: str
    src: str
    attrs: str


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
        help="Profile name to prepare markdown for (default: default_profile).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for the prepared markdown file.",
    )
    return parser.parse_args()


def has_refs_anchor(lines: list[str], index: int) -> bool:
    for offset in range(0, 8):
        if index + offset >= len(lines):
            break
        line = lines[index + offset].strip().lower()
        if "id=\"refs\"" in line or "id='refs'" in line:
            return True
    return False


def reference_placement(lines: list[str]) -> list[str]:
    out_lines: list[str] = []
    refs_injected = False

    for index, line in enumerate(lines):
        if not refs_injected and REFERENCE_SECTION_RE.match(line.strip()):
            refs_injected = True
            out_lines.append(line)
            if not has_refs_anchor(lines, index):
                out_lines.append("")
                out_lines.append('<div id="refs"></div>')
            continue
        out_lines.append(line)

    return out_lines


def extract_figure_id(attrs: str) -> str:
    match = FIGURE_ID_RE.search(attrs or "")
    if not match:
        return ""
    return match.group("id")


def is_figure_placeholder(line: str, placeholder_id: str) -> bool:
    pattern = re.compile(
        rf"^\s*<div\s+[^>]*\bid\s*=\s*['\"]{re.escape(placeholder_id)}['\"][^>]*>"
        rf"(?:\s*</div>\s*)?$",
        re.IGNORECASE,
    )
    return bool(pattern.match(line))


def extract_figures(lines: list[str]) -> tuple[list[str], list[FigureBlock]]:
    out_lines: list[str] = []
    figures: list[FigureBlock] = []
    in_code_fence = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            out_lines.append(line)
            continue

        if in_code_fence:
            out_lines.append(line)
            continue

        match = FIGURE_LINE_RE.match(line)
        if not match:
            out_lines.append(line)
            continue

        attrs = (match.group("attrs") or "").strip()
        figure_id = extract_figure_id(attrs)
        figures.append(
            FigureBlock(
                raw=line.rstrip(),
                figure_id=figure_id,
                title=(match.group("alt") or "").strip(),
                src=(match.group("src") or "").strip(),
                attrs=attrs,
            )
        )
        if not figure_id:
            print(
                f"Warning: figure line has no explicit ID token in attrs; this can break "
                f"anchor links: {line.rstrip()}",
            )

    return out_lines, figures


def _caption_line(label: str) -> str:
    return f"**{label}.**"


def _title_line(label: str, figure: FigureBlock) -> str:
    title = (figure.title or "").strip()
    if title:
        return f"**{label}.** {title}"
    return f"**{label}.**"


def _ordered_figures(figures: list[FigureBlock]) -> list[tuple[str, FigureBlock]]:
    mains: list[FigureBlock] = []
    supplements: list[FigureBlock] = []
    for figure in figures:
        if SUPPLEMENTARY_ID_RE.search(figure.figure_id):
            supplements.append(figure)
        else:
            mains.append(figure)

    ordered: list[tuple[str, FigureBlock]] = []
    for main_index, figure in enumerate(mains, start=1):
        ordered.append((f"Fig. {main_index}", figure))

    for supplement_index, figure in enumerate(supplements, start=1):
        label = figure.figure_id
        if label and "-s" in label.lower():
            suffix = label.split("-s", 1)[1]
            if suffix:
                ordered.append((f"Fig. S{suffix}", figure))
                continue
        ordered.append((f"Fig. S{supplement_index}", figure))

    return ordered


def _ordered_main_and_supplementary_figures(
    figures: list[FigureBlock],
) -> tuple[list[tuple[str, FigureBlock]], list[tuple[str, FigureBlock]]]:
    ordered = _ordered_figures(figures)
    main_figures: list[tuple[str, FigureBlock]] = []
    supplementary_figures: list[tuple[str, FigureBlock]] = []
    for label, figure in ordered:
        if label.startswith("Fig. S"):
            supplementary_figures.append((label, figure))
        else:
            main_figures.append((label, figure))
    return main_figures, supplementary_figures


def _build_figure_block_with_caption_position(
    label: str,
    figure: FigureBlock,
    caption_position: str,
) -> str:
    caption = _caption_line(label)
    if caption_position == "bottom":
        return f"{figure.raw}\n\n{caption}"
    return f"{caption}\n\n{figure.raw}"


def _image_without_caption_text(figure: FigureBlock) -> str:
    attrs_block = f"{{{figure.attrs}}}" if figure.attrs else ""
    # Empty alt text suppresses auto-generated "Figure N:" caption text in Pandoc output.
    return f"![]({figure.src}){attrs_block}"


def build_figure_blocks(
    figures: list[FigureBlock],
    caption_position: str,
    placement: str,
) -> str:
    if not figures:
        return ""

    ordered = _ordered_figures(figures)
    main_figures, supplementary_figures = _ordered_main_and_supplementary_figures(figures)
    blocks: list[str] = []

    if placement == "captions_page":
        blocks.append("\\clearpage\n## Figure Captions")
        for label, figure in ordered:
            blocks.append(_title_line(label, figure))
        for label, figure in main_figures:
            blocks.append(f"\\clearpage\n{_caption_line(label)}\n\n{_image_without_caption_text(figure)}")
        if supplementary_figures:
            blocks.append("\\clearpage\n## Supplementary Information")
            for label, figure in supplementary_figures:
                blocks.append(f"\\clearpage\n{_caption_line(label)}\n\n{_image_without_caption_text(figure)}")
        return "\n\n".join(blocks) + ("\n" if blocks else "")

    if placement == "inline":
        for label, figure in ordered:
            block = _build_figure_block_with_caption_position(label, figure, caption_position)
            blocks.append(block.strip())
        return "\n\n".join(blocks) + ("\n" if blocks else "")

    for label, figure in main_figures:
        blocks.append(f"\\clearpage\n{_build_figure_block_with_caption_position(label, figure, caption_position)}")
    if supplementary_figures:
        blocks.append("\\clearpage\n## Supplementary Information")
        for label, figure in supplementary_figures:
            blocks.append(
                f"\\clearpage\n{_build_figure_block_with_caption_position(label, figure, caption_position)}"
            )
    if not blocks:
        return ""

    return "\n\n".join(blocks) + ("\n" if blocks else "")


def apply_figure_placement(
    lines: list[str],
    figures: list[FigureBlock],
    profile,
) -> list[str]:
    if not figures:
        return lines

    figure_blocks = build_figure_blocks(
        figures=figures,
        caption_position=profile.figures.caption_position,
        placement=profile.figures.placement,
    )
    if not figure_blocks:
        return lines

    if profile.figures.placement == "inline":
        placeholder = profile.figures.placeholder_id
        in_code_fence = False
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_fence = not in_code_fence
            if in_code_fence:
                continue

            if is_figure_placeholder(line, placeholder):
                new_lines = lines[:index] + [figure_blocks] + lines[index + 1 :]
                return new_lines
        print(
            f"Warning: no placeholder <div id=\"{placeholder}\"></div> found; appending figures "
            "at end of prepared manuscript.",
        )

    # Default behavior: place all figure blocks after all manuscript content.
    return lines + ["", figure_blocks]


def load_markdown_sources(sources: list[str]) -> str:
    chunks = [Path(raw).read_text(encoding="utf-8").rstrip() for raw in sources]
    # Keep a readable separation between merged files.
    return "\n\n".join(chunks) + "\n"


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))
    profile = resolve_profile(config, args.profile.strip() if args.profile else None)

    raw = load_markdown_sources(profile.manuscript_sources)
    lines = raw.splitlines()
    lines_without_figures, figures = extract_figures(lines)
    refs_lines = reference_placement(lines_without_figures)
    prepared_lines = apply_figure_placement(
        lines=refs_lines,
        figures=figures,
        profile=profile,
    )
    prepared = "\n".join(prepared_lines) + "\n"

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prepared, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
