"""Shared markdown scanning helpers for lint and citation audit flows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


FENCE_OPEN_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


@dataclass(frozen=True)
class MarkdownLine:
    line: int
    raw: str
    searchable: str


def _mask_comments(text: str, in_comment: bool) -> tuple[str, bool]:
    """Blank out HTML comment text in one line; return the result and the carried state."""
    out: list[str] = []
    cursor = 0
    while cursor < len(text):
        if in_comment:
            end = text.find("-->", cursor)
            if end == -1:
                out.append(" " * (len(text) - cursor))
                cursor = len(text)
            else:
                out.append(" " * (end + 3 - cursor))
                cursor = end + 3
                in_comment = False
        else:
            start = text.find("<!--", cursor)
            if start == -1:
                out.append(text[cursor:])
                cursor = len(text)
            else:
                out.append(text[cursor:start])
                cursor = start
                in_comment = True
    return "".join(out), in_comment


def scan_lines(lines: list[str]) -> list[tuple[bool, str]]:
    """Classify each line as (visible, searchable).

    A line is not visible when it is inside a fenced block or lies wholly inside an HTML
    comment. `searchable` is the line with inline code spans and comment text blanked out,
    so that patterns are only matched against prose.
    """
    scanned: list[tuple[bool, str]] = []
    active_fence_char = ""
    active_fence_len = 0
    in_comment = False

    for raw_line in lines:
        text = raw_line.rstrip("\n")
        stripped = text.strip()

        if active_fence_char:
            scanned.append((False, text))
            if stripped.startswith(active_fence_char * active_fence_len):
                if set(stripped) == {active_fence_char} and len(stripped) >= active_fence_len:
                    active_fence_char = ""
                    active_fence_len = 0
            continue

        if not in_comment:
            match = FENCE_OPEN_RE.match(text)
            if match:
                fence = match.group("fence")
                active_fence_char = fence[0]
                active_fence_len = len(fence)
                scanned.append((False, text))
                continue

        searchable, in_comment = _mask_comments(strip_inline_code_spans(text), in_comment)
        scanned.append((not stripped or bool(searchable.strip()), searchable))

    return scanned


def visible_line_flags(lines: list[str]) -> list[bool]:
    return [visible for visible, _ in scan_lines(lines)]


def strip_inline_code_spans(text: str) -> str:
    """Replace inline code spans with spaces so literal examples are not linted."""
    out: list[str] = []
    cursor = 0
    length = len(text)

    while cursor < length:
        if text[cursor] != "`":
            out.append(text[cursor])
            cursor += 1
            continue

        fence_len = 1
        while cursor + fence_len < length and text[cursor + fence_len] == "`":
            fence_len += 1

        closing = text.find("`" * fence_len, cursor + fence_len)
        if closing == -1:
            out.append(text[cursor])
            cursor += 1
            continue

        out.append(" " * (closing + fence_len - cursor))
        cursor = closing + fence_len

    return "".join(out)


def _iter_visible_lines(lines: list[str]) -> list[MarkdownLine]:
    return [
        MarkdownLine(line=number, raw=raw.rstrip("\n"), searchable=searchable)
        for number, (raw, (visible, searchable)) in enumerate(zip(lines, scan_lines(lines), strict=True), start=1)
        if visible
    ]


def scan_markdown_lines(source: Path) -> list[MarkdownLine]:
    with source.open("r", encoding="utf-8") as handle:
        return _iter_visible_lines(handle.readlines())
