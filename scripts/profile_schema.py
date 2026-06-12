#!/usr/bin/env python3
"""Shared schema constants for makedoc profile configuration."""

from __future__ import annotations

from pathlib import Path


DEFAULT_CONFIG = Path("settings/build.yaml")

PAGE_NUMBERING_DEFAULT = "lower_right"
PAGE_NUMBERING_CHOICES = ("lower_right", "none")
LINE_SPACING_CHOICES = ("single", "1.1", "1.25", "1.5", "2")
LINE_NUMBERING_CHOICES = ("continuous", "page", "section", "none")
FIGURE_PLACEMENT_CHOICES = ("pages", "captions_page", "inline")
FIGURE_CAPTION_POSITION_CHOICES = ("top", "bottom")
MARGIN_UNIT_CHOICES = ("cm", "in")
MARGIN_PAPER_SIZE_CHOICES = ("a4", "letter")

DEFAULT_FIGURE_SETTINGS = {
    "placement": "pages",
    "caption_position": "top",
    "placeholder_id": "figures",
}
DEFAULT_MARGINS = {
    "unit": "cm",
    "paper_size": "a4",
    "top": 1.5,
    "right": 1.5,
    "bottom": 1.5,
    "left": 1.5,
}
DEFAULT_REVIEW_MARKUP = {
    "enabled": False,
}

ALLOWED_TOP_LEVEL_KEYS = {"default_profile", "profiles"}
ALLOWED_PROFILE_KEYS = {
    "description",
    "manuscript_sources",
    "lint_sources",
    "author_metadata",
    "bibliography",
    "csl",
    "journal",
    "csl_search_dirs",
    "output_dir",
    "output_stem",
    "golden_contract",
    "edgecases",
    "page_numbers",
    "line_spacing",
    "line_numbering",
    "references_new_page",
    "figures",
    "margins",
    "review_markup",
}
ALLOWED_FIGURE_KEYS = {"placement", "caption_position", "placeholder_id"}
ALLOWED_EDGECASE_KEYS = {"unknown_cite", "manual_cite", "malformed_table"}
ALLOWED_MARGIN_KEYS = {"unit", "paper_size", "top", "right", "bottom", "left"}
ALLOWED_REVIEW_MARKUP_KEYS = {"enabled"}
