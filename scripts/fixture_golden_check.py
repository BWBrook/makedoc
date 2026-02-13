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

import yaml


DEFAULT_REQUIRED_TEXT = [
    "Fixture Manuscript Title",
    "Fixture Table",
    "Fixture Figures",
    "Discussion",
]
DEFAULT_EXPECT_TABLES = 1
DEFAULT_EXPECT_DRAWINGS = 3
DEFAULT_MIN_PDF_PAGES = 1
DEFAULT_CONTRACT_PATH = Path("testbed/expected/golden_contract.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", required=True, help="Path to fixture DOCX output.")
    parser.add_argument("--pdf", required=True, help="Path to fixture PDF output.")
    parser.add_argument(
        "--contract",
        default=str(DEFAULT_CONTRACT_PATH),
        help=(
            "Path to fixture golden contract YAML. Defaults to "
            "testbed/expected/golden_contract.yaml."
        ),
    )
    parser.add_argument(
        "--expect-tables",
        type=int,
        default=None,
        help="Minimum number of table elements expected in DOCX (overrides contract).",
    )
    parser.add_argument(
        "--expect-drawings",
        type=int,
        default=None,
        help="Minimum number of drawing/image elements expected in DOCX (overrides contract).",
    )
    parser.add_argument(
        "--min-pdf-pages",
        type=int,
        default=None,
        help="Minimum page count expected in generated PDF (overrides contract).",
    )
    parser.add_argument(
        "--require-text",
        action="append",
        default=None,
        help="Text marker expected in both DOCX and PDF output (repeatable; overrides contract).",
    )
    return parser.parse_args()


def load_contract(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Contract file must contain mapping root: {path}")
    return data


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
    contract_path = Path(args.contract)

    errors: list[str] = []
    try:
        contract = load_contract(contract_path)
    except (ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: unable to read contract: {exc}")
        return 1

    contract_required_text = contract.get("required_text", DEFAULT_REQUIRED_TEXT)
    if not isinstance(contract_required_text, list) or not all(
        isinstance(item, str) for item in contract_required_text
    ):
        print("ERROR: contract key 'required_text' must be a list of strings.")
        return 1

    contract_expect_tables = contract.get("expect_tables", DEFAULT_EXPECT_TABLES)
    contract_expect_drawings = contract.get("expect_drawings", DEFAULT_EXPECT_DRAWINGS)
    contract_min_pdf_pages = contract.get("min_pdf_pages", DEFAULT_MIN_PDF_PAGES)
    for key, value in {
        "expect_tables": contract_expect_tables,
        "expect_drawings": contract_expect_drawings,
        "min_pdf_pages": contract_min_pdf_pages,
    }.items():
        if not isinstance(value, int):
            print(f"ERROR: contract key '{key}' must be an integer.")
            return 1

    expect_tables = args.expect_tables if args.expect_tables is not None else int(contract_expect_tables)
    expect_drawings = (
        args.expect_drawings if args.expect_drawings is not None else int(contract_expect_drawings)
    )
    min_pdf_pages = args.min_pdf_pages if args.min_pdf_pages is not None else int(contract_min_pdf_pages)
    required_text = args.require_text if args.require_text is not None else list(contract_required_text)

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

    if table_count < expect_tables:
        errors.append(f"DOCX table count {table_count} is below expected minimum {expect_tables}.")
    if drawing_count < expect_drawings:
        errors.append(
            f"DOCX drawing count {drawing_count} is below expected minimum {expect_drawings}."
        )

    try:
        pdf_pages = read_pdf_page_count(pdf_path)
    except (RuntimeError, ValueError) as exc:
        errors.append(str(exc))
        pdf_pages = 0
    else:
        if pdf_pages < min_pdf_pages:
            errors.append(
                f"PDF page count {pdf_pages} is below expected minimum {min_pdf_pages}."
            )

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
    print(f"Contract: {contract_path} ({'found' if contract_path.exists() else 'missing, defaults used'})")
    print(f"Required text markers: {len(required_text)}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    print("Fixture golden checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
