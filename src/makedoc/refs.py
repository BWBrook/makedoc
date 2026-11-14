"""Audit manuscript citation keys against bibliography keys."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .markdown_scan import scan_markdown_lines


# Pandoc's key grammar: a letter, digit or underscore, then alphanumerics with single
# internal punctuation marks; or any key wrapped in braces, as in @{key}.
CITE_PATTERN = re.compile(
    r"(?<![\w/])@(?:\{(?P<braced>[^}\s]+)\}|(?P<bare>[A-Za-z0-9_]+(?:[:.#$%&\-+?<>~/][A-Za-z0-9_]+)*))"
)


@dataclass(frozen=True)
class CitationHit:
    key: str
    source: Path
    line: int


def load_bibliography_keys(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    refs = data.get("references") or []
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
    for line in scan_markdown_lines(source):
        for match in CITE_PATTERN.finditer(line.searchable):
            key = match.group("braced") or match.group("bare")
            hits.append(CitationHit(key=key, source=source, line=line.line))
    return hits


@dataclass(frozen=True)
class RefsAudit:
    bibliography_keys: set[str]
    hits: list[CitationHit]

    @property
    def cited(self) -> set[str]:
        return {hit.key for hit in self.hits}

    @property
    def unknown(self) -> list[CitationHit]:
        return [hit for hit in self.hits if hit.key not in self.bibliography_keys]

    @property
    def unused(self) -> list[str]:
        return sorted(self.bibliography_keys - self.cited)


def audit_references(bibliography: Path, sources: list[Path]) -> RefsAudit:
    keys = load_bibliography_keys(bibliography)
    hits: list[CitationHit] = []
    for source in sources:
        hits.extend(scan_citations(source))
    return RefsAudit(bibliography_keys=keys, hits=hits)
