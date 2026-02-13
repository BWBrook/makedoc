#!/usr/bin/env python3
"""Prepare concatenated markdown for build.

The source pipeline now normalizes references placement:
if an author-supplied ``References`` heading exists, we inject the
Pandoc-style anchor div (`<div id="refs"></div>`) at that location so the
bibliography is rendered there.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from build_profile import load_config, resolve_profile


REFERENCE_SECTION_RE = re.compile(r"^(?P<prefix>#{1,6})\s+references\b", re.IGNORECASE)


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


def normalize_sources(markdown: str) -> str:
    lines = markdown.splitlines()
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

    if not refs_injected:
        return "\n".join(lines) + "\n"

    return "\n".join(out_lines) + "\n"


def load_markdown_sources(sources: list[str]) -> str:
    chunks = [Path(raw).read_text(encoding="utf-8").rstrip() for raw in sources]
    # Keep a readable separation between merged files.
    return "\n\n".join(chunks) + "\n"


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))
    profile = resolve_profile(config, args.profile.strip() if args.profile else None)

    raw = load_markdown_sources(profile.manuscript_sources)
    prepared = normalize_sources(raw)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prepared, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
