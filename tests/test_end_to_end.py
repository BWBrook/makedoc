from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
import sys
import threading
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from makedoc.build import BuildError, build_profile, invisible_pngs
from makedoc.cli import main
from makedoc.prepare import prepare_markdown
from makedoc.profile import load_profile
from support import (
    FIGURES_DIR,
    FIXTURE_CSL,
    FIXTURE_REFS,
    TESTBED,
    W_NS,
    docx_stats,
    docx_xml,
    needs_pdf,
    needs_poppler,
    pdf_pages,
    pdf_text,
    squash,
    copy_testbed_config,
    write_config,
)

pytestmark = needs_pdf

CONTRACT_TEXT = ("Fixture Manuscript Title", "Fixture Table", "Discussion", "Fig. 1", "Fig. 2", "Fig. S1")
CONTRACT = {
    "fixture": {"stem": "fixture_manuscript", "tables": 1, "drawings": 3, "min_pages": 5, "line_spacing": "single"},
    "default": {"stem": "manuscript", "tables": 1, "drawings": 3, "min_pages": 6, "line_spacing": "1.5"},
}


@pytest.fixture(scope="module")
def testbed_builds(tmp_path_factory: pytest.TempPathFactory) -> dict:
    root = tmp_path_factory.mktemp("testbed")
    config = copy_testbed_config(root / "settings" / "build.yaml", root / "out")
    workdir = root / "work-default"
    strict_status = main(["build", "--strict", "-c", str(config), "-p", "default", "--workdir", str(workdir)])
    results = {name: build_profile(load_profile(config, name), config) for name in ("fixture", "review_markup")}
    return {"config": config, "out": root / "out", "workdir": workdir, "strict_status": strict_status, "results": results}


def test_strict_build_of_default_fixture_profile_succeeds(testbed_builds: dict) -> None:
    assert testbed_builds["strict_status"] == 0


@pytest.mark.parametrize("name", ["fixture", "default"])
def test_output_dir_holds_only_the_profile_outputs(testbed_builds: dict, name: str) -> None:
    stem = CONTRACT[name]["stem"]
    out = testbed_builds["out"] / name
    assert sorted(p.name for p in out.iterdir()) == sorted(
        [f"{stem}.pdf", f"{stem}.docx", f"{stem}_build_manifest.json"]
    )


@pytest.mark.parametrize("name", ["fixture", "default"])
def test_manifest_records_profile_and_provenance_inputs(testbed_builds: dict, name: str) -> None:
    out = testbed_builds["out"] / name
    manifest = json.loads((out / f"{CONTRACT[name]['stem']}_build_manifest.json").read_text(encoding="utf-8"))
    inputs = {Path(record["path"]).resolve() for record in manifest["inputs"]}
    assert testbed_builds["config"].resolve() in inputs
    assert (TESTBED / "manuscript" / "authors.yaml").resolve() in inputs
    assert all(record["exists"] for record in manifest["inputs"])
    assert manifest["profile"]["name"] == name
    assert manifest["profile"]["line_spacing"] == CONTRACT[name]["line_spacing"]
    assert {Path(record["path"]).name for record in manifest["outputs"]} == {
        f"{CONTRACT[name]['stem']}.pdf", f"{CONTRACT[name]['stem']}.docx"
    }


@pytest.mark.parametrize("name", ["fixture", "default"])
def test_docx_meets_fixture_contract(testbed_builds: dict, name: str) -> None:
    docx = testbed_builds["out"] / name / f"{CONTRACT[name]['stem']}.docx"
    text, tables, drawings = docx_stats(docx)
    assert tables == CONTRACT[name]["tables"]
    assert drawings == CONTRACT[name]["drawings"]
    for marker in CONTRACT_TEXT:
        assert marker in squash(text)
    xml = docx_xml(docx)
    bookmarks = set(re.findall(r'<w:bookmarkStart\b[^>]*\bw:name="([^"]+)"', xml))
    anchors = set(re.findall(r'<w:hyperlink\b[^>]*\bw:anchor="([^"]+)"', xml))
    assert anchors <= bookmarks


