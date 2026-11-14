"""What the structure stage (prepare_markdown + filters/structure.lua) guarantees."""

from __future__ import annotations

from pathlib import Path

import pytest

from makedoc.build import BuildError
from makedoc.profile import load_profile
from support import (
    FIGURES_DIR,
    TESTBED_CONFIG,
    identifier,
    is_page_break,
    manuscript,
    nodes,
    needs_pandoc,
    resolve,
    text,
)

pytestmark = needs_pandoc

FIG = FIGURES_DIR / "fig1_dummy.png"
FIGURE_LINE = "![Draft.](missing.png){#fig-x}"


def labels(blocks: list) -> list[str]:
    return [text(strong) for strong in nodes(blocks, "Strong") if text(strong).startswith("Fig. ")]


def kinds(blocks: list) -> list[str]:
    return ["BREAK" if is_page_break(block) else block["t"] for block in blocks]


@pytest.mark.parametrize("source, literal", [
    (f"```markdown\n{FIGURE_LINE}\n```\n", FIGURE_LINE),
    (f"Use `{FIGURE_LINE}` here.\n", FIGURE_LINE),
    (f"Use ``a\n{FIGURE_LINE}\nb`` here.\n", f"a {FIGURE_LINE} b"),
    (f"``\n{FIGURE_LINE}\n``\n", FIGURE_LINE),
], ids=["fenced", "code-span", "multi-line-code-span", "code-span-on-own-lines"])
def test_figure_line_in_code_stays_literal(tmp_path: Path, source: str, literal: str) -> None:
    resolved = resolve(manuscript(tmp_path, "# T\n\n" + source))

    assert nodes(resolved.blocks, "Image") == []
    assert labels(resolved.blocks) == []
    assert [node["c"][1] for node in nodes(resolved.blocks, "Code") + nodes(resolved.blocks, "CodeBlock")] == [literal]


def test_relative_image_in_second_source_resolves_against_its_own_directory(tmp_path: Path) -> None:
    (tmp_path / "second" / "fig.png").parent.mkdir(parents=True)
    (tmp_path / "second" / "fig.png").write_bytes(FIG.read_bytes())

    resolved = resolve(manuscript(tmp_path, {
        "first/main.md": "# T\n\nText.\n",
        "second/figures.md": "![One.](fig.png){#fig-one}\n",
    }))

    assert resolved.images == [(tmp_path / "second" / "fig.png").resolve()]


def test_relative_image_in_second_source_does_not_fall_back_to_the_first_directory(tmp_path: Path) -> None:
    (tmp_path / "first" / "fig.png").parent.mkdir(parents=True)
    (tmp_path / "first" / "fig.png").write_bytes(FIG.read_bytes())
    profile = manuscript(tmp_path, {
        "first/main.md": "# T\n\nText.\n",
        "second/figures.md": "![One.](fig.png){#fig-one}\n",
    })

    with pytest.raises(BuildError, match="Image file not found: fig.png") as caught:
        resolve(profile)
    assert str((tmp_path / "second").resolve()) in str(caught.value)


def test_consecutive_figure_lines_are_each_extracted(tmp_path: Path) -> None:
    resolved = resolve(manuscript(tmp_path, (
        f"# T\n\nText.\n\n![One.]({FIG}){{#fig-one}}\n![Two.]({FIG}){{#fig-two}}\n![Three.]({FIG}){{#fig-three-s1}}\n"
    )))

    assert [identifier(figure) for figure in nodes(resolved.blocks, "Figure")] == ["fig-one", "fig-two", "fig-three-s1"]
    assert labels(resolved.blocks) == ["Fig. 1.", "Fig. 2.", "Fig. S1."]
    assert [text(figure["c"][1][1]) for figure in nodes(resolved.blocks, "Figure")] == ["One.", "Two.", "Three."]


def test_fixture_figures_are_all_extracted() -> None:
    resolved = resolve(load_profile(TESTBED_CONFIG, "fixture"))

    assert [identifier(figure) for figure in nodes(resolved.blocks, "Figure")] == [
        "fig-fixture-main", "fig-fixture-richness", "fig-fixture-s1",
    ]
    assert labels(resolved.blocks) == ["Fig. 1.", "Fig. 2.", "Fig. S1."]
    assert resolved.warnings == []


@pytest.mark.parametrize("caption", ["Caption.", ""])
def test_bare_standalone_image_is_a_figure(tmp_path: Path, caption: str) -> None:
    resolved = resolve(manuscript(tmp_path, f"# T\n\nText.\n\n![{caption}]({FIG})\n\nMore text.\n"))

    assert kinds(resolved.blocks)[:3] == ["Header", "Para", "Para"]
    assert text(resolved.blocks[2]) == "More text."
    assert labels(resolved.blocks) == ["Fig. 1."]
    assert resolved.images == [FIG.resolve()]
    assert any("has no #id" in warning for warning in resolved.warnings)


