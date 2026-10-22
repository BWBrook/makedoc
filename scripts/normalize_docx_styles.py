#!/usr/bin/env python3
"""Normalize DOCX style/layout defaults for manuscript output."""

from __future__ import annotations

import argparse
import io
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from prepare_markdown_sources import _load_author_metadata
from profile_schema import (
    DEFAULT_MARGINS, LINE_NUMBERING_CHOICES, LINE_SPACING_CHOICES,
    MARGIN_PAPER_SIZE_CHOICES, MARGIN_UNIT_CHOICES,
    PAGE_NUMBERING_CHOICES, PAGE_NUMBERING_DEFAULT,
)


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
NS = {"w": W_NS, "r": R_NS}
STANDARD_NAMESPACES = {
    "w": W_NS, "r": R_NS, "wp": WP_NS, "pic": PIC_NS,
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "v": "urn:schemas-microsoft-com:vml",
    "o": "urn:schemas-microsoft-com:office:office",
    "cp": CP_NS, "dc": DC_NS,
}
PAPER_TWIPS = {"a4": (11906, 16838), "letter": (12240, 15840)}
INTERNAL_CUSTOM_PROPERTIES = {
    "bibliography", "csl", "citation-abbreviations", "resource-path",
    "reference-doc", "template", "include-in-header", "include-before-body",
    "include-after-body", "css",
}
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
    parser.add_argument("--author-metadata", default="",
                        help="Selected profile's author YAML; only names enter core metadata.")
    parser.add_argument(
        "--heading-color",
        default="000000",
        help="Hex heading color override (default: 000000).",
    )
    parser.add_argument(
        "--line-spacing",
        choices=LINE_SPACING_CHOICES,
        default="single",
        help="Paragraph line spacing mode for DOCX output.",
    )
    parser.add_argument(
        "--line-numbering",
        choices=LINE_NUMBERING_CHOICES,
        default="none",
        help="Line numbering mode for DOCX output.",
    )
    parser.add_argument("--page-numbers", choices=PAGE_NUMBERING_CHOICES,
                        default=PAGE_NUMBERING_DEFAULT)
    parser.add_argument("--paper-size", choices=MARGIN_PAPER_SIZE_CHOICES,
                        default=DEFAULT_MARGINS["paper_size"])
    parser.add_argument("--margin-unit", choices=MARGIN_UNIT_CHOICES,
                        default=DEFAULT_MARGINS["unit"])
    for side in ("top", "right", "bottom", "left"):
        parser.add_argument(f"--margin-{side}", type=float, default=DEFAULT_MARGINS[side])
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
    return serialize_xml(root, styles_xml)


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
    return serialize_xml(root, styles_xml)


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
            line_numbering = _set_child(sect_pr, "lnNumType")
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
    return serialize_xml(root, document_xml)


def serialize_xml(root: ET.Element, original: bytes = b"") -> bytes:
    """Keep Word's prefixes and declarations used by mc:Ignorable values.

    ElementTree otherwise invents ns0 prefixes and drops declarations that are
    referenced only in attribute values, which breaks some DOCX consumers.
    """
    namespaces = dict(event for _, event in ET.iterparse(io.BytesIO(original),
                      events=("start-ns",))) if original else {}
    for prefix, uri in namespaces.items():
        if not re.fullmatch(r"ns\d+", prefix):
            ET.register_namespace(prefix, uri)
    for prefix, uri in STANDARD_NAMESPACES.items():
        ET.register_namespace(prefix, uri)
    serialized = ET.tostring(root, encoding="unicode")
    for prefix, uri in namespaces.items():
        if not prefix or re.fullmatch(r"ns\d+", prefix):
            continue
        if f'xmlns:{prefix}=' not in serialized:
            root.set(f"xmlns:{prefix}", uri)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


# WordprocessingML property elements are ordered sequences (ECMA-376).
PROPERTY_ORDER = {
    "sectPr": "headerReference footerReference footnotePr endnotePr type pgSz pgMar paperSrc pgBorders lnNumType pgNumType cols formProt vAlign noEndnote titlePg textDirection bidi rtlGutter docGrid printerSettings sectPrChange".split(),
    "pPr": "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange".split(),
    "tblPr": "tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing tblInd tblBorders shd tblLayout tblCellMar tblLook tblCaption tblDescription tblPrChange".split(),
    "trPr": "cnfStyle divId gridBefore gridAfter wBefore wAfter cantSplit trHeight tblHeader tblCellSpacing jc hidden ins del trPrChange".split(),
}


