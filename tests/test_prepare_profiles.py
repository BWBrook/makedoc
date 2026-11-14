from __future__ import annotations

import shutil
from pathlib import Path

from makedoc.prepare import author_block_markdown, prepare_markdown
from makedoc.profile import load_profile
from support import (
    FIGURES_DIR,
    FIXTURE_REFS,
    TESTBED_CONFIG,
    identifier,
    is_page_break,
    manuscript,
    needs_pandoc,
    nodes,
    resolve,
    text,
    write_config,
)

AUTHORS_YAML = """\
title_note: Synthetic author metadata block
authors:
  - name: Ava K. Morgan
    affiliations: [aff1, aff2]
    corresponding: true
    email: ava.morgan@example.org
  - name: Theo J. Patel
    affiliations: [aff2]
affiliations:
  aff1: Department of Synthetic Ecology, Harborview University
  aff2: Centre for Reproducible Workflows, Southern Institute of Systems Science
"""
AUTHOR_TEXT = "Ava K. Morgan*1,2, Theo J. Patel2"
FIG1 = "Fixture main figure used for CI layout and rendering checks."
FIG2 = "Fixture richness figure used for CI cross-reference and image embedding checks."
FIGS1 = "Fixture supplementary figure used for supplementary material rendering checks."
THREE_FIGURES = (
    f"![{FIG1}](../figures/fig1_dummy.png){{#fig-fixture-main width=95%}}\n"
    f"![{FIG2}](../figures/fig2_dummy.png){{#fig-fixture-richness width=85%}}\n"
    f"![{FIGS1}](../figures/figS1_dummy.png){{#fig-fixture-s1 width=85%}}\n"
)
LATEX_BREAK = "\\clearpage"
DOCX_BREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def outline(blocks: list) -> list[str]:
    """Top-level blocks as short labels: headings, page breaks, figures, images and text."""
    out = []
    for block in blocks:
        kind = block["t"]
        if kind == "Header":
            out.append("#" * block["c"][0] + " " + text(block["c"][2]))
        elif is_page_break(block):
            out.append("BREAK:" + block["c"][0])
        elif kind == "Div":
            out.append(f"DIV#{identifier(block)}")
        elif kind == "Figure":
            out.append(f"FIGURE#{identifier(block)}")
        else:
            out.append(text(block))
    return out


def index_of(items: list[str], needle: str) -> int:
    return next(i for i, item in enumerate(items) if needle in item)


def breaks_between(items: list[str], start: str, end: str) -> list[str]:
    lo, hi = index_of(items, start), index_of(items, end)
    assert lo < hi
    return [item for item in items[lo + 1 : hi] if item.startswith("BREAK:")]


def resolve_with_authors(tmp_path: Path, main: str, **profile):
    authors = tmp_path / "authors.yaml"
    authors.write_text(AUTHORS_YAML, encoding="utf-8")
    return resolve(manuscript(tmp_path, main, author_metadata=str(authors), line_numbering="none", **profile))


def resolve_figure_repo(tmp_path: Path, main: str, figures: str, **figure_settings):
    repo = tmp_path / "repo"
    (repo / "manuscript" / "figures").mkdir(parents=True)
    for name in ("fig1_dummy.png", "fig2_dummy.png", "figS1_dummy.png"):
        shutil.copy(FIGURES_DIR / name, repo / "manuscript" / "figures" / name)
    text_dir = repo / "manuscript" / "text"
    text_dir.mkdir()
    (text_dir / "main.md").write_text(main, encoding="utf-8")
    (text_dir / "figures.md").write_text(figures, encoding="utf-8")
    config = write_config(repo / "settings" / "build.yaml", {"p": {
        "manuscript_sources": ["../manuscript/text/main.md", "../manuscript/text/figures.md"],
        "bibliography": str(FIXTURE_REFS),
        "output_dir": "dist",
        "output_stem": "fixture",
        "figures": {"placeholder_id": "figures", **figure_settings},
    }})
    return resolve(load_profile(config, "p")), (repo / "manuscript" / "figures").resolve()


