#!/usr/bin/env python3
"""Normalize DOCX style/layout defaults for manuscript output."""

from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
HEADING_STYLE_IDS = {f"Heading{index}" for index in range(1, 10)}
COLOR_TAG = f"{{{W_NS}}}color"
RPR_TAG = f"{{{W_NS}}}rPr"
STYLE_ID_ATTR = f"{{{W_NS}}}styleId"
STYLE_TYPE_ATTR = f"{{{W_NS}}}type"
PPR_TAG = f"{{{W_NS}}}pPr"
SPACING_TAG = f"{{{W_NS}}}spacing"
SECTPR_TAG = f"{{{W_NS}}}sectPr"
LNNUMTYPE_TAG = f"{{{W_NS}}}lnNumType"
LINE_ATTR = f"{{{W_NS}}}line"
LINE_RULE_ATTR = f"{{{W_NS}}}lineRule"
LINE_RULE_AUTO = "auto"
LINE_NUMBERING_RESTART_ATTR = f"{{{W_NS}}}restart"
LINE_NUMBERING_COUNTBY_ATTR = f"{{{W_NS}}}countBy"
LINE_NUMBERING_DISTANCE_ATTR = f"{{{W_NS}}}distance"
LINE_NUMBERING_START_ATTR = f"{{{W_NS}}}start"
LINE_SPACING_VALUES = {
    "single": "240",
    "1.1": "264",
    "1.25": "300",
    "1.5": "360",
    "2": "480",
}
LINE_NUMBERING_RESTART_VALUES = {
    "continuous": "continuous",
    "page": "newPage",
    "section": "newSection",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", required=True, help="Path to DOCX file to normalize.")
    parser.add_argument(
        "--heading-color",
        default="000000",
        help="Hex heading color override (default: 000000).",
    )
    parser.add_argument(
        "--line-spacing",
        choices=("single", "1.1", "1.25", "1.5", "2"),
        default="single",
        help="Paragraph line spacing mode for DOCX output.",
    )
    parser.add_argument(
        "--line-numbering",
        choices=("continuous", "page", "section", "none"),
        default="none",
        help="Line numbering mode for DOCX output.",
    )
    return parser.parse_args()


def normalize_heading_styles(styles_xml: bytes, heading_color: str) -> bytes:
    root = ET.fromstring(styles_xml)
    changed = False

    for style in root.findall("w:style", NS):
        style_id = style.attrib.get(STYLE_ID_ATTR, "")
        if style_id not in HEADING_STYLE_IDS:
            continue

        rpr = style.find("w:rPr", NS)
        if rpr is None:
            rpr = ET.SubElement(style, RPR_TAG)

        color = rpr.find("w:color", NS)
        if color is None:
            color = ET.SubElement(rpr, COLOR_TAG)

        if color.attrib.get(f"{{{W_NS}}}val") != heading_color:
            color.attrib[f"{{{W_NS}}}val"] = heading_color
            changed = True

        for unwanted_attr in ("themeColor", "themeShade", "themeTint"):
            full_attr = f"{{{W_NS}}}{unwanted_attr}"
            if full_attr in color.attrib:
                del color.attrib[full_attr]
                changed = True

    if not changed:
        return styles_xml
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    return child


def normalize_line_spacing(styles_xml: bytes, line_spacing_mode: str) -> bytes:
    root = ET.fromstring(styles_xml)
    line_value = LINE_SPACING_VALUES[line_spacing_mode]
    changed = False

    for style in root.findall("w:style", NS):
        style_type = style.attrib.get(STYLE_TYPE_ATTR, "")
        if style_type != "paragraph":
            continue

        ppr = _ensure_child(style, PPR_TAG)
        spacing = _ensure_child(ppr, SPACING_TAG)

        if spacing.attrib.get(LINE_ATTR) != line_value:
            spacing.attrib[LINE_ATTR] = line_value
            changed = True
        if spacing.attrib.get(LINE_RULE_ATTR) != LINE_RULE_AUTO:
            spacing.attrib[LINE_RULE_ATTR] = LINE_RULE_AUTO
            changed = True

    if not changed:
        return styles_xml
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def normalize_line_numbering(document_xml: bytes, line_numbering_mode: str) -> bytes:
    root = ET.fromstring(document_xml)
    changed = False

    for sect_pr in root.findall(f".//{SECTPR_TAG}"):
        line_numbering = sect_pr.find(LNNUMTYPE_TAG)
        if line_numbering_mode == "none":
            if line_numbering is not None:
                sect_pr.remove(line_numbering)
                changed = True
            continue

        if line_numbering is None:
            line_numbering = ET.SubElement(sect_pr, LNNUMTYPE_TAG)
            changed = True

        restart_value = LINE_NUMBERING_RESTART_VALUES[line_numbering_mode]
        expected_attrs = {
            LINE_NUMBERING_RESTART_ATTR: restart_value,
            LINE_NUMBERING_COUNTBY_ATTR: "1",
            LINE_NUMBERING_DISTANCE_ATTR: "360",
            LINE_NUMBERING_START_ATTR: "1",
        }
        for key, value in expected_attrs.items():
            if line_numbering.attrib.get(key) != value:
                line_numbering.attrib[key] = value
                changed = True

    if not changed:
        return document_xml
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rewrite_docx(
    path: Path,
    heading_color: str,
    line_spacing_mode: str,
    line_numbering_mode: str,
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")

    with zipfile.ZipFile(path, "r") as src_zip:
        members = src_zip.namelist()
        payloads = {member: src_zip.read(member) for member in members}

    styles_key = "word/styles.xml"
    if styles_key not in payloads:
        return

    payloads[styles_key] = normalize_heading_styles(payloads[styles_key], heading_color)
    payloads[styles_key] = normalize_line_spacing(payloads[styles_key], line_spacing_mode)

    document_key = "word/document.xml"
    if document_key in payloads:
        payloads[document_key] = normalize_line_numbering(payloads[document_key], line_numbering_mode)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_path = Path(temp_file.name)

    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
            for member in members:
                out_zip.writestr(member, payloads[member])
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main() -> int:
    args = parse_args()
    rewrite_docx(
        Path(args.docx),
        heading_color=args.heading_color.strip().upper(),
        line_spacing_mode=args.line_spacing.strip(),
        line_numbering_mode=args.line_numbering.strip(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