def _set_child(parent: ET.Element, local_name: str, **attrs: str) -> ET.Element:
    tag = f"{{{W_NS}}}{local_name}"
    child = parent.find(tag)
    if child is None:
        child = ET.Element(tag)
    else:
        parent.remove(child)
    order = PROPERTY_ORDER.get(parent.tag.rsplit("}", 1)[-1], [])
    successors = order[order.index(local_name) + 1:] if local_name in order else []
    index = next((index for index, item in enumerate(parent)
                  if item.tag.rsplit("}", 1)[-1] in successors), len(parent))
    parent.insert(index, child)
    child.attrib.update({f"{{{W_NS}}}{key}": str(value) for key, value in attrs.items()})
    return child


def _is_list_paragraph(paragraph: ET.Element) -> bool:
    numbering = paragraph.find("w:pPr/w:numPr", NS)
    if numbering is None:
        return False
    number_id = numbering.find("w:numId", NS)
    # numId=0 explicitly cancels numbering inherited from a paragraph style.
    return number_id is None or number_id.get(f"{{{W_NS}}}val") != "0"


def _is_standalone_bold(paragraph: ET.Element) -> bool:
    text_runs = [run for run in paragraph.findall(".//w:r", NS)
                 if "".join(node.text or "" for node in run.findall("w:t", NS)).strip()]
    return bool(text_runs) and all(
        (bold := run.find("w:rPr/w:b", NS)) is not None
        and bold.get(f"{{{W_NS}}}val", "1").lower() not in {"0", "false", "off"}
        for run in text_runs
    )


def _keep_body_lead_ins(root: ET.Element) -> None:
    """Attach headings and lead-ins without chaining list items or table cells."""
    body = root.find("w:body", NS)
    if body is None:
        return
    children = list(body)
    for index, paragraph in enumerate(children):
        if paragraph.tag != f"{{{W_NS}}}p":
            continue
        has_text = any((node.text or "").strip() for node in paragraph.findall(".//w:t", NS))
        has_math = any(node.tag.endswith("}oMath") for node in paragraph.iter())
        if not has_text and not has_math:
            continue  # Do not turn explicit page breaks or spacers into lead-ins.
        following = children[index + 1] if index + 1 < len(children) else None
        style = paragraph.find("w:pPr/w:pStyle", NS)
        is_heading = style is not None and style.get(f"{{{W_NS}}}val") in HEADING_STYLE_IDS
        is_list = _is_list_paragraph(paragraph)
        before_table = following is not None and following.tag == f"{{{W_NS}}}tbl"
        before_list = (following is not None and following.tag == f"{{{W_NS}}}p"
                       and not is_list and _is_list_paragraph(following))
        if is_heading or before_table or before_list or (not is_list and _is_standalone_bold(paragraph)):
            props = paragraph.find("w:pPr", NS)
            if props is None:
                props = ET.Element(PPR_TAG)
                paragraph.insert(0, props)
            _set_child(props, "keepNext", val="1")


def normalize_document_layout(document_xml: bytes, *, paper_size: str,
                              margins: dict[str, float], margin_unit: str) -> bytes:
    root = ET.fromstring(document_xml)
    width, height = PAPER_TWIPS[paper_size]
    factor = 1440 / 2.54 if margin_unit == "cm" else 1440
    for sect_pr in root.findall(f".//{SECTPR_TAG}"):
        page = _set_child(sect_pr, "pgSz", w=width, h=height)
        page.attrib.pop(f"{{{W_NS}}}orient", None)
        page_margins = _set_child(sect_pr, "pgMar", **{
            side: str(round(value * factor)) for side, value in margins.items()
        })
        for name, value in (("header", "720"), ("footer", "720"), ("gutter", "0")):
            page_margins.attrib.setdefault(f"{{{W_NS}}}{name}", value)
    for paragraph in root.findall(".//w:p", NS):
        # Empty source/page-break paragraphs and image-only paragraphs are
        # layout, not prose. Keep their lines out of manuscript line numbering.
        has_text = bool("".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip())
        has_math = any(node.tag.endswith("}oMath") for node in paragraph.iter())
        if not has_text and not has_math:
            ppr = paragraph.find("w:pPr", NS)
            if ppr is None:
                ppr = ET.Element(PPR_TAG)
                paragraph.insert(0, ppr)
            _set_child(ppr, "suppressLineNumbers")
    _keep_body_lead_ins(root)
    for row in root.findall(".//w:tr", NS):
        props = row.find("w:trPr", NS)
        if props is None:
            props = ET.Element(f"{{{W_NS}}}trPr")
            row.insert(0, props)
        _set_child(props, "cantSplit")
    for table in root.findall(".//w:tbl", NS):
        props = table.find("w:tblPr", NS)
        if props is None:
            props = ET.Element(f"{{{W_NS}}}tblPr")
            table.insert(0, props)
        # Let Word fit content within the text area rather than enforce narrow
        # fixed columns. Retain author/Pandoc grid widths as preferred widths.
        _set_child(props, "tblLayout", type="autofit")
    for local, namespace in (("docPr", WP_NS), ("cNvPr", PIC_NS)):
        for image in root.iter(f"{{{namespace}}}{local}"):
            for attr in ("descr", "title", "name"):
                value = image.get(attr, "")
                if re.match(r"^(?:/|[A-Za-z]:[\\/]|\.{1,2}/)", value):
                    if attr == "name":
                        image.set(attr, f"Image {image.get('id', '')}".strip())
                    else:
                        del image.attrib[attr]
                    print(f"Warning: removed source-path image {attr}; supply descriptive image alt text.", file=sys.stderr)
    return serialize_xml(root, document_xml)


