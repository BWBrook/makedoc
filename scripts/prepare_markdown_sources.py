#!/usr/bin/env python3
"""Prepare concatenated markdown for build.

The source pipeline now normalizes figure blocks and reference placement:
if an author-supplied ``References`` heading exists, we inject the
Pandoc-style anchor div (`<div id="refs"></div>`) at that location so the
bibliography is rendered there.
If profile-level author metadata is configured, an author block is injected at
`<div id="authors"></div>`; if that placeholder is absent, insertion falls back
to immediately after the first `#` title heading.

Default section layout policy:
- when author metadata is injected, a page break is inserted after the author block
- the first `Introduction` heading is forced onto a new page
- level-2 headings are separated by at least two blank lines in prepared markdown

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

from markdown_scan import scan_markdown_lines
import yaml

from build_profile import load_config, resolve_profile


REFERENCE_SECTION_RE = re.compile(r"^(?P<prefix>#{1,6})\s+references\b", re.IGNORECASE)
FIGURE_LINE_RE = re.compile(
    r"""^(?P<prefix>\s*)!\[(?P<alt>.*?)\]\((?P<src>[^)\n]+)\)\{(?P<attrs>[^\}]*)\}\s*$"""
)
FIGURE_ID_RE = re.compile(r"#(?P<id>[\w.-]+)")
IMAGE_REFERENCE_RE = re.compile(r"!\[[^\]]*\]\((?P<src>[^)\n]+)\)")
SUPPLEMENTARY_ID_RE = re.compile(r"-s\d+$", re.IGNORECASE)
DOCX_PAGEBREAK_OPENXML = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
TITLE_HEADING_RE = re.compile(r"^\s*#\s+\S+")
AUTHORS_PLACEHOLDER_RE = re.compile(
    r"^\s*<div\s+[^>]*\bid\s*=\s*['\"]authors['\"][^>]*>(?:\s*</div>\s*)?$",
    re.IGNORECASE,
)
INTRO_SECTION_RE = re.compile(r"^\s*#{1,6}\s+introduction\b", re.IGNORECASE)
MAJOR_SECTION_RE = re.compile(r"^\s*##\s+\S+")


@dataclass(frozen=True)
class FigureBlock:
    raw: str
    figure_id: str
    title: str
    src: str
    attrs: str


@dataclass(frozen=True)
class AuthorRecord:
    name: str
    affiliations: list[str]
    corresponding: bool
    email: str
    orcid: str


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


def _as_nonempty_str(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Author metadata '{label}' must be a non-empty string.")
    return value.strip()


def _load_author_metadata(path: Path) -> tuple[str, list[AuthorRecord], dict[str, str]]:
    if not path.exists():
        raise ValueError(f"Author metadata file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise ValueError("Author metadata root must be a mapping.")

    title_note = str(payload.get("title_note", "") or "").strip()

    affiliations_raw = payload.get("affiliations")
    if not isinstance(affiliations_raw, dict) or not affiliations_raw:
        raise ValueError("Author metadata key 'affiliations' must be a non-empty mapping.")
    affiliations: dict[str, str] = {}
    for aff_id, aff_text in affiliations_raw.items():
        aff_key = _as_nonempty_str(aff_id, label="affiliations key")
        affiliations[aff_key] = _as_nonempty_str(
            aff_text, label=f"affiliations.{aff_key}"
        )

    authors_raw = payload.get("authors")
    if not isinstance(authors_raw, list) or not authors_raw:
        raise ValueError("Author metadata key 'authors' must be a non-empty list.")

    authors: list[AuthorRecord] = []
    for index, item in enumerate(authors_raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Author metadata authors[{index}] must be a mapping.")

        name = _as_nonempty_str(item.get("name"), label=f"authors[{index}].name")
        aff_ids_raw = item.get("affiliations")
        if not isinstance(aff_ids_raw, list) or not aff_ids_raw:
            raise ValueError(
                f"Author metadata authors[{index}].affiliations must be a non-empty list."
            )

        aff_ids: list[str] = []
        for aff_id in aff_ids_raw:
            aff_key = _as_nonempty_str(
                aff_id, label=f"authors[{index}].affiliations item"
            )
            if aff_key not in affiliations:
                raise ValueError(
                    f"Author metadata authors[{index}] references unknown affiliation ID '{aff_key}'."
                )
            aff_ids.append(aff_key)

        corresponding = bool(item.get("corresponding", False))
        email = str(item.get("email", "") or "").strip()
        orcid = str(item.get("orcid", "") or "").strip()

        authors.append(
            AuthorRecord(
                name=name,
                affiliations=aff_ids,
                corresponding=corresponding,
                email=email,
                orcid=orcid,
            )
        )

    return title_note, authors, affiliations


def _author_block_lines(author_metadata_path: str) -> list[str]:
    title_note, authors, affiliations = _load_author_metadata(Path(author_metadata_path))

    ordered_affiliations: list[str] = []
    for author in authors:
        for aff_id in author.affiliations:
            if aff_id not in ordered_affiliations:
                ordered_affiliations.append(aff_id)

    if not ordered_affiliations:
        raise ValueError(
            "Author metadata includes no referenced affiliations. Check authors.affiliations."
        )

    aff_number = {aff_id: idx for idx, aff_id in enumerate(ordered_affiliations, start=1)}

    author_fragments: list[str] = []
    corresponding_contacts: list[str] = []
    for author in authors:
        superscripts = ",".join(str(aff_number[aff_id]) for aff_id in author.affiliations)
        display_name = f"{author.name}*" if author.corresponding else author.name
        author_text = f"{display_name}^{superscripts}^"
        if author.orcid:
            author_text = f"{author_text} (ORCID: {author.orcid})"
        author_fragments.append(author_text)

        if author.corresponding:
            if author.email:
                corresponding_contacts.append(f"{author.name} ({author.email})")
            else:
                corresponding_contacts.append(author.name)

    lines: list[str] = [", ".join(author_fragments), ""]

    if title_note:
        lines.append(f"*{title_note}*")
        lines.append("")

    for aff_id in ordered_affiliations:
        lines.append(f"{aff_number[aff_id]}. {affiliations[aff_id]}")

    if corresponding_contacts:
        lines.append("")
        label = "**Corresponding author:**" if len(corresponding_contacts) == 1 else "**Corresponding authors:**"
        lines.append(f"{label} {'; '.join(corresponding_contacts)}")

    return lines


def apply_author_metadata(lines: list[str], author_metadata_path: str) -> list[str]:
    if not author_metadata_path.strip():
        return lines

    block_lines = _author_block_lines(author_metadata_path)

    in_code_fence = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
        if in_code_fence:
            continue
        if AUTHORS_PLACEHOLDER_RE.match(line):
            return (
                lines[:index]
                + block_lines
                + [""]
                + _page_break_lines()
                + [""]
                + lines[index + 1 :]
            )

    in_code_fence = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
        if in_code_fence:
            continue
        if TITLE_HEADING_RE.match(line):
            return (
                lines[: index + 1]
                + [""]
                + block_lines
                + [""]
                + _page_break_lines()
                + [""]
                + lines[index + 1 :]
            )

    raise ValueError(
        "author_metadata is set but no insertion point found. Add <div id=\"authors\"></div> "
        "or ensure the manuscript starts with a '# Title' heading."
    )


def has_refs_anchor(lines: list[str], index: int) -> bool:
    for offset in range(0, 8):
        if index + offset >= len(lines):
            break
        line = lines[index + offset].strip().lower()
        if "id=\"refs\"" in line or "id='refs'" in line:
            return True
    return False


def _is_page_break_line(line: str) -> bool:
    stripped = line.strip()
    return stripped == "\\clearpage" or 'w:type="page"' in stripped


def _has_trailing_page_break(lines: list[str]) -> bool:
    cursor = len(lines) - 1
    saw_page_break_token = False

    while cursor >= 0:
        stripped = lines[cursor].strip()
        if not stripped:
            cursor -= 1
            continue
        if _is_page_break_line(lines[cursor]):
            saw_page_break_token = True
            cursor -= 1
            continue
        if stripped.startswith("```"):
            cursor -= 1
            continue
        return saw_page_break_token

    return saw_page_break_token


def _page_break_lines() -> list[str]:
    return _page_break_block().splitlines()


def _append_page_break(lines: list[str]) -> None:
    if lines and lines[-1].strip():
        lines.append("")
    lines.extend(_page_break_lines())
    lines.append("")


def apply_introduction_page_break(lines: list[str]) -> list[str]:
    out_lines: list[str] = []
    in_code_fence = False
    inserted = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            out_lines.append(line)
            continue
        if in_code_fence:
            out_lines.append(line)
            continue

        if not inserted and INTRO_SECTION_RE.match(line):
            if not _has_trailing_page_break(out_lines):
                _append_page_break(out_lines)
            inserted = True
        out_lines.append(line)

    return out_lines


def apply_major_section_spacing(lines: list[str]) -> list[str]:
    out_lines: list[str] = []
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

        if MAJOR_SECTION_RE.match(line) and out_lines:
            trailing_blanks = 0
            cursor = len(out_lines) - 1
            while cursor >= 0 and not out_lines[cursor].strip():
                trailing_blanks += 1
                cursor -= 1
            while trailing_blanks < 2:
                out_lines.append("")
                trailing_blanks += 1

        out_lines.append(line)

    return out_lines


def reference_placement(lines: list[str], references_new_page: bool = True) -> list[str]:
    out_lines: list[str] = []
    refs_injected = False

    for index, line in enumerate(lines):
        if not refs_injected and REFERENCE_SECTION_RE.match(line.strip()):
            refs_injected = True
            if references_new_page and not _has_trailing_page_break(out_lines):
                _append_page_break(out_lines)
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


def is_external_resource(src: str) -> bool:
    if src.startswith("//"):
        return True
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", src))


def validate_relative_image_resources(source_path: Path) -> None:
    for line in scan_markdown_lines(source_path):
        for match in IMAGE_REFERENCE_RE.finditer(line.searchable):
            src = (match.group("src") or "").strip()
            if not src or is_external_resource(src):
                continue

            candidate = Path(src).expanduser()
            if candidate.is_absolute():
                continue

            resolved = (source_path.parent / candidate).resolve()
            if not resolved.exists():
                raise ValueError(
                    f"Relative image resource not found in {source_path}:{line.line}: "
                    f"{src} -> {resolved}"
                )


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
    *,
    include_auto_caption: bool = True,
) -> str:
    if not include_auto_caption:
        return figure.raw
    caption = _caption_line(label)
    if caption_position == "bottom":
        return f"{figure.raw}\n\n{caption}"
    return f"{caption}\n\n{figure.raw}"


def _image_without_caption_text(figure: FigureBlock) -> str:
    attrs_block = f"{{{figure.attrs}}}" if figure.attrs else ""
    # Empty alt text suppresses auto-generated "Figure N:" caption text in Pandoc output.
    return f"![]({figure.src}){attrs_block}"


def _page_break_block() -> str:
    return (
        "```{=latex}\n"
        "\\clearpage\n"
        "```\n\n"
        "```{=openxml}\n"
        f"{DOCX_PAGEBREAK_OPENXML}\n"
        "```"
    )


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
        blocks.append(f"{_page_break_block()}\n\n## Figure Captions")
        for label, figure in ordered:
            blocks.append(_title_line(label, figure))
        for label, figure in main_figures:
            blocks.append(
                f"{_page_break_block()}\n\n{_caption_line(label)}\n\n{_image_without_caption_text(figure)}"
            )
        if supplementary_figures:
            blocks.append(f"{_page_break_block()}\n\n## Supplementary Information")
            for label, figure in supplementary_figures:
                blocks.append(
                    f"{_page_break_block()}\n\n{_caption_line(label)}\n\n{_image_without_caption_text(figure)}"
                )
        return "\n\n".join(blocks) + ("\n" if blocks else "")

    if placement == "inline":
        for label, figure in ordered:
            block = _build_figure_block_with_caption_position(
                label,
                figure,
                caption_position,
                include_auto_caption=bool((figure.title or "").strip()),
            )
            blocks.append(block.strip())
        return "\n\n".join(blocks) + ("\n" if blocks else "")

    for label, figure in main_figures:
        blocks.append(
            f"{_page_break_block()}\n\n"
            f"{_build_figure_block_with_caption_position(label, figure, caption_position)}"
        )
    if supplementary_figures:
        blocks.append(f"{_page_break_block()}\n\n## Supplementary Information")
        for label, figure in supplementary_figures:
            blocks.append(
                f"{_page_break_block()}\n\n"
                f"{_build_figure_block_with_caption_position(label, figure, caption_position)}"
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
    chunks: list[str] = []
    for raw in sources:
        path = Path(raw)
        validate_relative_image_resources(path)
        chunks.append(path.read_text(encoding="utf-8").rstrip())
    # Keep a readable separation between merged files.
    return "\n\n".join(chunks) + "\n"


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)
    profile = resolve_profile(config, args.profile.strip() if args.profile else None, config_path=config_path)

    raw = load_markdown_sources(profile.manuscript_sources)
    lines = raw.splitlines()
    lines = apply_author_metadata(lines, profile.author_metadata)
    lines_without_figures, figures = extract_figures(lines)
    intro_paginated = apply_introduction_page_break(lines_without_figures)
    refs_lines = reference_placement(intro_paginated, profile.references_new_page)
    spaced_lines = apply_major_section_spacing(refs_lines)
    prepared_lines = apply_figure_placement(
        lines=spaced_lines,
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
