"""Regressions for defects found in review of makedoc 2.0."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from makedoc.build import BuildError, build_profile
from makedoc.docx import WP_NS, normalize_document_layout
from makedoc.layout import render_layout
from makedoc.markdown_scan import scan_lines
from makedoc.profile import load_profile
from makedoc.refs import scan_citations
from makedoc.validate import validate_config
from support import (
    FIGURES_DIR,
    FIXTURE_REFS,
    identifier,
    manuscript,
    needs_pandoc,
    needs_pdf,
    needs_poppler,
    nodes,
    pdf_text,
    resolve,
    text,
    write_config,
)

FIG = FIGURES_DIR / "fig1_dummy.png"


@needs_pandoc
@pytest.mark.parametrize("source", [
    f"Visible text <!-- hidden\n![Draft.]({FIG}){{#fig-x}}\n-->\nAfter.\n",
    f"Visible text <!-- hidden\n\n![Draft.]({FIG}){{#fig-x}}\n\n-->\n\nAfter.\n",
    "<!--\n![Draft.](missing.png){#fig-x}\n-->\n\nAfter.\n",
], ids=["mid-line", "mid-line-with-blank-lines", "block"])
def test_figure_inside_comment_is_not_extracted(tmp_path: Path, source: str) -> None:
    resolved = resolve(manuscript(tmp_path, "# T\n\n" + source))

    assert nodes(resolved.blocks, "Image") == []
    assert nodes(resolved.blocks, "Figure") == []
    assert "Fig. 1." not in resolved.markdown
    assert "After." in text(resolved.blocks)
    assert resolved.images == []


def test_text_after_a_one_line_comment_is_still_scanned(tmp_path: Path) -> None:
    source = tmp_path / "a.md"
    source.write_text("<!-- note --> See [@visible2020].\n", encoding="utf-8")
    assert [hit.key for hit in scan_citations(source)] == ["visible2020"]


def test_comment_opener_inside_fence_does_not_hide_later_prose() -> None:
    lines = ["```html", "<!-- literal", "```", "Prose."]
    assert [visible for visible, _ in scan_lines(lines)] == [False, False, False, True]


@pytest.mark.parametrize(
    "key", ["10.1038/nature123", "doe/2020", "doe&2020", "doe?2020", "smith_2020", "a:b.c-d+e"]
)
def test_citation_keys_with_internal_punctuation(tmp_path: Path, key: str) -> None:
    source = tmp_path / "a.md"
    source.write_text(f"Shown before [@{key}]. And @{{{key}}}.\n", encoding="utf-8")
    assert [hit.key for hit in scan_citations(source)] == [key, key]


def test_trailing_sentence_punctuation_is_not_part_of_a_key(tmp_path: Path) -> None:
    source = tmp_path / "a.md"
    source.write_text("As shown by @doe2020. Mail me@example.org.\n", encoding="utf-8")
    assert [hit.key for hit in scan_citations(source)] == ["doe2020"]


@needs_pandoc
@pytest.mark.parametrize("destination", [
    "fig.png",
    'fig.png "A title"',
    "<fig.png>",
    "<my figure.png>",
    '<my figure.png> "A title"',
])
def test_image_destination_forms_resolve(tmp_path: Path, destination: str) -> None:
    name = "my figure.png" if "my figure" in destination else "fig.png"
    (tmp_path / name).write_bytes(FIG.read_bytes())

    resolved = resolve(manuscript(tmp_path, f"# T\n\n![Caption.]({destination}){{#fig-a}}\n"))

    assert resolved.images == [(tmp_path / name).resolve()]
    assert [identifier(figure) for figure in nodes(resolved.blocks, "Figure")] == ["fig-a"]
    if "title" in destination:
        assert nodes(resolved.blocks, "Image")[0]["c"][2][1] == "A title"


@needs_pandoc
def test_image_with_citation_in_caption_is_tracked(tmp_path: Path) -> None:
    resolved = resolve(manuscript(tmp_path, f"# T\n\n![Data from [@alpha2020].]({FIG}){{#fig-a}}\n"))

    assert resolved.images == [FIG.resolve()]
    [figure] = nodes(resolved.blocks, "Figure")
    assert {cite["c"][0][0]["citationId"] for cite in nodes(figure, "Cite")} == {"alpha2020"}


@needs_pandoc
def test_missing_absolute_image_fails(tmp_path: Path) -> None:
    absent = tmp_path / "absent.png"
    with pytest.raises(BuildError, match=f"Image file not found: {absent}"):
        resolve(manuscript(tmp_path, f"![Caption.]({absent}){{#fig-a}}\n"))


@needs_pandoc
def test_bibliography_is_anchored_at_the_end_without_a_references_heading(tmp_path: Path) -> None:
    resolved = resolve(manuscript(tmp_path, "# T\n\nText [@a].\n"))

    assert resolved.blocks[-1]["t"] == "Div"
    assert identifier(resolved.blocks[-1]) == "refs"


@needs_pandoc
@pytest.mark.parametrize("decoy", [
    '<!-- <div id="refs"></div> -->',
    '```html\n<div id="refs"></div>\n```',
    'Write `<div id="refs"></div>` to place it.',
], ids=["comment", "fenced-code", "code-span"])
def test_refs_anchor_in_comment_or_code_does_not_suppress_the_real_one(tmp_path: Path, decoy: str) -> None:
    resolved = resolve(manuscript(
        tmp_path, f"# T\n\n## References\n\n{decoy}\n", references_new_page=False
    ))

    divs = [identifier(div) for div in nodes(resolved.blocks, "Div")]
    assert divs == ["refs"]
    assert resolved.blocks[2]["t"] == "Div"


def _config(tmp_path: Path, **overrides: object) -> Path:
    source = tmp_path / "main.md"
    source.write_text("# T\n\nText.\n", encoding="utf-8")
    return write_config(tmp_path / "build.yaml", {"p": {
        "manuscript_sources": [str(source)], "bibliography": str(FIXTURE_REFS),
        "output_dir": "out", "output_stem": "p", **overrides,
    }})


@pytest.mark.parametrize("overrides, key", [
    ({"author_metadata": ["authors.yaml"]}, "author_metadata"),
    ({"csl": ["journal.csl"]}, "csl"),
    ({"review_markup": {"enabled": "ture"}}, "enabled"),
    ({"references_new_page": "fales"}, "references_new_page"),
])
def test_invalid_optional_values_are_reported(tmp_path: Path, overrides: dict, key: str) -> None:
    problems = validate_config(_config(tmp_path, **overrides), [])
    assert any(key in problem for problem in problems), problems


def test_section_line_numbering_hooks_the_section_command(tmp_path: Path) -> None:
    layout = render_layout(load_profile(_config(tmp_path, line_numbering="section")))
    assert r"\pretocmd{\section}{\resetlinenumber}" in layout
    assert "AtBeginEnvironment" not in layout


def test_title_page_follows_the_page_number_setting(tmp_path: Path) -> None:
    assert r"\let\ps@plain\ps@empty" in render_layout(load_profile(_config(tmp_path, page_numbers="none")))
    assert r"\let\ps@plain\ps@makedoclowerright" in render_layout(load_profile(_config(tmp_path)))


@needs_pdf
@needs_poppler
def test_section_numbering_builds_and_restarts(tmp_path: Path) -> None:
    source = tmp_path / "main.md"
    source.write_text("# One\n\nFirst.\n\nSecond.\n\n# Two\n\nThird.\n", encoding="utf-8")
    config = write_config(tmp_path / "build.yaml", {"p": {
        "manuscript_sources": [str(source)], "bibliography": str(FIXTURE_REFS),
        "output_dir": "out", "output_stem": "p", "line_numbering": "section",
    }})
    result = build_profile(load_profile(config, "p"), config, ("pdf",))
    numbers = [int(token) for token in pdf_text(result.outputs[0]).split() if token.isdigit()]
    assert numbers.count(1) >= 3


@needs_pandoc
def test_docx_images_are_scaled_to_the_text_area(tmp_path: Path) -> None:
    import subprocess

    source = tmp_path / "a.md"
    source.write_text(f"![Wide.]({FIG}){{width=100%}}\n", encoding="utf-8")
    docx = tmp_path / "a.docx"
    subprocess.run(["pandoc", str(source), "-o", str(docx)], check=True)
    document = zipfile.ZipFile(io.BytesIO(docx.read_bytes())).read("word/document.xml")
    margins = {"top": 2.0, "right": 4.0, "bottom": 2.0, "left": 4.0}
    fitted = ET.fromstring(normalize_document_layout(document, paper_size="a4", margins=margins, margin_unit="cm"))
    text_width_emu = (11906 - 2 * round(4.0 * 1440 / 2.54)) * 635
    extents = [int(node.get("cx")) for node in fitted.iter(f"{{{WP_NS}}}extent")]
    assert extents and all(cx <= text_width_emu for cx in extents)


UNICODE_FILTER = Path(__file__).resolve().parents[1] / "src" / "makedoc" / "filters" / "unicode_fallback.lua"


@needs_pandoc
def test_fallback_characters_survive_in_pdf_metadata_and_bookmarks(tmp_path: Path) -> None:
    import subprocess

    source = tmp_path / "a.md"
    source.write_text(
        '---\ntitle: "CO₂ and α"\n---\n\n# α diversity & CO₂ {#sec-a}\n\nText.\n\n## Plain heading\n',
        encoding="utf-8",
    )
    latex = subprocess.run(
        ["pandoc", str(source), f"--lua-filter={UNICODE_FILTER}", "-t", "latex", "-s"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "pdftitle={CO₂ and α}" in latex
    assert r'{\unichar{"03B1} diversity \& CO\unichar{"2082}}}\label{sec-a}' in latex
    assert r"\makedocchar{03B1}{\ensuremath{\alpha}} diversity" in latex
    assert r"\subsection{Plain heading}\label{plain-heading}" in latex


@needs_pdf
@needs_poppler
def test_heading_and_title_with_symbols_build_without_warnings(tmp_path: Path) -> None:
    import subprocess

    source = tmp_path / "main.md"
    source.write_text(
        '---\ntitle: "CO₂ and α"\n---\n\n# α diversity and CO₂ {#sec-a}\n\nSee [above](#sec-a).\n',
        encoding="utf-8",
    )
    config = write_config(tmp_path / "build.yaml", {"p": {
        "manuscript_sources": [str(source)], "bibliography": str(FIXTURE_REFS),
        "output_dir": "out", "output_stem": "p",
    }})
    result = build_profile(load_profile(config, "p"), config, ("pdf",))
    assert result.warnings == []
    info = subprocess.run(["pdfinfo", str(result.outputs[0])], capture_output=True, text=True, check=True).stdout
    assert "CO₂ and α" in info
