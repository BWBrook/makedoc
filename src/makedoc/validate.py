"""Validate build profile configuration contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .profile import load_config, resolve_profile
from .schema import (
    ALLOWED_FIGURE_KEYS,
    ALLOWED_MARGIN_KEYS,
    ALLOWED_PROFILE_KEYS,
    ALLOWED_REVIEW_MARKUP_KEYS,
    ALLOWED_TOP_LEVEL_KEYS,
    FONT_KEYS,
    REMOVED_PROFILE_KEYS,
)


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

        for key, instruction in REMOVED_PROFILE_KEYS.items():
            if key in raw_profile:
                append_error(
                    errors,
                    f"Profile '{name}' uses '{key}', removed in makedoc 2: {instruction} "
                    "(see MIGRATING.md).",
                )
        fonts = raw_profile.get("fonts")
        if isinstance(fonts, dict):
            unknown_font_keys = sorted(set(fonts) - set(FONT_KEYS))
            if unknown_font_keys:
                append_error(
                    errors, f"Profile '{name}' fonts has unknown keys: {', '.join(unknown_font_keys)}"
                )

        unknown_profile_keys = sorted(
            set(raw_profile.keys()) - ALLOWED_PROFILE_KEYS - set(REMOVED_PROFILE_KEYS)
        )
        if unknown_profile_keys:
            append_error(
                errors,
                f"Profile '{name}' has unknown keys: {', '.join(unknown_profile_keys)}",
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

        margins = raw_profile.get("margins")
        if margins is not None:
            if not isinstance(margins, dict):
                append_error(errors, f"Profile '{name}' key 'margins' must be a mapping.")
            else:
                unknown_margin_keys = sorted(set(margins.keys()) - ALLOWED_MARGIN_KEYS)
                if unknown_margin_keys:
                    append_error(
                        errors,
                        (
                            f"Profile '{name}' margins has unknown keys: "
                            f"{', '.join(unknown_margin_keys)}"
                        ),
                    )

        review_markup = raw_profile.get("review_markup")
        if review_markup is not None:
            if isinstance(review_markup, bool):
                pass
            elif not isinstance(review_markup, dict):
                append_error(
                    errors,
                    f"Profile '{name}' key 'review_markup' must be a boolean or mapping.",
                )
            else:
                unknown_review_keys = sorted(
                    set(review_markup.keys()) - ALLOWED_REVIEW_MARKUP_KEYS
                )
                if unknown_review_keys:
                    append_error(
                        errors,
                        (
                            f"Profile '{name}' review_markup has unknown keys: "
                            f"{', '.join(unknown_review_keys)}"
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
        for label, raw_path in path_checks:
            if not raw_path:
                continue
            path = Path(raw_path)
            if not path.exists():
                append_error(
                    errors,
                    f"Profile '{profile.name}' path missing ({label}): {path}",
                )


def validate_config(config_path: Path, profile_names: list[str], *, check_paths: bool = True) -> list[str]:
    """Return a list of problems with the config; empty means valid."""
    errors: list[str] = []
    try:
        config = load_config(config_path)
    except (ValueError, yaml.YAMLError) as exc:
        return [str(exc)]
    if validate_schema(config, errors):
        validate_selected_profiles(
            config=config,
            config_path=config_path,
            profile_names=profile_names,
            check_paths=check_paths,
            errors=errors,
        )
    return errors