@needs_poppler
@pytest.mark.parametrize("name", ["fixture", "default"])
def test_pdf_meets_fixture_contract(testbed_builds: dict, name: str) -> None:
    pdf = testbed_builds["out"] / name / f"{CONTRACT[name]['stem']}.pdf"
    assert CONTRACT[name]["min_pages"] <= pdf_pages(pdf) <= 20
    text = squash(pdf_text(pdf))
    for marker in CONTRACT_TEXT:
        assert marker in text
    if name == "default":
        assert "Figure Captions" in text


def test_captions_page_pdf_has_no_undefined_references(testbed_builds: dict) -> None:
    workdir = testbed_builds["workdir"]
    assert (workdir / "prepared.md").is_file()
    assert (workdir / "layout.tex").is_file()
    logs = list(workdir.rglob("*.log"))
    assert logs
    for log in logs:
        assert "undefined" not in log.read_text(encoding="utf-8", errors="replace").lower()


@needs_poppler
def test_review_markup_renders_in_pdf_and_docx(testbed_builds: dict) -> None:
    result = testbed_builds["results"]["review_markup"]
    pdf = next(p for p in result.outputs if p.suffix == ".pdf")
    docx = next(p for p in result.outputs if p.suffix == ".docx")
    text = re.sub(r"(?<=[a-z])- (?=[a-z])", "", squash(pdf_text(pdf)))
    for marker in (
        "[+ inserted review text +]",
        "[- removed review text -]",
        "[- outdated wording -] [+ revised wording +]",
        "[Reviewer note:",
        "reviewer asks for a clearer transition]",
        "{++ literal addition ++}",
        "{-- fenced deletion should remain literal --}",
    ):
        assert marker in text
    xml = docx_xml(docx)
    for marker in (
        "[+ inserted review text +]",
        "[- removed review text -]",
        "[- outdated wording -]",
        "[+ revised wording +]",
        "[Reviewer note: reviewer asks for a clearer transition]",
        "{++ literal addition ++}",
        "{-- fenced deletion should remain literal --}",
    ):
        assert marker in xml
    assert "<w:strike" not in xml


def test_external_repo_with_relative_paths_builds_into_config_directory(tmp_path: Path) -> None:
    repo = tmp_path / "with spaces (probe)" / "external paper"
    figures = repo / "manuscript" / "figures"
    text = repo / "manuscript" / "text"
    for directory in (figures, text, repo / "references", repo / "csl"):
        directory.mkdir(parents=True)
    for name in ("fig1_dummy.png", "fig2_dummy.png"):
        shutil.copy(FIGURES_DIR / name, figures / name)
    shutil.copy(TESTBED / "manuscript" / "authors.yaml", repo / "manuscript" / "authors.yaml")
    shutil.copy(FIXTURE_REFS, repo / "references" / "refs.yaml")
    shutil.copy(FIXTURE_CSL, repo / "csl" / "fixture_style.csl")
    (text / "main.md").write_text(
        "# External Relative Path Regression\n\n<div id=\"authors\"></div>\n\n## Abstract\n\n"
        "This synthetic external manuscript exercises config-relative inputs [@alpha2020SyntheticWorkflow].\n\n"
        "## Results\n\nFigure content is referenced in Fig. [1](#fig-external-main).\n\n## References\n",
        encoding="utf-8",
    )
    (text / "figures.md").write_text(
        "![External regression figure one.](../figures/fig1_dummy.png){#fig-external-main width=95%}\n"
        "![External regression figure two.](../figures/fig2_dummy.png){#fig-external-two width=85%}\n",
        encoding="utf-8",
    )
    sources = ["../manuscript/text/main.md", "../manuscript/text/figures.md"]
    config = write_config(repo / "settings" / "build.yaml", {"ext": {
        "manuscript_sources": sources,
        "lint_sources": sources,
        "author_metadata": "../manuscript/authors.yaml",
        "bibliography": "../references/refs.yaml",
        "csl": "../csl/fixture_style.csl",
        "journal": "Oikos",
        "csl_search_dirs": ["../csl"],
        "output_dir": "dist",
        "output_stem": "manuscript",
        "line_numbering": "continuous",
        "figures": {"placement": "pages", "caption_position": "top", "placeholder_id": "figures"},
    }})

    assert main(["check", "-c", str(config)]) == 0
    assert main(["build", "-c", str(config)]) == 0

    out = repo / "settings" / "dist"
    assert sorted(p.name for p in out.iterdir()) == [
        "manuscript.docx", "manuscript.pdf", "manuscript_build_manifest.json"
    ]
    assert docx_stats(out / "manuscript.docx")[2] == 2