def test_author_block_markdown_lists_authors_affiliations_and_contact(tmp_path: Path) -> None:
    authors = tmp_path / "authors.yaml"
    authors.write_text(AUTHORS_YAML, encoding="utf-8")

    block = author_block_markdown(str(authors)).splitlines()

    assert block[0] == "Ava K. Morgan*^1,2^, Theo J. Patel^2^"
    assert "*Synthetic author metadata block*" in block
    assert "1. Department of Synthetic Ecology, Harborview University" in block
    assert "2. Centre for Reproducible Workflows, Southern Institute of Systems Science" in block
    assert block[-1] == "**Corresponding author:** Ava K. Morgan (ava.morgan@example.org)"


@needs_pandoc
def test_author_placeholder_is_replaced_with_author_block_and_page_breaks(tmp_path: Path) -> None:
    resolved = resolve_with_authors(tmp_path, (
        "# Author Injection Placeholder Check\n\n<div id=\"authors\"></div>\n\n## Abstract\n\n"
        "Synthetic abstract body.\n\n## Keywords\n\nworkflow; fixtures\n\n## Introduction\n\n"
        "Body starts here.\n\n## References\n\nDummy reference list placeholder.\n"
    ))
    items = outline(resolved.blocks)

    assert "DIV#authors" not in items
    assert items[0] == "# Author Injection Placeholder Check"
    assert items[1] == AUTHOR_TEXT
    assert "Corresponding author: Ava K. Morgan (ava.morgan@example.org)" in items
    assert [text(item) for item in nodes(resolved.blocks, "OrderedList")[0]["c"][1]] == [
        "Department of Synthetic Ecology, Harborview University",
        "Centre for Reproducible Workflows, Southern Institute of Systems Science",
    ]
    pair = ["BREAK:latex", "BREAK:openxml"]
    assert breaks_between(items, "Corresponding author", "## Abstract") == pair
    assert breaks_between(items, "## Abstract", "## Keywords") == []
    assert breaks_between(items, "## Keywords", "## Introduction") == pair
    assert breaks_between(items, "## Introduction", "## References") == pair
    assert resolved.markdown.count(LATEX_BREAK) == 3
    assert resolved.markdown.count(DOCX_BREAK) == 3


@needs_pandoc
def test_author_block_falls_back_to_after_title_without_placeholder(tmp_path: Path) -> None:
    resolved = resolve_with_authors(tmp_path, (
        "# Author Injection Fallback Check\n\nBody starts here.\n\n## References\n\n"
        "Dummy reference list placeholder.\n"
    ))
    items = outline(resolved.blocks)

    assert items.index("# Author Injection Fallback Check") < items.index(AUTHOR_TEXT) < items.index("Body starts here.")


@needs_pandoc
def test_author_page_break_is_not_doubled_before_an_immediate_introduction(tmp_path: Path) -> None:
    resolved = resolve_with_authors(tmp_path, "# Title\n\n## Introduction\n\nBody.\n")
    items = outline(resolved.blocks)

    assert breaks_between(items, "Corresponding author", "## Introduction") == ["BREAK:latex", "BREAK:openxml"]


@needs_pandoc
def test_pages_mode_puts_each_figure_on_its_own_page_with_supplementary_last(tmp_path: Path) -> None:
    resolved, _ = resolve_figure_repo(
        tmp_path,
        "# Figure Mode Regression: pages\n\nNo figure placeholder.\n\n## References\n\nDummy.\n",
        THREE_FIGURES,
        placement="pages",
        caption_position="top",
    )
    items = outline(resolved.blocks)

    assert [item for item in items if item.startswith(("Fig.", "FIGURE", "## Supp"))] == [
        "Fig. 1.", "FIGURE#fig-fixture-main",
        "Fig. 2.", "FIGURE#fig-fixture-richness",
        "## Supplementary Information",
        "Fig. S1.", "FIGURE#fig-fixture-s1",
    ]
    assert breaks_between(items, "## References", "Fig. 1.")
    assert breaks_between(items, "FIGURE#fig-fixture-main", "Fig. 2.")
    assert breaks_between(items, "## Supplementary Information", "Fig. S1.")
    assert resolved.markdown.count(LATEX_BREAK) == resolved.markdown.count(DOCX_BREAK) >= 4
    assert "DIV#figures" not in items


