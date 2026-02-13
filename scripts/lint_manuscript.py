#!/usr/bin/env python3
"""Lint markdown manuscript sources for unresolved citations and table issues."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"\[REF\]")
MANUAL_CITE_RE = re.compile(r"\(([A-Z][^)]*(?:19|20)\d{2}[a-z]?[^)]*)\)")
TABLE_DELIM_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


@dataclass(frozen=True)
class LintError:
    source: Path
    line: int
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        help="Markdown source file to lint (repeatable).",
    )
    return parser.parse_args()


def split_table_cells(line: str) -> list[str]:
    """Split a markdown table row into cells, respecting escaped pipes."""
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for ch in line.rstrip("\n"):
        if escaped:
            current.append(ch)
            escaped = False
            continue
        if ch == "\\":
            current.append(ch)
            escaped = True
            continue
        if ch == "|":
            cells.append("".join(current))
            current = []
            continue
        current.append(ch)
    cells.append("".join(current))

    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return cells


def check_table_block(source: Path, lines: list[str], start_idx: int) -> tuple[list[LintError], int]:
    errors: list[LintError] = []
    header_line = lines[start_idx]
    expected_cells = len(split_table_cells(header_line))
    if expected_cells == 0:
        return errors, start_idx + 1

    idx = start_idx + 2  # skip header + delimiter
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if stripped == "" or "|" not in line:
            break
        if TABLE_DELIM_RE.match(line):
            break

        cells = split_table_cells(line)
        if len(cells) != expected_cells:
            errors.append(
                LintError(
                    source=source,
                    line=idx + 1,
                    message=(
                        "Malformed markdown table row: expected "
                        f"{expected_cells} cells, found {len(cells)}."
                    ),
                )
            )
        if any(cell.strip() == "$" for cell in cells):
            errors.append(
                LintError(
                    source=source,
                    line=idx + 1,
                    message="Suspicious table cell containing lone '$' token.",
                )
            )
        idx += 1

    return errors, idx


def lint_source(source: Path) -> list[LintError]:
    errors: list[LintError] = []
    if not source.exists():
        errors.append(LintError(source=source, line=1, message="Source file not found."))
        return errors

    with source.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    for line_num, line in enumerate(lines, start=1):
        if PLACEHOLDER_RE.search(line):
            errors.append(
                LintError(source=source, line=line_num, message="Unresolved placeholder [REF] found.")
            )
        if MANUAL_CITE_RE.search(line):
            errors.append(
                LintError(
                    source=source,
                    line=line_num,
                    message="Possible manual author-year citation found; convert to Pandoc citekeys.",
                )
            )

    idx = 0
    while idx < len(lines) - 1:
        if "|" in lines[idx] and TABLE_DELIM_RE.match(lines[idx + 1]):
            table_errors, next_idx = check_table_block(source, lines, idx)
            errors.extend(table_errors)
            idx = next_idx
            continue
        idx += 1

    return errors


def emit_error(err: LintError) -> None:
    print(f"{err.source}:{err.line}: {err.message}")
    if os.getenv("GITHUB_ACTIONS") == "true" and os.getenv("DISABLE_GHA_ANNOTATIONS") != "1":
        msg = err.message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error file={err.source},line={err.line}::{msg}")


def main() -> int:
    args = parse_args()
    sources = [Path(item) for item in args.source]
    all_errors: list[LintError] = []
    for source in sources:
        all_errors.extend(lint_source(source))

    if all_errors:
        for err in all_errors:
            emit_error(err)
        return 1

    print("Manuscript lint passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
