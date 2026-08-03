#!/usr/bin/env python3
"""Resolve manuscript build profile values from YAML configuration."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from profile_schema import (
    DEFAULT_CONFIG,
    DEFAULT_FIGURE_SETTINGS,
    DEFAULT_MARGINS,
    DEFAULT_REVIEW_MARKUP,
    FIGURE_CAPTION_POSITION_CHOICES,
    FIGURE_PLACEMENT_CHOICES,
    LINE_NUMBERING_CHOICES,
    LINE_SPACING_CHOICES,
    MARGIN_PAPER_SIZE_CHOICES,
    MARGIN_UNIT_CHOICES,
    PAGE_NUMBERING_CHOICES,
    PAGE_NUMBERING_DEFAULT,
)
import yaml


@dataclass(frozen=True)
class Margins:
    unit: str
    paper_size: str
    top: float
    right: float
    bottom: float
    left: float

    def to_dict(self) -> dict[str, float | str]:
        return {
            "unit": self.unit,
            "paper_size": self.paper_size,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "left": self.left,
        }


@dataclass(frozen=True)
class Figures:
    placement: str
    caption_position: str
    placeholder_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "placement": self.placement,
            "caption_position": self.caption_position,
            "placeholder_id": self.placeholder_id,
        }


@dataclass(frozen=True)
class ReviewMarkup:
    enabled: bool

    def to_dict(self) -> dict[str, bool]:
        return {
            "enabled": self.enabled,
        }


def _find_repo_root(path: Path) -> Path | None:
    for parent in [path, *path.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def _safe_output_subdir(raw_name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw_name.strip()).strip("-._")
    return safe or "manuscript"


def _derive_output_subdir(manuscript_sources: list[str], repo_name: str | None = None) -> str:
    source_paths = [Path(source).expanduser() for source in manuscript_sources]

    # Prefer explicit manuscript root markers.
    manuscript_candidates: list[str] = []
    for raw in source_paths:
        source = raw.resolve()
        for ancestor in [source] + list(source.parents):
            if ancestor.name.lower() == "manuscript":
                container = ancestor.parent
                if container.name:
                    manuscript_candidates.append(_safe_output_subdir(container.name))
                break

    if manuscript_candidates:
        # Prefer the most common match when inputs span multiple paths.
        ranked = sorted(
            {name: manuscript_candidates.count(name) for name in set(manuscript_candidates)}.items(),
            key=lambda item: (-item[1], item[0]),
        )
        if ranked:
            return ranked[0][0]

    if repo_name:
        return _safe_output_subdir(repo_name)

    # Last-resort collision-safe fallback.
    return _next_fallback_dir("manuscript")


def _next_fallback_dir(prefix: str) -> str:
    base_dir = Path("dist")
    existing = []
    for item in base_dir.glob(f"{prefix}-*"):
        if not item.is_dir():
            continue
        suffix = item.name.removeprefix(f"{prefix}-")
        if suffix.isdigit():
            existing.append(int(suffix))

    next_n = (max(existing) + 1) if existing else 1
    return f"{prefix}-{next_n}"


def _infer_output_dir(output_dir: str, manuscript_sources: list[str], *, config_dir: Path) -> str:
    candidate = Path(output_dir).expanduser()
    base_output = candidate.as_posix()
    if base_output == "dist":
        repo_name: str | None = None
        for source in manuscript_sources:
            resolved = Path(source).expanduser().resolve()
            repo_root = _find_repo_root(resolved)
            if repo_root:
                repo_name = repo_root.name
                break

        inferred = _derive_output_subdir(manuscript_sources, repo_name=repo_name)
        return str(Path("dist") / inferred)

    if candidate.parts and candidate.parts[0] == "dist":
        return output_dir

    if base_output != "dist":
        if candidate.is_absolute():
            return str(candidate.resolve())
        return str((config_dir / candidate).resolve())
    return output_dir


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    manuscript_sources: list[str]
    lint_sources: list[str]
    author_metadata: str
    bibliography: str
    csl: str
    journal: str
    csl_search_dirs: list[str]
    resource_paths: list[str]
    output_dir: str
    output_stem: str
    pdf_out: str
    docx_out: str
    golden_contract: str
    edgecase_unknown_cite: str
    edgecase_manual_cite: str
    edgecase_malformed_table: str
    page_numbers: str
    line_spacing: str
    line_numbering: str
    references_new_page: bool
    margins: Margins
    figures: Figures
    review_markup: ReviewMarkup

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "manuscript_sources": self.manuscript_sources,
            "lint_sources": self.lint_sources,
            "author_metadata": self.author_metadata,
            "bibliography": self.bibliography,
            "csl": self.csl,
            "journal": self.journal,
            "csl_search_dirs": self.csl_search_dirs,
            "resource_paths": self.resource_paths,
            "output_dir": self.output_dir,
            "output_stem": self.output_stem,
            "pdf_out": self.pdf_out,
            "docx_out": self.docx_out,
            "golden_contract": self.golden_contract,
            "edgecases": {
                "unknown_cite": self.edgecase_unknown_cite,
                "manual_cite": self.edgecase_manual_cite,
                "malformed_table": self.edgecase_malformed_table,
            },
            "page_numbers": self.page_numbers,
            "line_spacing": self.line_spacing,
            "line_numbering": self.line_numbering,
            "references_new_page": self.references_new_page,
            "margins": self.margins.to_dict(),
            "figures": self.figures.to_dict(),
            "review_markup": self.review_markup.to_dict(),
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


def expect_str_or_number(mapping: dict[str, Any], key: str, *, required: bool = True, default: str | float | int = "") -> str:
    value = mapping.get(key, default)
    if value is None:
        value = default
    if value == "" and not required:
        return ""
    if isinstance(value, bool):
        raise ValueError(f"Profile key '{key}' must be a non-empty string/number.")
    if isinstance(value, (int, float)):
        value_text = str(value)
    elif isinstance(value, str):
        value_text = value.strip()
    else:
        raise ValueError(f"Profile key '{key}' must be a non-empty string/number.")
    if not value_text:
        if required:
            raise ValueError(f"Profile key '{key}' must be a non-empty string/number.")
        return ""
    return value_text


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


def resolve_relative_path(raw_path: str, *, config_dir: Path) -> str:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return str(candidate.resolve())
    return str((config_dir / candidate).resolve())


def resolve_relative_path_list(raw_paths: list[str], *, config_dir: Path) -> list[str]:
    return [resolve_relative_path(item, config_dir=config_dir) for item in raw_paths]


def resolve_optional_relative_path(raw_path: str, *, config_dir: Path) -> str:
    if not raw_path.strip():
        return ""
    return resolve_relative_path(raw_path, config_dir=config_dir)


def normalize_page_numbers(raw_value: str) -> str:
    value = raw_value.strip().lower().replace("-", "_")
    if value in {"right", "lr", "lower_right"}:
        return "lower_right"
    if value in {"off", "0", "false", "no", "none"}:
        return "none"
    if value == "lowerright":
        return "lower_right"
    return value


def normalize_line_numbering(raw_value: str) -> str:
    value = raw_value.strip().lower().replace("-", "_")
    if value in {"page", "by_page"}:
        return "page"
    if value in {"section", "by_section"}:
        return "section"
    if value in {"continuous", "cont"}:
        return "continuous"
    return value


def normalize_margin_unit(raw_value: str) -> str:
    value = raw_value.strip().lower().replace("_", "").replace("-", "")
    if value in {"cm", "centimeter", "centimetre", "metric"}:
        return "cm"
    if value in {"inch", "in", "inches", "imperial"}:
        return "in"
    return value


def normalize_paper_size(raw_value: str) -> str:
    value = raw_value.strip().lower().replace("_", "").replace("-", "")
    if value in {"a4paper", "a4"}:
        return "a4"
    if value in {"letter", "letterpaper", "usletter"}:
        return "letter"
    return value


def normalize_figure_placement(raw_value: str) -> str:
    value = raw_value.strip().lower().replace("-", "_")
    if value in {"page", "pages", "end", "endpages", "end_page", "end_of_doc", "append"}:
        return "pages"
    if value in {
        "captions",
        "caption",
        "captionspage",
        "caption_page",
        "captions_page",
        "figure_captions",
        "figurecaptions",
        "figcaps",
    }:
        return "captions_page"
    if value in {"inline", "in", "embed", "inlinefigures", "inline_figures"}:
        return "inline"
    return value


def normalize_caption_position(raw_value: str) -> str:
    value = raw_value.strip().lower().replace("-", "_")
    if value in {"top", "caption_top", "above"}:
        return "top"
    if value in {"bottom", "caption_bottom", "below"}:
        return "bottom"
    return value


def expect_positive_number(mapping: dict[str, Any], key: str, default: float, *, required: bool = True) -> float:
    value = mapping.get(key, default)
    if value is None:
        if required:
            raise ValueError(f"Profile key '{key}' must be a positive number.")
        return float(default)

    if isinstance(value, bool):
        raise ValueError(f"Profile key '{key}' must be a positive number.")

    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            if required:
                raise ValueError(f"Profile key '{key}' must be a positive number.")
            return float(default)
        try:
            number = float(normalized)
        except ValueError as exc:
            raise ValueError(f"Profile key '{key}' must be a positive number.") from exc
    else:
        raise ValueError(f"Profile key '{key}' must be a positive number.")

    if number <= 0:
        raise ValueError(f"Profile key '{key}' must be greater than 0.")
    return number


def expect_bool(mapping: dict[str, Any], key: str, *, required: bool = True, default: bool = False) -> bool:
    value = mapping.get(key, default)
    if value is None:
        value = default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    if required:
        raise ValueError(f"Profile key '{key}' must be a boolean.")
    return bool(default)


def _select_profile(
    config: dict[str, Any], profile_name: str | None
) -> tuple[str, dict[str, Any]]:
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
    return selected_name, raw_profile


def _resolve_profile_values(raw_profile: dict[str, Any], *, config_dir: Path) -> dict[str, Any]:
    manuscript_sources = resolve_relative_path_list(
        expect_list_of_str(raw_profile, "manuscript_sources"),
        config_dir=config_dir,
    )
    lint_sources = resolve_relative_path_list(
        expect_list_of_str(
            raw_profile,
            "lint_sources",
            required=False,
            default=manuscript_sources,
        ),
        config_dir=config_dir,
    )
    bibliography = resolve_relative_path(expect_str(raw_profile, "bibliography"), config_dir=config_dir)
    csl = resolve_relative_path(expect_str(raw_profile, "csl"), config_dir=config_dir)
    author_metadata = resolve_optional_relative_path(
        expect_str(raw_profile, "author_metadata", required=False),
        config_dir=config_dir,
    )
    requested_output_dir = expect_str(raw_profile, "output_dir")
    output_dir = _infer_output_dir(requested_output_dir, manuscript_sources, config_dir=config_dir)
    output_stem = expect_str(raw_profile, "output_stem")

    resource_paths = dedupe_keep_order([str(Path(source).parent) for source in manuscript_sources])
    return {
        "manuscript_sources": manuscript_sources,
        "lint_sources": lint_sources,
        "author_metadata": author_metadata,
        "bibliography": bibliography,
        "csl": csl,
        "journal": expect_str(raw_profile, "journal", required=False),
        "description": expect_str(raw_profile, "description", required=False),
        "output_dir": output_dir,
        "output_stem": output_stem,
        "pdf_out": str(Path(output_dir) / f"{output_stem}.pdf"),
        "docx_out": str(Path(output_dir) / f"{output_stem}.docx"),
        "golden_contract": resolve_optional_relative_path(
            expect_str(raw_profile, "golden_contract", required=False),
            config_dir=config_dir,
        ),
        "resource_paths": resource_paths,
        "csl_search_dirs": _resolve_csl_search_dirs(raw_profile, csl, config_dir=config_dir),
    }


def _resolve_csl_search_dirs(
    raw_profile: dict[str, Any], csl: str, *, config_dir: Path
) -> list[str]:
    csl_search_dirs = expect_list_of_str(raw_profile, "csl_search_dirs", required=False, default=[])
    csl_search_dirs = resolve_relative_path_list(csl_search_dirs, config_dir=config_dir)
    if csl_search_dirs:
        return csl_search_dirs

    derived_dirs: list[str] = []
    csl_parent = str(Path(csl).parent)
    if csl_parent not in ("", "."):
        derived_dirs.append(csl_parent)
    config_csl_dir = (config_dir / "csl").resolve()
    if config_csl_dir.exists():
        derived_dirs.append(str(config_csl_dir))
    return dedupe_keep_order(derived_dirs)


def _resolve_edgecase_paths(
    raw_profile: dict[str, Any], *, config_dir: Path
) -> tuple[str, str, str]:
    edgecases = raw_profile.get("edgecases") or {}
    if not isinstance(edgecases, dict):
        raise ValueError("Profile key 'edgecases' must be a mapping when present.")

    values = {
        "edgecases.unknown_cite": edgecases.get("unknown_cite", ""),
        "edgecases.manual_cite": edgecases.get("manual_cite", ""),
        "edgecases.malformed_table": edgecases.get("malformed_table", ""),
    }
    for key, value in values.items():
        if value and not isinstance(value, str):
            raise ValueError(f"Profile key '{key}' must be a string path.")

    return tuple(
        resolve_optional_relative_path(str(value).strip(), config_dir=config_dir)
        for value in values.values()
    )


def _resolve_layout_settings(raw_profile: dict[str, Any]) -> tuple[str, str, str, bool]:
    page_numbers = normalize_page_numbers(
        expect_str(raw_profile, "page_numbers", required=False, default=PAGE_NUMBERING_DEFAULT)
    )
    if page_numbers not in PAGE_NUMBERING_CHOICES:
        raise ValueError(f"Profile key 'page_numbers' resolved to unsupported value: {page_numbers}")

    line_spacing = expect_str_or_number(
        raw_profile, "line_spacing", required=False, default="single"
    ).lower()
    if line_spacing not in LINE_SPACING_CHOICES:
        allowed = ", ".join(LINE_SPACING_CHOICES)
        raise ValueError(f"Profile key 'line_spacing' must be one of: {allowed}.")

    line_numbering = normalize_line_numbering(
        expect_str(raw_profile, "line_numbering", required=False, default="continuous")
    )
    if line_numbering not in LINE_NUMBERING_CHOICES:
        raise ValueError(
            f"Profile key 'line_numbering' resolved to unsupported value: {line_numbering}"
        )

    references_new_page = expect_bool(
        raw_profile, "references_new_page", required=False, default=True
    )
    return page_numbers, line_spacing, line_numbering, references_new_page


def _resolve_figures(raw_profile: dict[str, Any]) -> Figures:
    figures_raw = raw_profile.get("figures", {})
    if figures_raw is None:
        figures_raw = {}
    if not isinstance(figures_raw, dict):
        raise ValueError("Profile key 'figures' must be a mapping when present.")

    placement = normalize_figure_placement(
        expect_str(
            figures_raw, "placement", required=False, default=DEFAULT_FIGURE_SETTINGS["placement"]
        )
    )
    if placement not in FIGURE_PLACEMENT_CHOICES:
        allowed = ", ".join(FIGURE_PLACEMENT_CHOICES)
        raise ValueError(f"Profile key 'figures.placement' must be one of: {allowed}.")

    caption_position = normalize_caption_position(
        expect_str(
            figures_raw,
            "caption_position",
            required=False,
            default=DEFAULT_FIGURE_SETTINGS["caption_position"],
        )
    )
    if caption_position not in FIGURE_CAPTION_POSITION_CHOICES:
        allowed = ", ".join(FIGURE_CAPTION_POSITION_CHOICES)
        raise ValueError(f"Profile key 'figures.caption_position' must be one of: {allowed}.")

    placeholder_id = expect_str(
        figures_raw,
        "placeholder_id",
        required=False,
        default=DEFAULT_FIGURE_SETTINGS["placeholder_id"],
    )
    if not placeholder_id:
        raise ValueError("Profile key 'figures.placeholder_id' must be a non-empty string.")
    return Figures(placement=placement, caption_position=caption_position, placeholder_id=placeholder_id)


def _resolve_review_markup(raw_profile: dict[str, Any]) -> ReviewMarkup:
    review_markup_raw = raw_profile.get("review_markup", {})
    if review_markup_raw is None:
        review_markup_raw = {}
    if isinstance(review_markup_raw, bool):
        enabled = review_markup_raw
    elif isinstance(review_markup_raw, dict):
        enabled = expect_bool(
            review_markup_raw,
            "enabled",
            required=False,
            default=DEFAULT_REVIEW_MARKUP["enabled"],
        )
    else:
        raise ValueError("Profile key 'review_markup' must be a boolean or mapping when present.")
    return ReviewMarkup(enabled=enabled)


def _resolve_margins(raw_profile: dict[str, Any]) -> Margins:
    margins_raw = raw_profile.get("margins", {})
    if margins_raw is None:
        margins_raw = {}
    if not isinstance(margins_raw, dict):
        raise ValueError("Profile key 'margins' must be a mapping when present.")

    unit = normalize_margin_unit(
        expect_str(margins_raw, "unit", required=False, default=DEFAULT_MARGINS["unit"])
    )
    paper_size = normalize_paper_size(
        expect_str(margins_raw, "paper_size", required=False, default=DEFAULT_MARGINS["paper_size"])
    )
    values = {
        "top": expect_positive_number(
            margins_raw, "top", default=DEFAULT_MARGINS["top"], required=False
        ),
        "right": expect_positive_number(
            margins_raw, "right", default=DEFAULT_MARGINS["right"], required=False
        ),
        "bottom": expect_positive_number(
            margins_raw, "bottom", default=DEFAULT_MARGINS["bottom"], required=False
        ),
        "left": expect_positive_number(
            margins_raw, "left", default=DEFAULT_MARGINS["left"], required=False
        ),
    }
    if unit not in MARGIN_UNIT_CHOICES:
        allowed = ", ".join(MARGIN_UNIT_CHOICES)
        raise ValueError(f"Profile key 'margins.unit' must be one of: {allowed}.")
    if paper_size not in MARGIN_PAPER_SIZE_CHOICES:
        allowed = ", ".join(MARGIN_PAPER_SIZE_CHOICES)
        raise ValueError(f"Profile key 'margins.paper_size' must be one of: {allowed}.")
    return Margins(unit=unit, paper_size=paper_size, **values)


def resolve_profile(
    config: dict[str, Any],
    profile_name: str | None,
    *,
    config_path: Path | None = None,
) -> Profile:
    config_dir = (
        config_path.expanduser().resolve().parent
        if config_path is not None
        else Path.cwd().resolve()
    )
    selected_name, raw_profile = _select_profile(config, profile_name)

    values = _resolve_profile_values(raw_profile, config_dir=config_dir)
    manuscript_sources = values["manuscript_sources"]
    lint_sources = values["lint_sources"]
    author_metadata = values["author_metadata"]
    bibliography = values["bibliography"]
    csl = values["csl"]
    journal = values["journal"]
    description = values["description"]
    csl_search_dirs = values["csl_search_dirs"]
    resource_paths = values["resource_paths"]
    output_dir = values["output_dir"]
    output_stem = values["output_stem"]
    pdf_out = values["pdf_out"]
    docx_out = values["docx_out"]
    golden_contract = values["golden_contract"]

    (
        edge_unknown_path,
        edge_manual_path,
        edge_table_path,
    ) = _resolve_edgecase_paths(raw_profile, config_dir=config_dir)

    (
        page_numbers,
        line_spacing,
        line_numbering,
        references_new_page,
    ) = _resolve_layout_settings(raw_profile)

    figures = _resolve_figures(raw_profile)

    review_markup = _resolve_review_markup(raw_profile)

    margins = _resolve_margins(raw_profile)

    return Profile(
        name=selected_name,
        description=description,
        manuscript_sources=manuscript_sources,
        lint_sources=lint_sources,
        author_metadata=author_metadata,
        bibliography=bibliography,
        csl=csl,
        journal=journal,
        csl_search_dirs=csl_search_dirs,
        resource_paths=resource_paths,
        output_dir=output_dir,
        output_stem=output_stem,
        pdf_out=pdf_out,
        docx_out=docx_out,
        golden_contract=golden_contract,
        edgecase_unknown_cite=edge_unknown_path,
        edgecase_manual_cite=edge_manual_path,
        edgecase_malformed_table=edge_table_path,
        page_numbers=page_numbers,
        line_spacing=line_spacing,
        line_numbering=line_numbering,
        references_new_page=references_new_page,
        margins=margins,
        figures=figures,
        review_markup=review_markup,
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


def format_shell_value(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(shlex.quote(str(item)) for item in value)
    return shlex.quote(str(value))


def escape_make_assignment(value: str) -> str:
    out = value
    out = out.replace("#", "\\#")
    out = out.replace("$", "$$")
    return out


def _make_variable_values(profile: Profile, base: str) -> dict[str, Any]:
    return {
        f"{base}_PROFILE": profile.name,
        f"{base}_DESCRIPTION": profile.description,
        f"{base}_MANUSCRIPT_SOURCES": profile.manuscript_sources,
        f"{base}_LINT_SOURCES": profile.lint_sources,
        f"{base}_AUTHOR_METADATA": profile.author_metadata,
        f"{base}_BIBLIOGRAPHY": profile.bibliography,
        f"{base}_CSL": profile.csl,
        f"{base}_JOURNAL": profile.journal,
        f"{base}_CSL_SEARCH_DIRS": profile.csl_search_dirs,
        f"{base}_RESOURCE_PATHS": profile.resource_paths,
        f"{base}_RESOURCE_PATH": os.pathsep.join(profile.resource_paths),
        f"{base}_OUTPUT_DIR": profile.output_dir,
        f"{base}_OUTPUT_STEM": profile.output_stem,
        f"{base}_PDF_OUT": profile.pdf_out,
        f"{base}_DOCX_OUT": profile.docx_out,
        f"{base}_GOLDEN_CONTRACT": profile.golden_contract,
        f"{base}_EDGECASE_UNKNOWN_CITE": profile.edgecase_unknown_cite,
        f"{base}_EDGECASE_MANUAL_CITE": profile.edgecase_manual_cite,
        f"{base}_EDGECASE_MALFORMED_TABLE": profile.edgecase_malformed_table,
        f"{base}_PAGE_NUMBERS": profile.page_numbers,
        f"{base}_LINE_SPACING": profile.line_spacing,
        f"{base}_LINE_NUMBERING": profile.line_numbering,
        f"{base}_FIGURE_PLACEMENT": profile.figures.placement,
        f"{base}_FIGURE_CAPTION_POSITION": profile.figures.caption_position,
        f"{base}_FIGURE_PLACEHOLDER_ID": profile.figures.placeholder_id,
        f"{base}_REVIEW_MARKUP_ENABLED": profile.review_markup.enabled,
        f"{base}_MARGIN_UNIT": profile.margins.unit,
        f"{base}_MARGIN_PAPER_SIZE": profile.margins.paper_size,
        f"{base}_MARGIN_TOP": profile.margins.top,
        f"{base}_MARGIN_RIGHT": profile.margins.right,
        f"{base}_MARGIN_BOTTOM": profile.margins.bottom,
        f"{base}_MARGIN_LEFT": profile.margins.left,
    }


def _shell_variable_values(profile: Profile, base: str) -> dict[str, Any]:
    return {
        f"{base}_MANUSCRIPT_SOURCES_SH": profile.manuscript_sources,
        f"{base}_LINT_SOURCES_SH": profile.lint_sources,
        f"{base}_AUTHOR_METADATA_SH": profile.author_metadata,
        f"{base}_BIBLIOGRAPHY_SH": profile.bibliography,
        f"{base}_CSL_SH": profile.csl,
        f"{base}_CSL_SEARCH_DIRS_SH": profile.csl_search_dirs,
        f"{base}_RESOURCE_PATH_SH": os.pathsep.join(profile.resource_paths),
        f"{base}_OUTPUT_DIR_SH": profile.output_dir,
        f"{base}_PDF_OUT_SH": profile.pdf_out,
        f"{base}_DOCX_OUT_SH": profile.docx_out,
        f"{base}_GOLDEN_CONTRACT_SH": profile.golden_contract,
        f"{base}_EDGECASE_UNKNOWN_CITE_SH": profile.edgecase_unknown_cite,
        f"{base}_EDGECASE_MANUAL_CITE_SH": profile.edgecase_manual_cite,
        f"{base}_EDGECASE_MALFORMED_TABLE_SH": profile.edgecase_malformed_table,
    }


def emit_make_vars(profile: Profile, prefix: str) -> str:
    base = prefix.strip().upper() if prefix.strip() else "ACTIVE"
    values = _make_variable_values(profile, base)
    shell_values = _shell_variable_values(profile, base)
    lines = [f"{name} := {format_make_value(value)}" for name, value in values.items()]
    lines.extend(
        f"{name} := {escape_make_assignment(format_shell_value(value))}"
        for name, value in shell_values.items()
    )
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
        config_path = Path(args.config)
        config = load_config(config_path)
        profile = resolve_profile(config, args.profile, config_path=config_path)
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
