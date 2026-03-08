#!/usr/bin/env python3
"""Validate build profile configuration contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from build_profile import load_config, resolve_profile
from profile_schema import (
    ALLOWED_EDGECASE_KEYS,
    ALLOWED_FIGURE_KEYS,
    ALLOWED_PROFILE_KEYS,
    ALLOWED_TOP_LEVEL_KEYS,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="settings/build.yaml",
        help="Path to build config YAML (default: settings/build.yaml).",
    )
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Profile name to validate with path checks (repeatable).",
    )
    parser.add_argument(
        "--no-check-paths",
        action="store_true",
        help="Skip filesystem existence checks for selected profile paths.",
    )
    return parser.parse_args()


def append_error(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_schema(config: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    unknown_top = sorted(set(config.keys()) - ALLOWED_TOP_LEVEL_KEYS)
    if unknown_top:
        append_error(errors, f"Unknown top-level config keys: {', '.join(unknown_top)}")

    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        append_error(errors, "Config must include non-empty 'profiles' mapping.")
        return {}

    default_profile = config.get("default_profile")
    if not isinstance(default_profile, str) or not default_profile.strip():
        append_error(errors, "Config must define non-empty 'default_profile'.")
    elif default_profile not in profiles:
        append_error(errors, f"default_profile '{default_profile}' was not found in profiles.")

    for name, raw_profile in profiles.items():
        if not isinstance(raw_profile, dict):
            append_error(errors, f"Profile '{name}' must be a mapping.")
            continue

        unknown_profile_keys = sorted(set(raw_profile.keys()) - ALLOWED_PROFILE_KEYS)
        if unknown_profile_keys:
            append_error(
                errors,
                f"Profile '{name}' has unknown keys: {', '.join(unknown_profile_keys)}",
            )

        edgecases = raw_profile.get("edgecases")
        if edgecases is not None:
            if not isinstance(edgecases, dict):
                append_error(errors, f"Profile '{name}' key 'edgecases' must be a mapping.")
            else:
                unknown_edge_keys = sorted(set(edgecases.keys()) - ALLOWED_EDGECASE_KEYS)
                if unknown_edge_keys:
                    append_error(
                        errors,
                        (
                            f"Profile '{name}' edgecases has unknown keys: "
                            f"{', '.join(unknown_edge_keys)}"
                        ),
                    )

        figures = raw_profile.get("figures")
        if figures is not None:
            if not isinstance(figures, dict):
                append_error(errors, f"Profile '{name}' key 'figures' must be a mapping.")
            else:
                unknown_figure_keys = sorted(set(figures.keys()) - ALLOWED_FIGURE_KEYS)
                if unknown_figure_keys:
                    append_error(
                        errors,
                        (
                            f"Profile '{name}' figures has unknown keys: "
                            f"{', '.join(unknown_figure_keys)}"
                        ),
                    )

    return profiles


def validate_selected_profiles(
    config: dict[str, Any],
    config_path: Path,
    profile_names: list[str],
    check_paths: bool,
    errors: list[str],
) -> None:
    selected = profile_names or [str(config.get("default_profile", "")).strip()]
    if not selected or not selected[0]:
        return

    seen: set[str] = set()
    for profile_name in selected:
        if profile_name in seen:
            continue
        seen.add(profile_name)
        try:
            profile = resolve_profile(config, profile_name, config_path=config_path)
        except ValueError as exc:
            append_error(errors, f"Profile '{profile_name}' failed resolution: {exc}")
            continue

        if not check_paths:
            continue

        path_checks: list[tuple[str, str]] = []
        for item in profile.manuscript_sources:
            path_checks.append(("manuscript_sources", item))
        for item in profile.lint_sources:
            path_checks.append(("lint_sources", item))
        path_checks.extend(
            [
                ("author_metadata", profile.author_metadata),
                ("bibliography", profile.bibliography),
                ("csl", profile.csl),
            ]
        )
        if profile.golden_contract:
            path_checks.append(("golden_contract", profile.golden_contract))
        if profile.edgecase_unknown_cite:
            path_checks.append(("edgecases.unknown_cite", profile.edgecase_unknown_cite))
        if profile.edgecase_manual_cite:
            path_checks.append(("edgecases.manual_cite", profile.edgecase_manual_cite))
        if profile.edgecase_malformed_table:
            path_checks.append(("edgecases.malformed_table", profile.edgecase_malformed_table))

        for label, raw_path in path_checks:
            if not raw_path:
                continue
            path = Path(raw_path)
            if not path.exists():
                append_error(
                    errors,
                    f"Profile '{profile.name}' path missing ({label}): {path}",
                )


def main() -> int:
    args = parse_args()
    errors: list[str] = []

    config_path = Path(args.config)
    try:
        config = load_config(config_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    profiles = validate_schema(config, errors)
    if profiles:
        validate_selected_profiles(
            config=config,
            config_path=config_path,
            profile_names=[item for item in args.profile if item.strip()],
            check_paths=not args.no_check_paths,
            errors=errors,
        )

    if errors:
        print("Build config validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    selected_display = ", ".join([item for item in args.profile if item.strip()]) or str(
        config.get("default_profile", "")
    )
    print(f"Build config validation passed for selected profile(s): {selected_display}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