@pytest.fixture
def tiny_config(tmp_path: Path):
    def make(extra: dict | None = None, **bodies: str) -> Path:
        profiles = {}
        for name, body in bodies.items():
            source = tmp_path / f"{name}.md"
            source.write_text(body, encoding="utf-8")
            profiles[name] = {
                "manuscript_sources": [str(source)],
                "bibliography": str(FIXTURE_REFS),
                "output_dir": name,
                "output_stem": name,
                "line_numbering": "none",
                **(extra or {}).get(name, {}),
            }
        return write_config(tmp_path / "build.yaml", profiles)
    return make


@needs_poppler
def test_unicode_in_body_text_reaches_the_pdf(tiny_config) -> None:
    config = tiny_config(body="# Unicode\n\nThe bound α ≤ x₂ holds.\n")
    result = build_profile(load_profile(config, "body"), config, ("pdf",))
    text = pdf_text(result.outputs[0])
    assert re.search(r"[α𝛼] ≤ x\s?[2₂]", text), text
    assert not result.warnings


def test_unicode_in_code_span_without_glyph_fails_the_pdf_build(tiny_config) -> None:
    config = tiny_config(code="# Code\n\nSee `α ≤ x₂` here.\n")
    with pytest.raises(BuildError) as excinfo:
        build_profile(load_profile(config, "code"), config, ("pdf",))
    message = str(excinfo.value)
    for char, codepoint in (("α", "U+03B1"), ("≤", "U+2264"), ("₂", "U+2082")):
        assert char in message and codepoint in message


@needs_poppler
def test_two_profiles_build_concurrently_without_mixing_outputs(tiny_config) -> None:
    config = tiny_config(
        alpha="# Alpha Document\n\nAlpha body marker.\n",
        beta="# Beta Document\n\nBeta body marker.\n",
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {name: pool.submit(build_profile, load_profile(config, name), config) for name in ("alpha", "beta")}
        results = {name: future.result() for name, future in futures.items()}
    for name, other in (("alpha", "beta"), ("beta", "alpha")):
        pdf = config.parent / name / f"{name}.pdf"
        docx = config.parent / name / f"{name}.docx"
        assert {p.resolve() for p in results[name].outputs} == {pdf.resolve(), docx.resolve()}
        assert f"{name.title()} body marker" in pdf_text(pdf)
        assert f"{other.title()} body marker" not in pdf_text(pdf)
        assert f"{name.title()} body marker" in docx_stats(docx)[0]


def test_concurrent_build_warnings_stay_with_their_profile(tiny_config) -> None:
    config = tiny_config(
        extra={"noisy": {"figures": {"placement": "inline"}}},
        clean="# Clean\n\nNo figures here.\n",
        noisy=f"# Noisy\n\nText.\n\n![A figure.]({FIGURES_DIR / 'fig1_dummy.png'}){{#fig-a}}\n",
    )
    results: dict = {}
    threads = [
        threading.Thread(target=lambda: results.setdefault("clean", build_profile(load_profile(config, "clean"), config))),
        threading.Thread(target=lambda: results.setdefault("noisy", build_profile(load_profile(config, "noisy"), config))),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    noisy = results["noisy"]

    assert any("placeholder" in warning for warning in noisy.warnings)
    assert results["clean"].warnings == []


def test_cli_reports_and_enforces_makedoc_warnings(tiny_config) -> None:
    config = tiny_config(
        extra={"noisy": {"figures": {"placement": "inline"}}},
        noisy=f"# Noisy\n\nText.\n\n![A figure.]({FIGURES_DIR / 'fig1_dummy.png'}){{#fig-a}}\n",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "makedoc", "build", "--docx", "--strict", "-c", str(config)],
        capture_output=True, text=True, check=False,
    )
    assert "placeholder" in proc.stderr
    assert proc.returncode == 1


def test_sixteen_bit_alpha_png_fails_the_pdf_build(tiny_config, tmp_path: Path) -> None:
    png = tmp_path / "deep.png"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 6, 0, 0, 0)
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr)
    config = tiny_config(body=f"# T\n\n![A figure.]({png}){{#fig-a}}\n")
    assert invisible_pngs([png, FIGURES_DIR / "fig1_dummy.png"]) == [png]
    with pytest.raises(BuildError, match="16-bit"):
        build_profile(load_profile(config, "body"), config, ("pdf",))