def normalize_page_numbers(payloads: dict[str, bytes], mode: str) -> None:
    document = ET.fromstring(payloads["word/document.xml"])
    rel_key = "word/_rels/document.xml.rels"
    original_rels = payloads.get(rel_key, b"")
    rels = ET.fromstring(original_rels) if original_rels else ET.Element(f"{{{REL_NS}}}Relationships")
    footer_type = f"{R_NS}/footer"
    # These are generated submission files: the profile owns the page-number
    # footer references. Existing unrelated package parts remain untouched.
    for section in document.findall(f".//{SECTPR_TAG}"):
        for ref in list(section.findall("w:footerReference", NS)):
            section.remove(ref)
    if mode == "lower_right":
        footer_key = "word/makedoc-page-footer.xml"
        footer_target = "makedoc-page-footer.xml"
        existing = next((rel for rel in rels if rel.get("Target") == footer_target
                         and rel.get("Type") == footer_type), None)
        if existing is None:
            used_ids = {rel.get("Id") for rel in rels}
            number = 1
            while f"rIdMakedocFooter{number}" in used_ids:
                number += 1
            existing = ET.SubElement(rels, f"{{{REL_NS}}}Relationship", {
                "Id": f"rIdMakedocFooter{number}", "Type": footer_type, "Target": footer_target,
            })
        footer = ET.Element(f"{{{W_NS}}}ftr")
        p = ET.SubElement(footer, f"{{{W_NS}}}p")
        ppr = ET.SubElement(p, PPR_TAG)
        _set_child(ppr, "jc", val="right")
        _set_child(ppr, "suppressLineNumbers")
        field = ET.SubElement(p, f"{{{W_NS}}}fldSimple", {f"{{{W_NS}}}instr": " PAGE "})
        run = ET.SubElement(field, f"{{{W_NS}}}r")
        ET.SubElement(run, f"{{{W_NS}}}t").text = "1"
        payloads[footer_key] = serialize_xml(footer)
        for section in document.findall(f".//{SECTPR_TAG}"):
            # Use the same number on first/even pages if that section enables
            # those variants in an upstream reference document.
            for kind in ("default", "first", "even"):
                ref = ET.Element(f"{{{W_NS}}}footerReference", {
                    f"{{{W_NS}}}type": kind, f"{{{R_NS}}}id": existing.get("Id"),
                })
                section.insert(0, ref)
        types_xml = payloads["[Content_Types].xml"]
        types = ET.fromstring(types_xml)
        if not any(part.get("PartName") == "/" + footer_key for part in types):
            ET.SubElement(types, f"{{{CT_NS}}}Override", {
                "PartName": "/" + footer_key,
                "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
            })
        payloads["[Content_Types].xml"] = serialize_xml(types, types_xml)
    payloads[rel_key] = serialize_xml(rels, original_rels)
    payloads["word/document.xml"] = serialize_xml(document, payloads["word/document.xml"])


def strip_build_custom_properties(payloads: dict[str, bytes]) -> None:
    key = "docProps/custom.xml"
    if key not in payloads:
        return
    root = ET.fromstring(payloads[key])
    for prop in list(root):
        if prop.get("name", "").lower() in INTERNAL_CUSTOM_PROPERTIES:
            root.remove(prop)
    payloads[key] = serialize_xml(root, payloads[key])


def document_title(document_xml: bytes) -> str:
    """Read the leading title block without changing rendered document content."""
    body = ET.fromstring(document_xml).find("w:body", NS)
    if body is None:
        return ""
    paragraphs = []
    for child in body:
        if child.tag in {f"{{{W_NS}}}bookmarkStart", f"{{{W_NS}}}bookmarkEnd", f"{{{W_NS}}}proofErr"}:
            continue
        if child.tag != f"{{{W_NS}}}p":
            break
        text = "".join(node.text or "" for node in child.iter()
                       if node.tag in {f"{{{W_NS}}}t", f"{{{STANDARD_NAMESPACES['m']}}}t"}).strip()
        if not text:
            continue
        style = child.find("w:pPr/w:pStyle", NS)
        paragraphs.append((style.get(f"{{{W_NS}}}val", "") if style is not None else "", text))
        if len(paragraphs) == 2:
            break
    if not paragraphs or paragraphs[0][0] not in {"Title", "Heading1"}:
        return ""
    style, title = paragraphs[0]
    subtitle_style = "Subtitle" if style == "Title" else "Heading2"
    if len(paragraphs) > 1 and paragraphs[1][0] == subtitle_style:
        title += " — " + paragraphs[1][1]
    return title