@needs_pandoc
def test_inline_mode_replaces_placeholder_with_bottom_caption(tmp_path: Path) -> None:
    resolved, _ = resolve_figure_repo(
        tmp_path,
        "# Figure Mode Regression: inline\n\nText before inserted figures.\n\n<div id=\"figures\"></div>\n\n"
        "More text after placeholder.\n\n## References\n\nDummy reference list placeholder.\n",
        f"![{FIG1}](../figures/fig1_dummy.png){{#fig-fixture-main width=95%}}\n",
        placement="inline",
        caption_position="bottom",
    )
    items = outline(resolved.blocks)

    assert "DIV#figures" not in items
    assert items[1:4] == ["Text before inserted figures.", "FIGURE#fig-fixture-main", "Fig. 1."]
    assert items[4] == "More text after placeholder."
    assert resolved.markdown.count(LATEX_BREAK) == resolved.markdown.count(DOCX_BREAK) == 1
    assert breaks_between(items, "More text after placeholder.", "## References")
    assert resolved.warnings == []


@needs_pandoc
def test_inline_mode_empty_alt_text_suppresses_automatic_caption(tmp_path: Path) -> None:
    resolved, figures_dir = resolve_figure_repo(
        tmp_path,
        "# Inline empty alt\n\nText before.\n\n<div id=\"figures\"></div>\n\nCustom caption text.\n\n"
        "## References\n\nDummy.\n",
        "![](../figures/fig1_dummy.png){#fig-fixture-main width=95%}\n",
        placement="inline",
        caption_position="top",
    )
    items = outline(resolved.blocks)
    placed = resolved.blocks[items.index("Text before.") + 1]

    assert "DIV#figures" not in items
    assert placed["t"] == "Para"
    [image] = placed["c"]
    assert image["t"] == "Image"
    assert image["c"][0] == ["fig-fixture-main", [], [["width", "95%"]]]
    assert image["c"][1] == []
    assert Path(image["c"][2][0]).resolve() == figures_dir / "fig1_dummy.png"
    assert not any(item.startswith("Fig.") for item in items)


@needs_pandoc
def test_captions_page_lists_captions_then_anchored_figure_pages(tmp_path: Path) -> None:
    resolved, figures_dir = resolve_figure_repo(
        tmp_path,
        "# Figure Mode Regression: captions page\n\nNo inline figure slot.\n\n## References\n\nDummy.\n",
        THREE_FIGURES,
        placement="captions_page",
        caption_position="top",
    )
    items = outline(resolved.blocks)
    blocks = resolved.blocks

    captions = [f"Fig. 1. {FIG1}", f"Fig. 2. {FIG2}", f"Fig. S1. {FIGS1}"]
    heading = items.index("## Figure Captions")
    assert items[heading + 1 : heading + 4] == captions
    assert all(blocks[heading + offset]["t"] == "Para" for offset in (1, 2, 3))
    assert nodes(blocks, "BulletList") == []
    assert breaks_between(items, "## References", "## Figure Captions")
    assert resolved.markdown.count(LATEX_BREAK) == resolved.markdown.count(DOCX_BREAK) >= 5

    for label, fig_id, name, width in (
        ("Fig. 1.", "fig-fixture-main", "fig1_dummy.png", "95%"),
        ("Fig. 2.", "fig-fixture-richness", "fig2_dummy.png", "85%"),
        ("Fig. S1.", "fig-fixture-s1", "figS1_dummy.png", "85%"),
    ):
        [anchor] = [span for span in nodes(blocks, "Span") if identifier(span) == fig_id]
        assert [node["t"] for node in anchor["c"][1]] == ["Strong"]
        assert text(anchor) == label
        position = next(i for i, block in enumerate(blocks) if anchor in block.get("c", []))
        assert position > heading + 3
        assert is_page_break(blocks[position - 1])
        image_para = blocks[position + 1]
        assert image_para["t"] == "Para"
        [image] = image_para["c"]
        assert image["t"] == "Image"
        assert image["c"][0] == ["", [], [["width", width]]]
        assert Path(image["c"][2][0]).resolve() == figures_dir / name
    assert nodes(blocks, "Figure") == []
    anchors = [i for i, block in enumerate(blocks) if block["t"] == "Para" and nodes(block, "Span")]
    assert anchors[1] < items.index("## Supplementary Information") < anchors[2]