@needs_poppler
def test_fixture_figures_are_visible_in_the_pdf(testbed_builds: dict, tmp_path: Path) -> None:
    pdf = testbed_builds["out"] / "fixture" / "fixture_manuscript.pdf"
    subprocess.run(["pdfimages", "-png", str(pdf), str(tmp_path / "img")], check=True)
    masks = subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True, check=True).stdout
    mask_indexes = [int(line.split()[1]) for line in masks.splitlines() if " smask " in line]
    assert mask_indexes
    for index in mask_indexes:
        assert max(_png_pixels(tmp_path / f"img-{index:03d}.png")) > 0, "soft mask is fully transparent"


def _png_pixels(path: Path) -> bytes:
    data = path.read_bytes()
    chunks, pos = b"", 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        if data[pos + 4:pos + 8] == b"IDAT":
            chunks += data[pos + 8:pos + 8 + length]
        pos += 12 + length
    return zlib.decompress(chunks)


def test_figure_in_html_comment_is_ignored(tiny_config) -> None:
    config = tiny_config(body="# T\n\n<!--\n![Draft.](missing.png){#fig-x}\n-->\n\nText.\n")
    assert "missing.png" not in prepare_markdown(load_profile(config, "body")).split("-->")[1]
    assert "Fig. 1" not in prepare_markdown(load_profile(config, "body"))


def test_empty_bibliography_passes_check_when_nothing_is_cited(tmp_path: Path) -> None:
    refs = tmp_path / "refs.yaml"
    refs.write_text("references: []\n", encoding="utf-8")
    source = tmp_path / "memo.md"
    source.write_text("# Memo\n\nNo citations.\n", encoding="utf-8")
    config = write_config(tmp_path / "build.yaml", {"memo": {
        "manuscript_sources": [str(source)], "bibliography": str(refs),
        "output_dir": "out", "output_stem": "memo",
    }})
    assert main(["check", "-c", str(config)]) == 0


FIGURE_BODY = (
    "# Figures\n\nOpening paragraph.\n\n"
    f"![Main caption.]({FIGURES_DIR / 'fig1_dummy.png'}){{#fig-main}}\n\n"
    "Closing paragraph.\n\n"
    f"![Supplementary caption.]({FIGURES_DIR / 'figS1_dummy.png'}){{#fig-extra-s1}}\n"
)


@needs_poppler
@pytest.mark.parametrize("placement", ["pages", "in_place"])
def test_pdf_figures_carry_only_makedoc_labels(tiny_config, placement: str) -> None:
    config = tiny_config(extra={"figs": {"figures": {"placement": placement}}}, figs=FIGURE_BODY)
    result = build_profile(load_profile(config, "figs"), config, ("pdf",))
    text = squash(pdf_text(result.outputs[0]))

    assert "Fig. 1. Main caption." in text
    assert "Fig. S1. Supplementary caption." in text
    assert not re.search(r"Figure \d+:", text)
    if placement == "in_place":
        assert text.index("Opening paragraph.") < text.index("Fig. 1.") < text.index("Closing paragraph.") < text.index("Fig. S1.")
    assert not result.warnings


