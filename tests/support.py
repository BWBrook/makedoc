from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
import yaml

from makedoc.build import _resolve, document_images
from makedoc.profile import Profile, load_profile

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


@dataclass
class Resolved:
    """The structure stage's output for one profile: the parsed document and its warnings."""

    blocks: list
    meta: dict
    markdown: str
    warnings: list[str]
    images: list[Path]

    @property
    def lines(self) -> list[str]:
        return self.markdown.splitlines()


def resolve(profile: Profile) -> Resolved:
    """Run makedoc's structure stage (Pandoc plus structure.lua) and read back the result."""
    with tempfile.TemporaryDirectory(prefix="makedoc-test-") as temp:
        resolved, warnings = _resolve(profile, Path(temp))
        doc = json.loads(resolved.read_text(encoding="utf-8"))
        markdown = subprocess.run(
            ["pandoc", str(resolved), "-f", "json", "-t", "markdown", "--wrap=none"],
            check=True, capture_output=True, text=True,
        ).stdout
        images = document_images(resolved)
    return Resolved(doc["blocks"], doc["meta"], markdown, warnings, images)


def resolve_markdown(profile: Profile) -> str:
    return resolve(profile).markdown


def manuscript(tmp_path: Path, sources: str | dict[str, str], **settings) -> Profile:
    """A profile over Markdown sources written under `tmp_path` (a single text is `main.md`)."""
    if isinstance(sources, str):
        sources = {"main.md": sources}
    paths = []
    for name, text in sources.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        paths.append(str(path))
    config = write_config(tmp_path / "build.yaml", {"p": {
        "manuscript_sources": paths,
        "bibliography": str(FIXTURE_REFS),
        "output_dir": "out",
        "output_stem": "p",
        **settings,
    }})
    return load_profile(config, "p")


def nodes(tree: object, kind: str) -> list[dict]:
    """Every Pandoc JSON element of type `kind` under `tree`, in document order."""
    found: list[dict] = []
    if isinstance(tree, dict):
        if tree.get("t") == kind:
            found.append(tree)
        for value in tree.values():
            found.extend(nodes(value, kind))
    elif isinstance(tree, list):
        for value in tree:
            found.extend(nodes(value, kind))
    return found


def text(tree: object) -> str:
    """Plain text of Pandoc JSON inlines or blocks."""
    if isinstance(tree, list):
        return "".join(text(item) for item in tree)
    if not isinstance(tree, dict):
        return ""
    kind = tree.get("t")
    if kind == "Str":
        return tree["c"]
    if kind in ("Space", "SoftBreak", "LineBreak"):
        return " "
    if kind in ("Code", "Math"):
        return tree["c"][1]
    if kind == "Image":
        return text(tree["c"][1])
    return text(tree.get("c"))


def identifier(node: dict) -> str:
    """The id of a Header, Div, Span, Figure, Image or Link."""
    return node["c"][1][0] if node["t"] == "Header" else node["c"][0][0]


def is_page_break(block: dict) -> bool:
    return block["t"] == "RawBlock" and (
        "\\clearpage" in block["c"][1] or 'w:type="page"' in block["c"][1]
    )
