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

Experimental review markup:
- when `review_markup.enabled` is true, CriticMarkup-like addition/deletion/
  substitution/note tokens are converted to plain Pandoc-visible Markdown.
- additions, deletions, substitution sides, and notes render as bold bracketed
  markers so PDF output remains readable without relying on strikeout.
- the transform is default-off, skips fenced blocks and inline code spans, and
  runs after figure extraction so figure markdown is preserved.
- HTML comment blocks are treated as hidden Markdown content and are not
  transformed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .markdown_scan import scan_markdown_lines, strip_inline_code_spans, visible_line_flags
from .profile import Profile
from .report import warn


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
REVIEW_SUBSTITUTION_RE = re.compile(r"\{~~(?P<old>.*?)~>(?P<new>.*?)~~\}")
REVIEW_ADDITION_RE = re.compile(r"\{\+\+(?P<text>.*?)\+\+\}")
REVIEW_DELETION_RE = re.compile(r"\{--(?P<text>.*?)--\}")
REVIEW_NOTE_RE = re.compile(r"\{>>(?P<text>.*?)<<\}")
HTML_COMMENT_OPEN_RE = re.compile(r"<!--")
HTML_COMMENT_CLOSE_RE = re.compile(r"-->")


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


def _as_nonempty_str(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Author metadata '{label}' must be a non-empty string.")
    return value.strip()


def load_author_metadata(path: Path) -> tuple[str, list[AuthorRecord], dict[str, str]]:
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
    title_note, authors, affiliations = load_author_metadata(Path(author_metadata_path))

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

    for index, (line, visible) in enumerate(zip(lines, visible_line_flags(lines), strict=True)):
        if not visible:
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

    for index, (line, visible) in enumerate(zip(lines, visible_line_flags(lines), strict=True)):
        if not visible:
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
    inserted = False

    for line, visible in zip(lines, visible_line_flags(lines), strict=True):
        if not visible:
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

    for line, visible in zip(lines, visible_line_flags(lines), strict=True):
        if not visible:
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


def _inline_code_segments(text: str) -> list[tuple[str, bool]]:
    segments: list[tuple[str, bool]] = []
    cursor = 0
    length = len(text)

    while cursor < length:
        if text[cursor] != "`":
            next_tick = text.find("`", cursor)
            if next_tick == -1:
                segments.append((text[cursor:], False))
                break
            segments.append((text[cursor:next_tick], False))
            cursor = next_tick
            continue

        fence_len = 1
        while cursor + fence_len < length and text[cursor + fence_len] == "`":
            fence_len += 1

        closing = text.find("`" * fence_len, cursor + fence_len)
        if closing == -1:
            segments.append((text[cursor], False))
            cursor += 1
            continue

        end = closing + fence_len
        segments.append((text[cursor:end], True))
        cursor = end

    return segments


def _review_markup_text(text: str) -> str:
    def substitution(match: re.Match[str]) -> str:
        old = match.group("old").strip()
        new = match.group("new").strip()
        return f"**[- {old} -]** **[+ {new} +]**"

    def addition(match: re.Match[str]) -> str:
        return f"**[+ {match.group('text').strip()} +]**"

    def deletion(match: re.Match[str]) -> str:
        return f"**[- {match.group('text').strip()} -]**"

    def note(match: re.Match[str]) -> str:
        return f"**[Reviewer note: {match.group('text').strip()}]**"

    text = REVIEW_SUBSTITUTION_RE.sub(substitution, text)
    text = REVIEW_ADDITION_RE.sub(addition, text)
    text = REVIEW_DELETION_RE.sub(deletion, text)
    text = REVIEW_NOTE_RE.sub(note, text)
    return text


def _hidden_comment_flags(lines: list[str]) -> list[bool]:
    flags: list[bool] = []
    in_comment = False

    for line in lines:
        if in_comment:
            flags.append(True)
            if HTML_COMMENT_CLOSE_RE.search(line):
                in_comment = False
            continue

        if HTML_COMMENT_OPEN_RE.search(line):
            flags.append(True)
            if not HTML_COMMENT_CLOSE_RE.search(line):
                in_comment = True
            continue

        flags.append(False)

    return flags


def apply_review_markup(lines: list[str], enabled: bool = False) -> list[str]:
    if not enabled:
        return lines

    out_lines: list[str] = []
    hidden_flags = _hidden_comment_flags(lines)
    for line, visible, hidden in zip(lines, visible_line_flags(lines), hidden_flags, strict=True):
        if not visible or hidden or FIGURE_LINE_RE.match(line):
            out_lines.append(line)
            continue

        segments = _inline_code_segments(line)
        out_lines.append(
            "".join(
                segment if protected else _review_markup_text(segment)
                for segment, protected in segments
            )
        )

    return out_lines


def reference_placement(lines: list[str], references_new_page: bool = True) -> list[str]:
    out_lines: list[str] = []
    refs_injected = False

    for index, (line, visible) in enumerate(zip(lines, visible_line_flags(lines), strict=True)):
        if visible and not refs_injected and REFERENCE_SECTION_RE.match(line.strip()):
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

    for line, visible in zip(lines, visible_line_flags(lines), strict=True):
        if not visible:
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
            warn(f"figure has no #id in its attributes, so it cannot be linked: {line.strip()}")

    return out_lines, figures


def is_external_resource(src: str) -> bool:
    if src.startswith("//"):
        return True
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", src))


def validate_relative_image_resources(source_path: Path) -> None:
    for line in scan_markdown_lines(source_path):
        for match in IMAGE_REFERENCE_RE.finditer(line.searchable):
            resolve_image_resource(source_path, match.group("src") or "", line.line)


def image_resources(sources: list[Path]) -> list[Path]:
    """Local image files referenced by the given Markdown sources, in order of first use."""
    found: list[Path] = []
    for source in sources:
        for line in scan_markdown_lines(source):
            for match in IMAGE_REFERENCE_RE.finditer(line.searchable):
                src = (match.group("src") or "").strip()
                if not src or is_external_resource(src):
                    continue
                path = Path(src).expanduser()
                if not path.is_absolute():
                    path = (source.parent / path).resolve()
                if path not in found:
                    found.append(path)
    return found


def resolve_image_resource(source_path: Path, raw_src: str, line_number: int) -> str:
    src = raw_src.strip()
    if not src or is_external_resource(src):
        return raw_src

    candidate = Path(src).expanduser()
    if candidate.is_absolute():
        return raw_src

    resolved = (source_path.parent / candidate).resolve()
    if not resolved.exists():
        raise ValueError(
            f"Relative image resource not found in {source_path}:{line_number}: "
            f"{src} -> {resolved}"
        )
    return resolved.as_posix()


def rewrite_relative_image_resources(source_path: Path, text: str) -> str:
    rewritten_lines: list[str] = []
    lines = text.splitlines()
    flags = visible_line_flags(lines)

    for line_number, (line, visible) in enumerate(zip(lines, flags, strict=True), start=1):
        if not visible:
            rewritten_lines.append(line)
            continue

        searchable = strip_inline_code_spans(line)
        replacements: list[tuple[int, int, str]] = []
        for match in IMAGE_REFERENCE_RE.finditer(searchable):
            start, end = match.span("src")
            resolved = resolve_image_resource(source_path, line[start:end], line_number)
            replacements.append((start, end, resolved))

        if not replacements:
            rewritten_lines.append(line)
            continue

        cursor = 0
        parts: list[str] = []
        for start, end, replacement in replacements:
            parts.append(line[cursor:start])
            parts.append(replacement)
            cursor = end
        parts.append(line[cursor:])
        rewritten_lines.append("".join(parts))

    return "\n".join(rewritten_lines)


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
        match = SUPPLEMENTARY_ID_RE.search(figure.figure_id)
        if match:
            suffix = match.group(0)[2:]
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


def _label_and_bare_image(label: str, figure: FigureBlock) -> str:
    """Figure page for captions_page mode: an anchored label, then the image with no caption.

    Pandoc drops the id of an inline image in LaTeX output, so the id moves to the label,
    where in-text links land. The trailing nonbreaking space keeps the image inline, which
    suppresses a second visible caption while keeping its alt text (implicit_figures).
    """
    attrs = FIGURE_ID_RE.sub("", figure.attrs, count=1).strip()
    image = f"![{figure.title}]({figure.src})" + (f"{{{attrs}}}" if attrs else "")
    anchor = f"[{_caption_line(label)}]{{#{figure.figure_id}}}" if figure.figure_id else _caption_line(label)
    return f"{anchor}\n\n{image}\\ "


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
                f"{_page_break_block()}\n\n{_label_and_bare_image(label, figure)}"
            )
        if supplementary_figures:
            if main_figures:
                blocks.append(f"{_page_break_block()}\n\n## Supplementary Information")
            for label, figure in supplementary_figures:
                blocks.append(
                    f"{_page_break_block()}\n\n{_label_and_bare_image(label, figure)}"
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
        if main_figures:
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
        for index, (line, visible) in enumerate(zip(lines, visible_line_flags(lines), strict=True)):
            if not visible:
                continue

            if is_figure_placeholder(line, placeholder):
                new_lines = lines[:index] + [figure_blocks] + lines[index + 1 :]
                return new_lines
        warn(f'no <div id="{placeholder}"></div> placeholder found; figures appended at the end')

    # Default behavior: place all figure blocks after all manuscript content.
    return lines + ["", figure_blocks]


def load_markdown_sources(sources: list[str]) -> str:
    chunks: list[str] = []
    for raw in sources:
        path = Path(raw)
        text = path.read_text(encoding="utf-8")
        chunks.append(rewrite_relative_image_resources(path, text).rstrip())
    # Keep a readable separation between merged files.
    return "\n\n".join(chunks) + "\n"


def prepare_markdown(profile: Profile) -> str:
    """Return the single Markdown document handed to Pandoc for this profile."""
    lines = load_markdown_sources(profile.manuscript_sources).splitlines()
    lines = apply_author_metadata(lines, profile.author_metadata)
    lines, figures = extract_figures(lines)
    lines = apply_review_markup(lines, profile.review_markup.enabled)
    lines = apply_introduction_page_break(lines)
    lines = reference_placement(lines, profile.references_new_page)
    lines = apply_major_section_spacing(lines)
    lines = apply_figure_placement(lines=lines, figures=figures, profile=profile)
    return "\n".join(lines) + "\n"