@needs_pandoc
def test_profile_paths_and_image_paths_resolve_from_config_and_markdown(tmp_path: Path) -> None:
    repo = tmp_path / "with spaces (probe)" / "external paper"
    (repo / "manuscript" / "figures").mkdir(parents=True)
    shutil.copy(FIGURES_DIR / "fig1_dummy.png", repo / "manuscript" / "figures")
    text_dir = repo / "manuscript" / "text"
    text_dir.mkdir()
    (text_dir / "main.md").write_text("# External\n\nBody.\n", encoding="utf-8")
    (text_dir / "figures.md").write_text("![One.](../figures/fig1_dummy.png){#fig-one}\n", encoding="utf-8")
    (repo / "refs.yaml").write_text("references: []\n", encoding="utf-8")
    config = write_config(repo / "settings" / "build.yaml", {"ext": {
        "manuscript_sources": ["../manuscript/text/main.md", "../manuscript/text/figures.md"],
        "bibliography": "../refs.yaml",
        "output_dir": "dist",
        "output_stem": "manuscript",
    }})

    profile = load_profile(config, "ext")

    assert profile.manuscript_sources[0] == str((text_dir / "main.md").resolve())
    assert profile.bibliography == str((repo / "refs.yaml").resolve())
    assert profile.output_dir == str((repo / "settings" / "dist").resolve())
    assert resolve(profile).images == [(repo / "manuscript" / "figures" / "fig1_dummy.png").resolve()]


def test_review_markup_probe_renders_visible_markers() -> None:
    prepared = prepare_markdown(load_profile(TESTBED_CONFIG, "review_markup"))

    for marker in (
        "**[+ inserted review text +]**",
        "**[- removed review text -]**",
        "**[- outdated wording -]** **[+ revised wording +]**",
        "**[Reviewer note: reviewer asks for a clearer transition]**",
        "`{++ literal addition ++}`",
        "{-- fenced deletion should remain literal --}",
    ):
        assert marker in prepared
    for raw in (
        "{++ inserted review text ++}",
        "{-- removed review text --}",
        "{~~ outdated wording ~> revised wording ~~}",
        "{>> reviewer asks for a clearer transition <<}",
    ):
        assert raw not in prepared


@needs_pandoc
def test_review_markup_probe_survives_parsing() -> None:
    blocks = resolve(load_profile(TESTBED_CONFIG, "review_markup")).blocks

    assert [text(strong) for strong in nodes(blocks, "Strong")] == [
        "ordinary Markdown",
        "[+ inserted review text +]",
        "[- removed review text -]",
        "[- outdated wording -]",
        "[+ revised wording +]",
        "[Reviewer note: reviewer asks for a clearer transition]",
    ]
    assert [code["c"][1] for code in nodes(blocks, "Code")] == ["{++ literal addition ++}"]
    assert [code["c"][1] for code in nodes(blocks, "CodeBlock")] == ["{-- fenced deletion should remain literal --}"]