def test_image_sharing_a_paragraph_with_text_is_not_a_figure(tmp_path: Path) -> None:
    resolved = resolve(manuscript(tmp_path, f"# T\n\nSee ![icon]({FIG}){{#fig-icon}} here.\n"))

    assert labels(resolved.blocks) == []
    assert nodes(resolved.blocks[1], "Image")
    assert resolved.images == [FIG.resolve()]


@pytest.mark.parametrize("placement", ["pages", "captions_page"])
def test_refs_anchor_without_references_heading_comes_before_end_figures(tmp_path: Path, placement: str) -> None:
    resolved = resolve(manuscript(
        tmp_path, f"# T\n\nText [@a].\n\n![One.]({FIG}){{#fig-one}}\n", figures={"placement": placement}
    ))

    refs = [i for i, block in enumerate(resolved.blocks) if block["t"] == "Div" and identifier(block) == "refs"]
    assert refs == [2]
    assert labels(resolved.blocks[3:])


@pytest.mark.parametrize("raw_break", ["\\clearpage", "```{=latex}\n\\clearpage\n```"], ids=["bare", "fenced-raw"])
def test_author_page_break_is_completed_for_docx_not_doubled(tmp_path: Path, raw_break: str) -> None:
    resolved = resolve(manuscript(tmp_path, f"# T\n\nAbstract.\n\n{raw_break}\n\n## Introduction\n\nBody.\n"))

    assert kinds(resolved.blocks)[:6] == ["Header", "Para", "BREAK", "BREAK", "Header", "Para"]
    formats = [block["c"][0] for block in resolved.blocks[2:4]]
    assert formats[1] == "openxml" and formats[0] in ("tex", "latex")


def test_source_file_ending_inside_an_open_div_is_reported(tmp_path: Path) -> None:
    profile = manuscript(tmp_path, {"a/one.md": "# T\n\n::: note\nUnclosed.\n", "b/two.md": "More.\n"})

    with pytest.raises(BuildError, match="unclosed block"):
        resolve(profile)


def test_clearpage_in_code_block_does_not_suppress_the_introduction_break(tmp_path: Path) -> None:
    resolved = resolve(manuscript(tmp_path, "# T\n\nAbstract.\n\n```\n\\clearpage\n```\n\n## Introduction\n\nBody.\n"))

    assert kinds(resolved.blocks)[:6] == ["Header", "Para", "CodeBlock", "BREAK", "BREAK", "Header"]
    assert [block["c"][0] for block in resolved.blocks[3:5]] == ["latex", "openxml"]


@pytest.mark.parametrize("new_page", [True, False])
def test_references_page_break_follows_the_setting(tmp_path: Path, new_page: bool) -> None:
    resolved = resolve(manuscript(
        tmp_path, "# T\n\nText.\n\n## References\n", references_new_page=new_page
    ))

    expected = ["Header", "Para", "BREAK", "BREAK", "Header", "Div"] if new_page else ["Header", "Para", "Header", "Div"]
    assert kinds(resolved.blocks) == expected


def test_explicit_refs_anchor_is_kept_and_not_duplicated(tmp_path: Path) -> None:
    resolved = resolve(manuscript(
        tmp_path, '# T\n\n## References\n\nIntro to the list.\n\n<div id="refs"></div>\n\nAfter.\n',
        references_new_page=False,
    ))

    assert kinds(resolved.blocks) == ["Header", "Header", "Para", "Div", "Para"]
    assert identifier(resolved.blocks[3]) == "refs"


def test_yaml_metadata_title_survives_and_makedoc_settings_do_not(tmp_path: Path) -> None:
    resolved = resolve(manuscript(tmp_path, {
        "a.md": "---\ntitle: The Real Title\n---\n\n# Heading\n\nText.\n",
        "b.md": "More text.\n",
    }))

    assert text(resolved.meta["title"]) == "The Real Title"
    assert "makedoc" not in resolved.meta
    assert nodes(resolved.blocks, "RawBlock") == []


def test_review_markup_in_figure_caption_is_expanded(tmp_path: Path) -> None:
    resolved = resolve(manuscript(
        tmp_path,
        f"# T\n\n![Caption {{++ added ++}} and {{-- cut --}}.]({FIG}){{#fig-a}}\n",
        review_markup={"enabled": True},
    ))

    [figure] = nodes(resolved.blocks, "Figure")
    assert text(figure["c"][1][1]) == "Caption [+ added +] and [- cut -]."
    assert [text(strong) for strong in nodes(figure["c"][1], "Strong")] == ["[+ added +]", "[- cut -]"]
    assert resolved.images == [FIG.resolve()]


def test_inline_placement_without_placeholder_warns_and_appends(tmp_path: Path) -> None:
    resolved = resolve(manuscript(
        tmp_path,
        f"# T\n\n![One.]({FIG}){{#fig-one}}\n\nText.\n\n## References\n",
        figures={"placement": "inline"},
    ))

    assert any('no <div id="figures"></div> placeholder found' in warning for warning in resolved.warnings)
    assert kinds(resolved.blocks)[-3:] == ["Div", "Para", "Figure"]
    assert identifier(resolved.blocks[-1]) == "fig-one"
    assert text(resolved.blocks[-2]) == "Fig. 1."