@needs_poppler
@pytest.mark.parametrize("position", ["top", "bottom"])
def test_figure_caption_lines_are_numbered_and_the_image_is_not(tiny_config, position: str) -> None:
    figures = {"placement": "in_place", "caption_position": position}
    config = tiny_config(extra={"figs": {"line_numbering": "continuous", "figures": figures}}, figs=FIGURE_BODY)
    result = build_profile(load_profile(config, "figs"), config, ("pdf",))
    layout = subprocess.run(["pdftotext", "-layout", str(result.outputs[0]), "-"],
                            capture_output=True, text=True, check=True).stdout.replace("\f", "")
    numbered = dict(re.findall(r"^ *(\d+) +(\S.*?) *$", layout, flags=re.M))
    lines = {text: int(number) for number, text in numbered.items()}

    # One number per text line, none for either image: the count runs without a gap.
    assert sorted(lines.values()) == list(range(1, len(lines) + 1))
    assert {"Fig. 1. Main caption.", "Fig. S1. Supplementary caption."} <= set(lines)
    assert lines["Fig. 1. Main caption."] + 1 == lines["Closing paragraph."]
    assert not result.warnings


@needs_poppler
def test_manuscript_header_includes_reach_the_pdf_preamble(tiny_config) -> None:
    config = tiny_config(wide=(
        "---\nheader-includes:\n  - \\usepackage{pdflscape}\n---\n\n# Wide\n\nPortrait text.\n\n"
        "\\begin{landscape}\nLandscape text.\n\\end{landscape}\n"
    ))
    result = build_profile(load_profile(config, "wide"), config, ("pdf",))

    assert "Landscape text." in pdf_text(result.outputs[0])
    sizes = subprocess.run(["pdfinfo", "-f", "1", "-l", "9", str(result.outputs[0])],
                           capture_output=True, text=True, check=True).stdout
    assert re.search(r"rot:\s+(90|270)", sizes), sizes


def _docx_body(path: Path) -> list:
    return list(ET.fromstring(docx_xml(path)).find("w:body", W_NS))


def test_docx_uses_page_break_before_and_keeps_captions_with_images(tiny_config) -> None:
    config = tiny_config(figs=FIGURE_BODY)
    result = build_profile(load_profile(config, "figs"), config, ("docx",))
    body = _docx_body(result.outputs[0])
    w = "{" + W_NS["w"] + "}"

    def is_break_only(node) -> bool:
        runs = node.findall("w:r", W_NS)
        content = [child for run in runs for child in run if child.tag != w + "rPr"]
        return bool(content) and all(child.tag == w + "br" and child.get(w + "type") == "page" for child in content)

    def text_of(node) -> str:
        return "".join(t.text or "" for t in node.iterfind(".//w:t", W_NS))

    assert not [node for node in body if node.tag == w + "p" and is_break_only(node)]
    captions = [i for i, p in enumerate(body) if text_of(p).startswith("Fig. ")]
    assert [text_of(body[i]) for i in captions] == ["Fig. 1. Main caption.", "Fig. S1. Supplementary caption."]
    for i in captions:
        assert body[i + 1].find(".//w:drawing", W_NS) is not None
        assert body[i].find("w:pPr/w:keepNext", W_NS) is not None
        assert body[i].find("w:pPr/w:pageBreakBefore", W_NS) is not None


@pytest.mark.skipif(shutil.which("pdftoppm") is None or shutil.which("magick") is None,
                    reason="pdftoppm and ImageMagick required")
def test_docx_receives_png_for_pdf_figure(tiny_config, tmp_path: Path) -> None:
    figure = tmp_path / "plot.pdf"
    subprocess.run(["magick", "-size", "200x100", "xc:gray", str(figure)], check=True, capture_output=True)
    config = tiny_config(pdffig=f"# T\n\nText.\n\n![A PDF figure.]({figure}){{#fig-pdf}}\n")
    result = build_profile(load_profile(config, "pdffig"), config, ("docx",))

    with zipfile.ZipFile(result.outputs[0]) as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
        assert media and all(name.endswith(".png") for name in media), media
        assert archive.read(media[0])[:8] == b"\x89PNG\r\n\x1a\n"
    assert not any("pdftoppm" in warning for warning in result.warnings)
