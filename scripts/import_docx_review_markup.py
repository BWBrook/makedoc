#!/usr/bin/env python3
"""Experimental DOCX-to-Markdown review-markup import spike.

This is not a production importer. It provides two narrow evidence routes:

1. Compare original plain text with revised DOCX text and emit simple
   Makedoc review-markup tokens from a normalized word diff.
2. Read tiny DOCX OOXML containing native Word ``w:ins``/``w:del`` elements and
   emit insertion/deletion review-markup tokens in document order.

The prototype intentionally ignores layout, styles, tables, figures, comments,
citations, field codes, moves, and Markdown structure. It uses only Python
stdlib ZIP/XML parsing so the feasibility evidence is dependency-light.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DOCUMENT_XML = "word/document.xml"


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _read_document_xml(docx_path: Path) -> ElementTree.Element:
    with zipfile.ZipFile(docx_path) as archive:
        try:
            payload = archive.read(DOCUMENT_XML)
        except KeyError as exc:
            raise ValueError(f"DOCX is missing {DOCUMENT_XML}: {docx_path}") from exc
    return ElementTree.fromstring(payload)


def _paragraphs(root: ElementTree.Element) -> list[ElementTree.Element]:
    return list(root.findall(f".//{{{WORD_NS}}}p"))


def _collect_text(
    element: ElementTree.Element,
    *,
    include_deleted: bool = False,
    in_deleted: bool = False,
) -> str:
    local = _local_name(element.tag)
    if local == "del":
        in_deleted = True

    parts: list[str] = []
    if local == "t" and not in_deleted and element.text:
        parts.append(element.text)
    elif local == "delText" and include_deleted and element.text:
        parts.append(element.text)

    for child in list(element):
        parts.append(
            _collect_text(
                child,
                include_deleted=include_deleted,
                in_deleted=in_deleted,
            )
        )
    return "".join(parts)


def extract_revised_text_from_docx(docx_path: str | Path) -> str:
    """Extract simple accepted/revised paragraph text from a DOCX.

    Native deletion text is ignored. Insertion text is included because it is
    the visible revised text in Word's tracked-change view.
    """

    root = _read_document_xml(Path(docx_path))
    paragraphs = [
        _normalize_text(_collect_text(paragraph, include_deleted=False))
        for paragraph in _paragraphs(root)
    ]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def diff_text_to_review_markup(original_text: str, revised_text: str) -> str:
    """Emit simple review-markup tokens from a normalized word diff."""

    original_words = _normalize_text(original_text).split()
    revised_words = _normalize_text(revised_text).split()
    matcher = SequenceMatcher(None, original_words, revised_words, autojunk=False)

    pieces: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old = " ".join(original_words[i1:i2])
        new = " ".join(revised_words[j1:j2])
        if tag == "equal":
            pieces.extend(revised_words[j1:j2])
        elif tag == "insert" and new:
            pieces.append(f"{{++ {new} ++}}")
        elif tag == "delete" and old:
            pieces.append(f"{{-- {old} --}}")
        elif tag == "replace":
            if old and new:
                pieces.append(f"{{~~ {old} ~> {new} ~~}}")
            elif old:
                pieces.append(f"{{-- {old} --}}")
            elif new:
                pieces.append(f"{{++ {new} ++}}")
    return " ".join(pieces).strip()


def revised_docx_to_review_markup(original_text: str, revised_docx: str | Path) -> str:
    revised_text = extract_revised_text_from_docx(revised_docx)
    return diff_text_to_review_markup(original_text, revised_text)


def _review_token(prefix: str, text: str, suffix: str) -> str:
    cleaned = _normalize_text(text)
    if not cleaned:
        return ""
    return f"{{{prefix} {cleaned} {suffix}}}"


def _element_to_track_change_markup(element: ElementTree.Element) -> str:
    local = _local_name(element.tag)
    if local == "ins":
        return _review_token("++", _collect_text(element, include_deleted=False), "++")
    if local == "del":
        return _review_token("--", _collect_text(element, include_deleted=True), "--")
    if local == "t" and element.text:
        return element.text
    if local == "delText":
        return ""

    return "".join(_element_to_track_change_markup(child) for child in list(element))


def track_changes_docx_to_review_markup(docx_path: str | Path) -> str:
    """Read simple ``w:ins``/``w:del`` text changes from DOCX OOXML."""

    root = _read_document_xml(Path(docx_path))
    paragraphs = [
        _normalize_text(_element_to_track_change_markup(paragraph))
        for paragraph in _paragraphs(root)
    ]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _load_original_text(args: argparse.Namespace) -> str:
    if args.original_text is not None:
        return args.original_text
    return Path(args.original_path).read_text(encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    revised = subparsers.add_parser(
        "revised",
        help="Diff original text against revised DOCX text.",
    )
    original_group = revised.add_mutually_exclusive_group(required=True)
    original_group.add_argument("--original-text", help="Original plain text.")
    original_group.add_argument(
        "--original-path",
        help="Path to original plain text or Markdown to compare as text.",
    )
    revised.add_argument("--revised-docx", required=True, help="Path to revised DOCX.")

    tracked = subparsers.add_parser(
        "track-changes",
        help="Read simple native Word w:ins/w:del elements from DOCX OOXML.",
    )
    tracked.add_argument("--docx", required=True, help="Path to DOCX.")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "revised":
        print(revised_docx_to_review_markup(_load_original_text(args), args.revised_docx))
        return 0
    if args.command == "track-changes":
        print(track_changes_docx_to_review_markup(args.docx))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
