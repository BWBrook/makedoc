"""Regressions for defects found in review of makedoc 2.0."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from makedoc.build import build_profile
from makedoc.docx import WP_NS, normalize_document_layout
from makedoc.layout import render_layout
from makedoc.markdown_scan import scan_lines
from makedoc.prepare import (
    extract_figures,
    image_resources,
    load_markdown_sources,
    reference_placement,
    split_image_destination,
)
from makedoc.profile import load_profile
from makedoc.refs import scan_citations
from makedoc.validate import validate_config
from support import FIGURES_DIR, FIXTURE_REFS, needs_pandoc, needs_pdf, needs_poppler, pdf_text, write_config

FIG = FIGURES_DIR / "fig1_dummy.png"


def test_figure_inside_comment_opened_mid_line_stays_hidden() -> None:
    lines = ["Visible text <!-- hidden", f"![Draft.]({FIG}){{#fig-x}}", "-->", "After."]
    remaining, figures = extract_figures(lines)
    assert figures == []
    assert remaining == lines


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


def test_image_with_citation_in_caption_is_tracked(tmp_path: Path) -> None:
    source = tmp_path / "figures.md"
    source.write_text(f"![Data from [@alpha2020].]({FIG}){{#fig-a}}\n", encoding="utf-8")
    assert image_resources([source]) == [FIG]


@pytest.mark.parametrize("destination", ['{} "A title"', "<{}>", "{}"])
def test_image_destination_forms_resolve(tmp_path: Path, destination: str) -> None:
    (tmp_path / "fig.png").write_bytes(FIG.read_bytes())
    source = tmp_path / "figures.md"
    source.write_text(f"![Caption.]({destination.format('fig.png')}){{#fig-a}}\n", encoding="utf-8")
    assert (tmp_path / "fig.png").resolve().as_posix() in load_markdown_sources([str(source)])
    assert split_image_destination(destination.format("fig.png"))[1] == "fig.png"


def test_missing_absolute_image_fails(tmp_path: Path) -> None:
    source = tmp_path / "figures.md"
    source.write_text(f"![Caption.]({tmp_path / 'absent.png'}){{#fig-a}}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Image file not found"):
        load_markdown_sources([str(source)])


def test_bibliography_is_anchored_at_the_end_without_a_references_heading() -> None:
    assert reference_placement(["# T", "", "Text [@a]."])[-1] == '<div id="refs"></div>'


def test_refs_anchor_inside_comment_does_not_suppress_the_real_one() -> None:
    lines = ["## References", "", '<!-- <div id="refs"></div> -->']
    assert '<div id="refs"></div>' in reference_placement(lines, references_new_page=False)


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
