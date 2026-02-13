#!/usr/bin/env python3
"""Resolve manuscript build profile values from YAML configuration."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = Path("settings/build.yaml")


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    manuscript_sources: list[str]
    lint_sources: list[str]
    bibliography: str
    csl: str
    journal: str
    csl_search_dirs: list[str]
    output_dir: str
    output_stem: str
    pdf_out: str
    docx_out: str
    edgecase_unknown_cite: str
    edgecase_manual_cite: str
    edgecase_malformed_table: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "manuscript_sources": self.manuscript_sources,
            "lint_sources": self.lint_sources,
            "bibliography": self.bibliography,
            "csl": self.csl,
            "journal": self.journal,
            "csl_search_dirs": self.csl_search_dirs,
            "output_dir": self.output_dir,
            "output_stem": self.output_stem,
            "pdf_out": self.pdf_out,
            "docx_out": self.docx_out,
            "edgecases": {
                "unknown_cite": self.edgecase_unknown_cite,
                "manual_cite": self.edgecase_manual_cite,
                "malformed_table": self.edgecase_malformed_table,
            },
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to build profile YAML (default: settings/build.yaml).",
    )
    parser.add_argument(
        "--profile",
        help="Profile name. If omitted, the file's default_profile is used.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    make_vars = subparsers.add_parser(
        "make-vars", help="Emit Makefile variable assignments for the selected profile."
    )
    make_vars.add_argument(
        "--prefix",
        default="ACTIVE",
        help="Variable prefix for emitted Make assignments (default: ACTIVE).",
    )

    show = subparsers.add_parser("show", help="Show resolved profile values.")
    show.add_argument(
        "--format",
        choices=("yaml", "json"),
        default="yaml",
        help="Output format (default: yaml).",
    )

    subparsers.add_parser("list-profiles", help="List available profile names.")

    value = subparsers.add_parser("value", help="Return one value from resolved profile data.")
    value.add_argument("--key", required=True, help="Dotted key path, e.g. edgecases.manual_cite")
    value.add_argument(
        "--join",
        default="\n",
        help="Delimiter for list output (default: newline).",
    )

    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping.")
    return data


def expect_str(mapping: dict[str, Any], key: str, *, required: bool = True, default: str = "") -> str:
    value = mapping.get(key, default)
    if value is None:
        value = default
    if value == "" and not required:
        return ""
    if not isinstance(value, str) or not value.strip():
        if required:
            raise ValueError(f"Profile key '{key}' must be a non-empty string.")
        return ""
    return value.strip()


def expect_list_of_str(
    mapping: dict[str, Any], key: str, *, required: bool = True, default: list[str] | None = None
) -> list[str]:
    value = mapping.get(key, default if default is not None else [])
    if value is None:
        value = []
    if not isinstance(value, list):
        raise ValueError(f"Profile key '{key}' must be a list of strings.")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Profile key '{key}' contains an invalid empty/non-string item.")
        out.append(item.strip())
    if required and not out:
        raise ValueError(f"Profile key '{key}' must contain at least one path.")
    return out


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def resolve_profile(config: dict[str, Any], profile_name: str | None) -> Profile:
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("Config must define a non-empty 'profiles' mapping.")

    selected_name = profile_name or config.get("default_profile")
    if not isinstance(selected_name, str) or not selected_name.strip():
        selected_name = next(iter(profiles.keys()))
    selected_name = selected_name.strip()

    raw_profile = profiles.get(selected_name)
    if not isinstance(raw_profile, dict):
        available = ", ".join(sorted(profiles.keys()))
        raise ValueError(f"Unknown profile '{selected_name}'. Available profiles: {available}")

    manuscript_sources = expect_list_of_str(raw_profile, "manuscript_sources")
    lint_sources = expect_list_of_str(
        raw_profile,
        "lint_sources",
        required=False,
        default=manuscript_sources,
    )
    bibliography = expect_str(raw_profile, "bibliography")
    csl = expect_str(raw_profile, "csl")
    journal = expect_str(raw_profile, "journal", required=False)
    output_dir = expect_str(raw_profile, "output_dir")
    output_stem = expect_str(raw_profile, "output_stem")
    description = expect_str(raw_profile, "description", required=False)

    csl_search_dirs = expect_list_of_str(raw_profile, "csl_search_dirs", required=False, default=[])
    if not csl_search_dirs:
        derived_dirs: list[str] = []
        csl_parent = str(Path(csl).parent)
        if csl_parent not in ("", "."):
            derived_dirs.append(csl_parent)
        derived_dirs.extend(["csl", "testbed/csl"])
        csl_search_dirs = dedupe_keep_order(derived_dirs)

    edgecases = raw_profile.get("edgecases") or {}
    if not isinstance(edgecases, dict):
        raise ValueError("Profile key 'edgecases' must be a mapping when present.")

    edge_unknown = edgecases.get("unknown_cite", "")
    edge_manual = edgecases.get("manual_cite", "")
    edge_table = edgecases.get("malformed_table", "")
    for key, value in {
        "edgecases.unknown_cite": edge_unknown,
        "edgecases.manual_cite": edge_manual,
        "edgecases.malformed_table": edge_table,
    }.items():
        if value and not isinstance(value, str):
            raise ValueError(f"Profile key '{key}' must be a string path.")

    pdf_out = str(Path(output_dir) / f"{output_stem}.pdf")
    docx_out = str(Path(output_dir) / f"{output_stem}.docx")

    return Profile(
        name=selected_name,
        description=description,
        manuscript_sources=manuscript_sources,
        lint_sources=lint_sources,
        bibliography=bibliography,
        csl=csl,
        journal=journal,
        csl_search_dirs=csl_search_dirs,
        output_dir=output_dir,
        output_stem=output_stem,
        pdf_out=pdf_out,
        docx_out=docx_out,
        edgecase_unknown_cite=edge_unknown.strip(),
        edgecase_manual_cite=edge_manual.strip(),
        edgecase_malformed_table=edge_table.strip(),
    )


def escape_make_value(value: str) -> str:
    out = value
    out = out.replace("\\", "\\\\")
    out = out.replace("#", "\\#")
    out = out.replace(":", "\\:")
    out = out.replace("$", "$$")
    out = out.replace(" ", "\\ ")
    return out


def format_make_value(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(escape_make_value(str(item)) for item in value)
    return escape_make_value(str(value))


def emit_make_vars(profile: Profile, prefix: str) -> str:
    base = prefix.strip().upper() if prefix.strip() else "ACTIVE"
    values: dict[str, Any] = {
        f"{base}_PROFILE": profile.name,
        f"{base}_DESCRIPTION": profile.description,
        f"{base}_MANUSCRIPT_SOURCES": profile.manuscript_sources,
        f"{base}_LINT_SOURCES": profile.lint_sources,
        f"{base}_BIBLIOGRAPHY": profile.bibliography,
        f"{base}_CSL": profile.csl,
        f"{base}_JOURNAL": profile.journal,
        f"{base}_CSL_SEARCH_DIRS": profile.csl_search_dirs,
        f"{base}_OUTPUT_DIR": profile.output_dir,
        f"{base}_OUTPUT_STEM": profile.output_stem,
        f"{base}_PDF_OUT": profile.pdf_out,
        f"{base}_DOCX_OUT": profile.docx_out,
        f"{base}_EDGECASE_UNKNOWN_CITE": profile.edgecase_unknown_cite,
        f"{base}_EDGECASE_MANUAL_CITE": profile.edgecase_manual_cite,
        f"{base}_EDGECASE_MALFORMED_TABLE": profile.edgecase_malformed_table,
    }
    lines = [f"{name} := {format_make_value(value)}" for name, value in values.items()]
    return "\n".join(lines)


def lookup_key(data: Any, dotted_key: str) -> Any:
    current = data
    for part in dotted_key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        raise KeyError(f"Unknown key path: {dotted_key}")
    return current


def main() -> int:
    args = parse_args()
    try:
        config = load_config(Path(args.config))
        profile = resolve_profile(config, args.profile)
    except (ValueError, yaml.YAMLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.command == "make-vars":
        print(emit_make_vars(profile, args.prefix))
        return 0

    if args.command == "list-profiles":
        profiles = config.get("profiles", {})
        selected = profile.name
        for name in profiles:
            marker = "*" if name == selected else " "
            print(f"{marker} {name}")
        return 0

    profile_data = profile.to_dict()

    if args.command == "show":
        if args.format == "json":
            print(json.dumps(profile_data, indent=2, sort_keys=True))
        else:
            print(yaml.safe_dump(profile_data, sort_keys=False).strip())
        return 0

    if args.command == "value":
        try:
            value = lookup_key(profile_data, args.key)
        except KeyError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        if isinstance(value, list):
            print(args.join.join(str(item) for item in value))
            return 0
        if isinstance(value, dict):
            print(json.dumps(value, sort_keys=True))
            return 0
        print(value)
        return 0

    print(f"Error: unknown command '{args.command}'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
