"""Turn a profile's Markdown sources into the single document handed to Pandoc.

Text-level work is kept to what must happen before parsing: joining the source files,
marking where each one came from, and expanding review markup (its tokens collide with
Pandoc's own syntax, so they cannot be handled after parsing). Everything structural
(authors, figures, bibliography anchor, page breaks, image paths) is done on the parsed
document by filters/structure.lua, configured by `structure_metadata`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .markdown_scan import visible_line_flags
from .profile import Profile

REVIEW_SUBSTITUTION_RE = re.compile(r"\{~~(?P<old>.*?)~>(?P<new>.*?)~~\}")
REVIEW_ADDITION_RE = re.compile(r"\{\+\+(?P<text>.*?)\+\+\}")
REVIEW_DELETION_RE = re.compile(r"\{--(?P<text>.*?)--\}")
REVIEW_NOTE_RE = re.compile(r"\{>>(?P<text>.*?)<<\}")
SOURCE_MARKER_FORMAT = "makedoc-source"


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


def author_block_markdown(author_metadata_path: str) -> str:
    """The author line, affiliations and corresponding-author line as Markdown."""
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

    return "\n".join(lines) + "\n"


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


def apply_review_markup(lines: list[str], enabled: bool = False) -> list[str]:
    if not enabled:
        return lines

    out_lines: list[str] = []
    for line, visible in zip(lines, visible_line_flags(lines), strict=True):
        if not visible:
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


def source_marker(directory: Path) -> str:
    """A raw block telling structure.lua which directory the following text came from."""
    return f"```{{={SOURCE_MARKER_FORMAT}}}\n{directory}\n```"


def prepare_markdown(profile: Profile) -> str:
    chunks: list[str] = []
    for raw in profile.manuscript_sources:
        path = Path(raw)
        lines = path.read_text(encoding="utf-8").splitlines()
        lines = apply_review_markup(lines, profile.review_markup.enabled)
        chunks.append(source_marker(path.parent.resolve()) + "\n\n" + "\n".join(lines).rstrip())
    return "\n\n".join(chunks) + "\n"


def structure_metadata(profile: Profile) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "placement": profile.figures.placement,
        "caption_position": profile.figures.caption_position,
        "placeholder_id": profile.figures.placeholder_id,
        "references_new_page": profile.references_new_page,
    }
    if profile.author_metadata:
        settings["author_block"] = author_block_markdown(profile.author_metadata)
    return {"makedoc": settings}
