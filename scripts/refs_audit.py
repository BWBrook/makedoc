#!/usr/bin/env python3
"""Audit manuscript citation keys against bibliography keys."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


CITE_PATTERN = re.compile(r"(?<![\w/])@([A-Za-z0-9][A-Za-z0-9._:+-]*)")


@dataclass(frozen=True)
class CitationHit:
    key: str
    source: Path
    line: int


def load_bibliography_keys(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    refs = data.get("references", [])
    keys: set[str] = set()
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        key = ref.get("citation-key") or ref.get("id")
        if isinstance(key, str) and key.strip():
            keys.add(key.strip())
    return keys


def scan_citations(source: Path) -> list[CitationHit]:
    hits: list[CitationHit] = []
    with source.open("r", encoding="utf-8") as handle:
        for line_num, line in enumerate(handle, start=1):
            for match in CITE_PATTERN.finditer(line):
                hits.append(CitationHit(key=match.group(1), source=source, line=line_num))
    return hits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bibliography", required=True, help="Path to bibliography YAML file.")
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        help="Markdown source file to scan (repeatable).",
    )
    return parser.parse_args()


def emit_error(message: str, source: Path | None = None, line: int | None = None) -> None:
    print(message)
    if os.getenv("GITHUB_ACTIONS") == "true":
        msg = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        if source is not None and line is not None:
            print(f"::error file={source},line={line}::{msg}")
        else:
            print(f"::error::{msg}")


def main() -> int:
    args = parse_args()
    bibliography = Path(args.bibliography)
    sources = [Path(s) for s in args.source]

    if not bibliography.exists():
        emit_error(f"Error: bibliography not found: {bibliography}")
        return 1

    missing_sources = [s for s in sources if not s.exists()]
    if missing_sources:
        emit_error("Error: missing source files:")
        for src in missing_sources:
            emit_error(f"  - {src}")
        return 1

    bibliography_keys = load_bibliography_keys(bibliography)
    if not bibliography_keys:
        emit_error(f"Error: no citation keys found in bibliography: {bibliography}")
        return 1

    citation_hits: list[CitationHit] = []
    for src in sources:
        citation_hits.extend(scan_citations(src))

    cited_keys = {hit.key for hit in citation_hits}
    unknown_keys = sorted(cited_keys - bibliography_keys)
    unused_keys = sorted(bibliography_keys - cited_keys)

    print(f"Bibliography keys: {len(bibliography_keys)}")
    print(f"Cited keys: {len(cited_keys)}")
    print(f"Unknown keys: {len(unknown_keys)}")
    print(f"Unused keys: {len(unused_keys)}")

    if unknown_keys:
        emit_error("\nUnknown citation keys (must fix):")
        for key in unknown_keys:
            emit_error(f"  - {key}")
            for hit in citation_hits:
                if hit.key == key:
                    emit_error(
                        f"Unknown citation key '{key}' referenced in manuscript.",
                        source=hit.source,
                        line=hit.line,
                    )
        return 1

    print("\nReference audit passed.")
    if unused_keys:
        print("Unused bibliography keys (non-fatal):")
        for key in unused_keys:
            print(f"  - {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
