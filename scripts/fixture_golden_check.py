#!/usr/bin/env python3
"""Run lightweight structural regression checks on fixture PDF and DOCX outputs."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_REQUIRED_TEXT = [
    "Fixture Manuscript Title",
    "Fixture Table",
    "Fixture Figures",
    "Discussion",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", required=True, help="Path to fixture DOCX output.")
    parser.add_argument("--pdf", required=True, help="Path to fixture PDF output.")
    parser.add_argument(
        "--expect-tables",
        type=int,
        default=1,
        help="Minimum number of table elements expected in DOCX (default: 1).",
    )
    parser.add_argument(
        "--expect-drawings",
        type=int,
        default=3,
        help="Minimum number of drawing/image elements expected in DOCX (default: 3).",
    )
    parser.add_argument(
        "--require-text",
        action="append",
        default=[],
        help="Text marker expected in both DOCX and PDF output (repeatable).",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def read_docx_stats(path: Path) -> tuple[str, int, int]:
    with zipfile.ZipFile(path) as archive:
        payload = archive.read("word/document.xml")

    root = ET.fromstring(payload)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    texts = [node.text for node in root.findall(".//w:t", ns) if node.text]
    joined_text = " ".join(texts)
    table_count = len(root.findall(".//w:tbl", ns))
    drawing_count = len(root.findall(".//w:drawing", ns))
    return joined_text, table_count, drawing_count


def run_cmd(args: list[str]) -> str:
    proc = subprocess.run(args, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
        raise RuntimeError(f"Command failed ({' '.join(args)}): {err}")
    return proc.stdout


def read_pdf_text(path: Path) -> str:
    try:
        return run_cmd(["pdftotext", "-layout", str(path), "-"])
    except FileNotFoundError as exc:
        raise RuntimeError("pdftotext not found. Install poppler-utils.") from exc


def read_pdf_page_count(path: Path) -> int:
    try:
        output = run_cmd(["pdfinfo", str(path)])
    except FileNotFoundError as exc:
        raise RuntimeError("pdfinfo not found. Install poppler-utils.") from exc
    for line in output.splitlines():
        if line.startswith("Pages:"):
            _, value = line.split(":", 1)
            return int(value.strip())
    raise RuntimeError("Could not parse PDF page count from pdfinfo output.")


def main() -> int:
    args = parse_args()
    docx_path = Path(args.docx)
    pdf_path = Path(args.pdf)

    errors: list[str] = []
    required_text = args.require_text or DEFAULT_REQUIRED_TEXT

    if not docx_path.exists():
        errors.append(f"DOCX file missing: {docx_path}")
    if not pdf_path.exists():
        errors.append(f"PDF file missing: {pdf_path}")
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    try:
        docx_text, table_count, drawing_count = read_docx_stats(docx_path)
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError) as exc:
        print(f"ERROR: unable to inspect DOCX structure: {exc}")
        return 1

    if table_count < args.expect_tables:
        errors.append(f"DOCX table count {table_count} is below expected minimum {args.expect_tables}.")
    if drawing_count < args.expect_drawings:
        errors.append(
            f"DOCX drawing count {drawing_count} is below expected minimum {args.expect_drawings}."
        )

    try:
        pdf_pages = read_pdf_page_count(pdf_path)
    except (RuntimeError, ValueError) as exc:
        errors.append(str(exc))
        pdf_pages = 0
    else:
        if pdf_pages < 1:
            errors.append("PDF page count is zero.")

    try:
        pdf_text = read_pdf_text(pdf_path)
    except RuntimeError as exc:
        errors.append(str(exc))
        pdf_text = ""

    docx_norm = normalize_text(docx_text)
    pdf_norm = normalize_text(pdf_text)
    for marker in required_text:
        marker_norm = normalize_text(marker)
        if marker_norm and marker_norm not in docx_norm:
            errors.append(f"DOCX missing required marker text: '{marker}'")
        if marker_norm and marker_norm not in pdf_norm:
            errors.append(f"PDF missing required marker text: '{marker}'")

    print(f"DOCX tables: {table_count}")
    print(f"DOCX drawings: {drawing_count}")
    if pdf_pages:
        print(f"PDF pages: {pdf_pages}")
    print(f"Required text markers: {len(required_text)}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    print("Fixture golden checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
