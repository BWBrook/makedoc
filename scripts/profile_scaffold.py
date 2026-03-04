#!/usr/bin/env python3
"""Generate or append build profile entries for settings/build.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = Path("settings/build.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Profile name to create.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to build config YAML (default: settings/build.yaml).",
    )
    parser.add_argument(
        "--manuscript-source",
        action="append",
        default=[],
        help="Markdown source path; repeat for multiple files.",
    )
    parser.add_argument(
        "--lint-source",
        action="append",
        default=[],
        help="Lint source path; repeat for multiple files (defaults to manuscript sources).",
    )
    parser.add_argument("--bibliography", help="Bibliography YAML path.")
    parser.add_argument("--author-metadata", help="Author metadata YAML path.")
    parser.add_argument("--csl", help="CSL style path.")
    parser.add_argument("--journal", default="Journal Name", help="Journal label.")
    parser.add_argument(
        "--csl-search-dir",
        action="append",
        default=[],
        help="Directory searched for CSL files; repeatable.",
    )
    parser.add_argument("--output-dir", default="dist", help="Output directory.")
    parser.add_argument("--output-stem", default="manuscript", help="Output stem.")
    parser.add_argument(
        "--page-numbers",
        default="lower_right",
        help="Page-numbering mode: lower_right (default) or none.",
    )
    parser.add_argument(
        "--line-spacing",
        default="single",
        help="Line-spacing mode: single, 1.1, 1.25, 1.5, or 2.",
    )
    parser.add_argument(
        "--line-numbering",
        default="continuous",
        help="Line-numbering mode: continuous, page, section, or none.",
    )
    parser.add_argument(
        "--figure-placement",
        default="pages",
        help="Figure placement mode: pages (default), captions_page, or inline.",
    )
    parser.add_argument(
        "--figure-caption-position",
        default="top",
        help="Figure caption position: top (default) or bottom.",
    )
    parser.add_argument(
        "--figure-placeholder-id",
        default="figures",
        help="ID used for placeholder div when figure placement is inline.",
    )
    parser.add_argument(
        "--paper-size",
        default="a4",
        help="Paper size for output (a4 or letter).",
    )
    parser.add_argument(
        "--margin-unit",
        default="cm",
        help="Margin unit (cm or in).",
    )
    parser.add_argument(
        "--margin-top",
        default=1.5,
        type=float,
        help="Top margin value.",
    )
    parser.add_argument(
        "--margin-right",
        default=1.5,
        type=float,
        help="Right margin value.",
    )
    parser.add_argument(
        "--margin-bottom",
        default=1.5,
        type=float,
        help="Bottom margin value.",
    )
    parser.add_argument(
        "--margin-left",
        default=1.5,
        type=float,
        help="Left margin value.",
    )
    parser.add_argument("--edgecase-unknown-cite", help="Optional unknown-cite edge case path.")
    parser.add_argument("--edgecase-manual-cite", help="Optional manual-cite edge case path.")
    parser.add_argument("--edgecase-malformed-table", help="Optional malformed-table edge case path.")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append profile into config file instead of printing only.",
    )
    parser.add_argument(
        "--set-default",
        action="store_true",
        help="Set default_profile to this profile (requires --append).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing profile with same name when --append is used.",
    )
    return parser.parse_args()


def _positive_float(raw_value: float) -> float:
    if raw_value <= 0:
        raise ValueError("Values must be strictly greater than zero.")
    return raw_value


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def build_profile(args: argparse.Namespace) -> dict[str, Any]:
    manuscript_sources = [item.strip() for item in args.manuscript_source if item.strip()]
    if not manuscript_sources:
        manuscript_sources = [
            "/path/to/other-repo/manuscript/text/main.md",
            "/path/to/other-repo/manuscript/text/figures.md",
        ]

    lint_sources = [item.strip() for item in args.lint_source if item.strip()] or list(manuscript_sources)
    bibliography = (args.bibliography or "/path/to/other-repo/references/references.yaml").strip()
    author_metadata = (args.author_metadata or "").strip()
    csl = (args.csl or "/path/to/other-repo/csl/journal-style.csl").strip()

    csl_search_dirs = [item.strip() for item in args.csl_search_dir if item.strip()]
    if not csl_search_dirs:
        csl_parent = str(Path(csl).parent)
        derived_dirs = [csl_parent, "csl"]
        csl_search_dirs = [item for item in dedupe_keep_order(derived_dirs) if item not in ("", ".")]

    profile: dict[str, Any] = {
        "description": f"Scaffolded profile for {args.name}",
        "manuscript_sources": manuscript_sources,
        "lint_sources": lint_sources,
        "bibliography": bibliography,
        "csl": csl,
        "journal": args.journal,
        "csl_search_dirs": csl_search_dirs,
        "output_dir": args.output_dir,
        "output_stem": args.output_stem,
        "page_numbers": args.page_numbers,
        "line_spacing": args.line_spacing,
        "line_numbering": args.line_numbering,
        "figures": {
            "placement": args.figure_placement,
            "caption_position": args.figure_caption_position,
            "placeholder_id": args.figure_placeholder_id,
        },
        "margins": {
            "unit": args.margin_unit,
            "paper_size": args.paper_size,
            "top": _positive_float(args.margin_top),
            "right": _positive_float(args.margin_right),
            "bottom": _positive_float(args.margin_bottom),
            "left": _positive_float(args.margin_left),
        },
    }
    if author_metadata:
        profile["author_metadata"] = author_metadata

    edgecases: dict[str, str] = {}
    if args.edgecase_unknown_cite:
        edgecases["unknown_cite"] = args.edgecase_unknown_cite.strip()
    if args.edgecase_manual_cite:
        edgecases["manual_cite"] = args.edgecase_manual_cite.strip()
    if args.edgecase_malformed_table:
        edgecases["malformed_table"] = args.edgecase_malformed_table.strip()
    if edgecases:
        profile["edgecases"] = edgecases

    return profile


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"default_profile": "", "profiles": {}}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML root in {path}; expected mapping.")
    profiles = data.get("profiles")
    if profiles is None:
        data["profiles"] = {}
    elif not isinstance(profiles, dict):
        raise ValueError(f"Invalid 'profiles' section in {path}; expected mapping.")
    return data


def append_profile(path: Path, name: str, profile: dict[str, Any], overwrite: bool, set_default: bool) -> None:
    config = load_config(path)
    profiles = config.setdefault("profiles", {})
    assert isinstance(profiles, dict)

    if name in profiles and not overwrite:
        raise ValueError(f"Profile '{name}' already exists in {path}. Use --overwrite to replace it.")
    profiles[name] = profile

    if set_default:
        config["default_profile"] = name
    elif not str(config.get("default_profile", "")).strip():
        config["default_profile"] = name

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)


def print_snippet(name: str, profile: dict[str, Any]) -> None:
    snippet = {"profiles": {name: profile}}
    print(yaml.safe_dump(snippet, sort_keys=False).strip())


def main() -> int:
    args = parse_args()

    if args.set_default and not args.append:
        print("Error: --set-default requires --append.", file=sys.stderr)
        return 1

    profile = build_profile(args)
    print_snippet(args.name, profile)

    if not args.append:
        print("\nSnippet printed only (no file changes).")
        print("Use --append to write this profile into the config file.")
        return 0

    config_path = Path(args.config)
    try:
        append_profile(
            path=config_path,
            name=args.name,
            profile=profile,
            overwrite=args.overwrite,
            set_default=args.set_default,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"\nProfile '{args.name}' written to {config_path}.")
    if args.set_default:
        print(f"default_profile set to '{args.name}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
