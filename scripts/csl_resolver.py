#!/usr/bin/env python3
"""Search and source CSL files by journal name."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ZOTERO_STYLE_INDEX_URL = "https://www.zotero.org/styles-files/styles.json"
REQUEST_HEADERS = {"User-Agent": "makedoc-csl-resolver/1.0"}


@dataclass(frozen=True)
class Candidate:
    score: int
    name: str
    title: str
    href: str
    source: str
    path: Path | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search local and remote CSL matches.")
    add_search_args(search_parser)
    search_parser.set_defaults(func=cmd_search)

    source_parser = subparsers.add_parser(
        "source",
        help="Resolve a CSL path. Prefer local matches, otherwise download top remote match.",
    )
    add_search_args(source_parser)
    source_parser.add_argument(
        "--dest-dir",
        default="csl",
        help="Directory where downloaded CSL files are written (default: csl).",
    )
    source_parser.add_argument("--filename", help="Optional output filename for downloaded style.")
    source_parser.add_argument(
        "--local-only",
        action="store_true",
        help="Do not fetch remote styles; fail if no local match is found.",
    )
    source_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination file if it already exists.",
    )
    source_parser.add_argument(
        "--path-only",
        action="store_true",
        help="Print only the resolved CSL path.",
    )
    source_parser.set_defaults(func=cmd_source)

    return parser.parse_args()


def add_search_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--journal", required=True, help="Journal name to search for.")
    parser.add_argument(
        "--search-dir",
        action="append",
        default=[],
        help="Local directory to search recursively for *.csl files (repeatable).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=8,
        help="Maximum number of candidates to print (default: 8).",
    )
    parser.add_argument(
        "--cache-file",
        default=".cache/zotero_styles.json",
        help="Cache file for remote Zotero style index (default: .cache/zotero_styles.json).",
    )
    parser.add_argument(
        "--cache-ttl-hours",
        type=float,
        default=24.0,
        help="How long to reuse cached style index before refreshing (default: 24h).",
    )


def normalize(text: str) -> str:
    cleaned = text.lower().replace("&", "and")
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")
    return cleaned


def score_candidate(journal: str, *, name: str, title: str) -> int:
    query_norm = normalize(journal)
    if not query_norm:
        return 0

    name_norm = normalize(name)
    title_norm = normalize(title)
    query_tokens = {token for token in query_norm.split("-") if token}
    name_tokens = {token for token in name_norm.split("-") if token}
    title_tokens = {token for token in title_norm.split("-") if token}

    if query_norm == name_norm:
        return 120
    if query_norm == title_norm:
        return 115
    if query_norm in name_norm:
        return 100
    if query_norm in title_norm:
        return 95

    overlap = max(len(query_tokens & name_tokens), len(query_tokens & title_tokens))
    if overlap:
        return 70 + overlap * 8
    return 0


def try_read_csl_title(path: Path) -> str:
    try:
        root = ET.parse(path).getroot()
        for elem in root.iter():
            if elem.tag.endswith("title") and elem.text and elem.text.strip():
                return elem.text.strip()
    except (ET.ParseError, OSError):
        pass
    return path.stem


def find_local_candidates(journal: str, search_dirs: list[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    seen: set[Path] = set()

    for raw_dir in search_dirs:
        path = Path(raw_dir)
        if not path.exists():
            continue
        for csl_file in path.rglob("*.csl"):
            resolved = csl_file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            title = try_read_csl_title(csl_file)
            score = score_candidate(journal, name=csl_file.stem, title=title)
            if score <= 0:
                continue
            candidates.append(
                Candidate(
                    score=score,
                    name=csl_file.stem,
                    title=title,
                    href="",
                    source="local",
                    path=csl_file,
                )
            )

    candidates.sort(key=lambda item: (-item.score, item.name))
    return candidates


def fetch_remote_index(cache_file: Path, ttl_hours: float) -> list[dict[str, Any]]:
    if cache_file.exists():
        age_seconds = time.time() - cache_file.stat().st_mtime
        if age_seconds <= max(ttl_hours, 0.0) * 3600:
            with cache_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, list):
                return payload

    request = urllib.request.Request(ZOTERO_STYLE_INDEX_URL, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, list):
        raise ValueError("Unexpected Zotero style index payload format.")

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with cache_file.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return payload


def find_remote_candidates(
    journal: str, cache_file: Path, ttl_hours: float
) -> tuple[list[Candidate], str | None]:
    try:
        payload = fetch_remote_index(cache_file=cache_file, ttl_hours=ttl_hours)
    except (ValueError, OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return [], str(exc)

    candidates: list[Candidate] = []
    for style in payload:
        if not isinstance(style, dict):
            continue
        name = style.get("name")
        title = style.get("title")
        href = style.get("href")
        if not isinstance(name, str) or not isinstance(title, str) or not isinstance(href, str):
            continue
        score = score_candidate(journal, name=name, title=title)
        if score <= 0:
            continue
        candidates.append(
            Candidate(
                score=score,
                name=name,
                title=title,
                href=href,
                source="remote",
                path=None,
            )
        )

    candidates.sort(key=lambda item: (-item.score, item.name))
    return candidates, None


def print_candidate_list(header: str, candidates: list[Candidate], max_results: int) -> None:
    print(header)
    if not candidates:
        print("  (none)")
        return
    for idx, cand in enumerate(candidates[: max(max_results, 1)], start=1):
        if cand.source == "local" and cand.path is not None:
            print(f"  {idx}. {cand.title} [{cand.name}] -> {cand.path} (score={cand.score})")
            continue
        print(f"  {idx}. {cand.title} [{cand.name}] -> {cand.href} (score={cand.score})")


def choose_best(local: list[Candidate], remote: list[Candidate]) -> Candidate | None:
    if local:
        return local[0]
    if remote:
        return remote[0]
    return None


def download_csl(url: str) -> bytes:
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
    if b"<style" not in payload:
        raise ValueError("Downloaded content did not look like CSL XML.")
    return payload


def cmd_search(args: argparse.Namespace) -> int:
    local = find_local_candidates(args.journal, args.search_dir)
    remote, remote_err = find_remote_candidates(
        args.journal,
        cache_file=Path(args.cache_file),
        ttl_hours=args.cache_ttl_hours,
    )

    print(f"Journal query: {args.journal}")
    print_candidate_list("Local matches:", local, args.max_results)
    print_candidate_list("Remote matches:", remote, args.max_results)

    if remote_err:
        print(f"\nRemote index warning: {remote_err}")

    return 0 if (local or remote) else 1


def cmd_source(args: argparse.Namespace) -> int:
    local = find_local_candidates(args.journal, args.search_dir)
    remote: list[Candidate] = []
    remote_err: str | None = None

    if not args.local_only:
        remote, remote_err = find_remote_candidates(
            args.journal,
            cache_file=Path(args.cache_file),
            ttl_hours=args.cache_ttl_hours,
        )

    selected = choose_best(local, remote)
    if selected is None:
        print(f"No CSL match found for journal query: {args.journal}", file=sys.stderr)
        if remote_err:
            print(f"Remote index error: {remote_err}", file=sys.stderr)
        return 1

    if selected.source == "local":
        if selected.path is None:
            print("Internal error: local candidate missing path.", file=sys.stderr)
            return 1
        resolved_path = selected.path
        if args.path_only:
            print(resolved_path)
        else:
            print(f"Resolved local CSL: {resolved_path}")
            print(f"Title: {selected.title}")
        return 0

    if args.local_only:
        print("No local CSL match found and --local-only was requested.", file=sys.stderr)
        return 1

    dest_dir = Path(args.dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = args.filename or f"{selected.name}.csl"
    destination = dest_dir / filename

    if destination.exists() and not args.force:
        if args.path_only:
            print(destination)
        else:
            print(f"Destination exists, reusing: {destination}")
            print(f"Matched remote style: {selected.title} ({selected.href})")
        return 0

    try:
        payload = download_csl(selected.href)
    except (ValueError, urllib.error.URLError, TimeoutError) as exc:
        print(f"Failed to download CSL style '{selected.href}': {exc}", file=sys.stderr)
        return 1

    destination.write_bytes(payload)
    if args.path_only:
        print(destination)
    else:
        print(f"Downloaded CSL to: {destination}")
        print(f"Matched remote style: {selected.title} ({selected.href})")
    return 0


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