def normalize_core_properties(payloads: dict[str, bytes], author_names: list[str]) -> None:
    """Fill absent/blank title and creator, retaining authored core properties."""
    key = "docProps/core.xml"
    original = payloads.get(key, b"")
    root = ET.fromstring(original) if original else ET.Element(f"{{{CP_NS}}}coreProperties")
    title = document_title(payloads["word/document.xml"]) if "word/document.xml" in payloads else ""
    changed = False
    for name, value in (("title", title), ("creator", "; ".join(author_names))):
        node = root.find(f"{{{DC_NS}}}{name}")
        if value and (node is None or not (node.text or "").strip()):
            if node is None:
                node = ET.SubElement(root, f"{{{DC_NS}}}{name}")
            node.text = value
            changed = True
    if not changed:
        return
    payloads[key] = serialize_xml(root, original)
    if original:
        return
    # A package without a core part also needs the standard OPC registration.
    types_key = "[Content_Types].xml"
    original_types = payloads.get(types_key, b"")
    types = ET.fromstring(original_types) if original_types else ET.Element(f"{{{CT_NS}}}Types")
    if not any(node.get("PartName") == "/" + key for node in types):
        ET.SubElement(types, f"{{{CT_NS}}}Override", PartName="/" + key,
                      ContentType="application/vnd.openxmlformats-package.core-properties+xml")
    payloads[types_key] = serialize_xml(types, original_types)
    rels_key = "_rels/.rels"
    original_rels = payloads.get(rels_key, b"")
    rels = ET.fromstring(original_rels) if original_rels else ET.Element(f"{{{REL_NS}}}Relationships")
    rel_type = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
    if not any(node.get("Type") == rel_type for node in rels):
        used_ids = {node.get("Id") for node in rels}
        rel_id = "rIdMakedocCore"
        while rel_id in used_ids:
            rel_id += "_"
        ET.SubElement(rels, f"{{{REL_NS}}}Relationship", Id=rel_id, Type=rel_type, Target=key)
    payloads[rels_key] = serialize_xml(rels, original_rels)


def rewrite_docx(
    path: Path,
    heading_color: str,
    line_spacing_mode: str,
    line_numbering_mode: str,
    *,
    page_numbers: str = PAGE_NUMBERING_DEFAULT,
    paper_size: str = "a4",
    margin_unit: str = "cm",
    margins: dict[str, float] | None = None,
    author_metadata: str = "",
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")
    if margins is None:
        margins = {side: DEFAULT_MARGINS[side] for side in ("top", "right", "bottom", "left")}
    if any(value <= 0 for value in margins.values()):
        raise ValueError("DOCX margins must be positive.")
    author_names = []
    if author_metadata.strip():
        _, authors, _ = _load_author_metadata(Path(author_metadata))
        author_names = [author.name for author in authors]
    with zipfile.ZipFile(path, "r") as src_zip:
        payloads = {member: src_zip.read(member) for member in src_zip.namelist()}
    styles_key = "word/styles.xml"
    if styles_key in payloads:
        payloads[styles_key] = normalize_heading_styles(payloads[styles_key], heading_color)
        payloads[styles_key] = normalize_line_spacing(payloads[styles_key], line_spacing_mode)
    document_key = "word/document.xml"
    if document_key in payloads:
        payloads[document_key] = normalize_line_numbering(payloads[document_key], line_numbering_mode)
        payloads[document_key] = normalize_document_layout(payloads[document_key],
            paper_size=paper_size, margins=margins, margin_unit=margin_unit)
        normalize_page_numbers(payloads, page_numbers)
    strip_build_custom_properties(payloads)
    normalize_core_properties(payloads, author_names)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", dir=path.parent) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
            for member, payload in payloads.items():
                out_zip.writestr(member, payload)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main() -> int:
    args = parse_args()
    rewrite_docx(Path(args.docx), heading_color=args.heading_color.strip().upper(),
                 line_spacing_mode=args.line_spacing, line_numbering_mode=args.line_numbering,
                 page_numbers=args.page_numbers, paper_size=args.paper_size,
                 margin_unit=args.margin_unit,
                 author_metadata=args.author_metadata,
                 margins={side: getattr(args, f"margin_{side}")
                          for side in ("top", "right", "bottom", "left")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
