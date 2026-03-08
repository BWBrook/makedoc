#!/usr/bin/env python3
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
    scanned: list[MarkdownLine] = []
    active_fence_char = ""
    active_fence_len = 0

    for line_num, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        match = FENCE_OPEN_RE.match(raw_line)

        if active_fence_char:
            if stripped.startswith(active_fence_char * active_fence_len):
                closing = stripped[: len(stripped.rstrip())]
                if closing and set(closing) == {active_fence_char} and len(closing) >= active_fence_len:
                    active_fence_char = ""
                    active_fence_len = 0
            continue

        if match:
            fence = match.group("fence")
            active_fence_char = fence[0]
            active_fence_len = len(fence)
            continue

        scanned.append(
            MarkdownLine(
                line=line_num,
                raw=raw_line.rstrip("\n"),
                searchable=strip_inline_code_spans(raw_line.rstrip("\n")),
            )
        )

    return scanned


def scan_markdown_lines(source: Path) -> list[MarkdownLine]:
    with source.open("r", encoding="utf-8") as handle:
        return _iter_visible_lines(handle.readlines())
