from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTBED = REPO_ROOT / "testbed"
TESTBED_CONFIG = TESTBED / "settings" / "build.yaml"
FIXTURE_REFS = TESTBED / "references" / "fixture_refs.yaml"
FIXTURE_CSL = TESTBED / "csl" / "fixture_style.csl"
FIGURES_DIR = TESTBED / "manuscript" / "figures"
PATH_KEYS = ("author_metadata", "bibliography", "csl", "output_dir")
PATH_LIST_KEYS = ("manuscript_sources", "lint_sources", "csl_search_dirs")
W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

needs_pandoc = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
needs_pdf = pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("xelatex") is None,
    reason="pandoc and xelatex required",
)
needs_poppler = pytest.mark.skipif(
    shutil.which("pdftotext") is None or shutil.which("pdfinfo") is None,
    reason="poppler (pdftotext, pdfinfo) not installed",
)


def write_config(path: Path, profiles: dict, default: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    config = {"default_profile": default or next(iter(profiles)), "profiles": profiles}
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def copy_testbed_config(path: Path, output_root: Path) -> Path:
    """Copy the fixture config with every path made absolute and outputs under `output_root`."""
    raw = yaml.safe_load(TESTBED_CONFIG.read_text(encoding="utf-8"))
    base = TESTBED_CONFIG.parent
    profiles = {}
    for name, profile in raw["profiles"].items():
        profile = dict(profile)
        for key in PATH_KEYS:
            if key in profile:
                profile[key] = str((base / profile[key]).resolve())
        for key in PATH_LIST_KEYS:
            if key in profile:
                profile[key] = [str((base / item).resolve()) for item in profile[key]]
        profile["output_dir"] = str(output_root / name)
        profiles[name] = profile
    return write_config(path, profiles, raw.get("default_profile"))


def pdf_text(path: Path) -> str:
    return subprocess.run(
        ["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True
    ).stdout


def pdf_pages(path: Path) -> int:
    out = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", out, re.M).group(1))


def docx_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read("word/document.xml").decode("utf-8")


def docx_stats(path: Path) -> tuple[str, int, int]:
    root = ET.fromstring(docx_xml(path))
    text = " ".join(node.text for node in root.iterfind(".//w:t", W_NS) if node.text)
    return text, len(root.findall(".//w:tbl", W_NS)), len(root.findall(".//w:drawing", W_NS))


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text)
