from __future__ import annotations

import shutil
from pathlib import Path

from makedoc.prepare import DOCX_PAGEBREAK_OPENXML, prepare_markdown
from makedoc.profile import load_profile
from support import FIGURES_DIR, FIXTURE_CSL, FIXTURE_REFS, TESTBED_CONFIG, write_config

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
AUTHOR_LINE = "Ava K. Morgan*^1,2^, Theo J. Patel^2^"
CLEARPAGE = "\\clearpage"
FIG1 = "Fixture main figure used for CI layout and rendering checks."
FIG2 = "Fixture richness figure used for CI cross-reference and image embedding checks."
FIGS1 = "Fixture supplementary figure used for supplementary material rendering checks."
THREE_FIGURES = (
    f"![{FIG1}](../figures/fig1_dummy.png){{#fig-fixture-main width=95%}}\n"
    f"![{FIG2}](../figures/fig2_dummy.png){{#fig-fixture-richness width=85%}}\n"
    f"![{FIGS1}](../figures/figS1_dummy.png){{#fig-fixture-s1 width=85%}}\n"
)


def line_of(lines: list[str], needle: str) -> int:
    return next(i for i, line in enumerate(lines) if needle in line)


def occurs_between(lines: list[str], needle: str, start: str, end: str) -> bool:
    lo, hi = line_of(lines, start), line_of(lines, end)
    assert lo < hi
    return any(needle in line for line in lines[lo + 1 : hi])


def prepare_single(tmp_path: Path, main: str, **profile) -> list[str]:
    main_path = tmp_path / "main.md"
    main_path.write_text(main, encoding="utf-8")
    authors = tmp_path / "authors.yaml"
    authors.write_text(AUTHORS_YAML, encoding="utf-8")
    config = write_config(tmp_path / "build.yaml", {"p": {
        "manuscript_sources": [str(main_path)],
        "bibliography": str(FIXTURE_REFS),
        "csl": str(FIXTURE_CSL),
        "author_metadata": str(authors),
        "output_dir": "out",
        "output_stem": "authors",
        "line_numbering": "none",
        **profile,
    }})
    return prepare_markdown(load_profile(config, "p")).splitlines()


def prepare_figure_repo(tmp_path: Path, main: str, figures: str, **figure_settings) -> tuple[list[str], Path]:
    repo = tmp_path / "repo"
    (repo / "manuscript" / "figures").mkdir(parents=True)
    for name in ("fig1_dummy.png", "fig2_dummy.png", "figS1_dummy.png"):
        shutil.copy(FIGURES_DIR / name, repo / "manuscript" / "figures" / name)
    text = repo / "manuscript" / "text"
    text.mkdir()
    (text / "main.md").write_text(main, encoding="utf-8")
    (text / "figures.md").write_text(figures, encoding="utf-8")
    config = write_config(repo / "settings" / "build.yaml", {"p": {
        "manuscript_sources": ["../manuscript/text/main.md", "../manuscript/text/figures.md"],
        "bibliography": str(FIXTURE_REFS),
        "output_dir": "dist",
        "output_stem": "fixture",
        "figures": {"placeholder_id": "figures", **figure_settings},
    }})
    figures_dir = (repo / "manuscript" / "figures").resolve()
    return prepare_markdown(load_profile(config, "p")).splitlines(), figures_dir


def test_author_placeholder_is_replaced_with_author_block_and_page_breaks(tmp_path: Path) -> None:
    lines = prepare_single(tmp_path, (
        "# Author Injection Placeholder Check\n\n<div id=\"authors\"></div>\n\n## Abstract\n\n"
        "Synthetic abstract body.\n\n## Keywords\n\nworkflow; fixtures\n\n## Introduction\n\n"
        "Body starts here.\n\n## References\n\nDummy reference list placeholder.\n"
    ))
    text = "\n".join(lines)

    assert '<div id="authors"></div>' not in text
    assert AUTHOR_LINE in text
    assert "1. Department of Synthetic Ecology, Harborview University" in text
    assert "2. Centre for Reproducible Workflows, Southern Institute of Systems Science" in text
    assert "**Corresponding author:** Ava K. Morgan (ava.morgan@example.org)" in text
    assert line_of(lines, "# Author Injection Placeholder Check") < line_of(lines, AUTHOR_LINE) < line_of(lines, "## Abstract")
    assert occurs_between(lines, CLEARPAGE, AUTHOR_LINE, "## Abstract")
    assert occurs_between(lines, CLEARPAGE, "## Keywords", "## Introduction")
    assert occurs_between(lines, CLEARPAGE, "## Introduction", "## References")
    assert text.count(CLEARPAGE) >= 3
    assert text.count(DOCX_PAGEBREAK_OPENXML) >= 3
    keywords = line_of(lines, "## Keywords")
    assert lines[keywords - 1].strip() == lines[keywords - 2].strip() == ""


def test_author_block_falls_back_to_after_title_without_placeholder(tmp_path: Path) -> None:
    lines = prepare_single(tmp_path, (
        "# Author Injection Fallback Check\n\nBody starts here.\n\n## References\n\n"
        "Dummy reference list placeholder.\n"
    ))
    assert (
        line_of(lines, "# Author Injection Fallback Check")
        < line_of(lines, AUTHOR_LINE)
        < line_of(lines, "Body starts here.")
    )


def test_pages_mode_puts_each_figure_on_its_own_page_with_supplementary_last(tmp_path: Path) -> None:
    lines, _ = prepare_figure_repo(
        tmp_path,
        "# Figure Mode Regression: pages\n\nNo figure placeholder.\n\n## References\n\nDummy.\n",
        THREE_FIGURES,
        placement="pages",
        caption_position="top",
    )
    text = "\n".join(lines)

    for label in ("**Fig. 1.**", "**Fig. 2.**", "**Fig. S1.**", "## Supplementary Information"):
        assert label in text
    assert line_of(lines, "**Fig. 1.**") < line_of(lines, "**Fig. 2.**") < line_of(lines, "**Fig. S1.**")
    assert (
        line_of(lines, "**Fig. 2.**")
        < line_of(lines, "## Supplementary Information")
        < line_of(lines, "**Fig. S1.**")
    )
    assert line_of(lines, "**Fig. 1.**") < line_of(lines, f"![{FIG1}]")
    assert text.count(CLEARPAGE) >= 4
    assert text.count(DOCX_PAGEBREAK_OPENXML) >= 4
    assert '<div id="figures"></div>' not in text


def test_inline_mode_replaces_placeholder_with_bottom_caption(tmp_path: Path) -> None:
    lines, _ = prepare_figure_repo(
        tmp_path,
        "# Figure Mode Regression: inline\n\nText before inserted figures.\n\n<div id=\"figures\"></div>\n\n"
        "More text after placeholder.\n\n## References\n\nDummy reference list placeholder.\n",
        f"![{FIG1}](../figures/fig1_dummy.png){{#fig-fixture-main width=95%}}\n",
        placement="inline",
        caption_position="bottom",
    )
    text = "\n".join(lines)

    assert '<div id="figures"></div>' not in text
    assert text.count(CLEARPAGE) == 1
    assert text.count(DOCX_PAGEBREAK_OPENXML) == 1
    assert occurs_between(lines, CLEARPAGE, "More text after placeholder.", "## References")
    assert line_of(lines, "Text before inserted figures.") < line_of(lines, f"![{FIG1}]")
    assert line_of(lines, f"![{FIG1}]") < line_of(lines, "**Fig. 1.**") < line_of(lines, "More text after placeholder.")


def test_inline_mode_empty_alt_text_suppresses_automatic_caption(tmp_path: Path) -> None:
    lines, figures_dir = prepare_figure_repo(
        tmp_path,
        "# Inline empty alt\n\nText before.\n\n<div id=\"figures\"></div>\n\nCustom caption text.\n\n"
        "## References\n\nDummy.\n",
        "![](../figures/fig1_dummy.png){#fig-fixture-main width=95%}\n",
        placement="inline",
        caption_position="top",
    )
    text = "\n".join(lines)

    assert '<div id="figures"></div>' not in text
    assert f"![]({(figures_dir / 'fig1_dummy.png').as_posix()}){{#fig-fixture-main width=95%}}" in text
    assert "**Fig. 1.**" not in text


def test_captions_page_lists_captions_then_anchored_figure_pages(tmp_path: Path) -> None:
    lines, figures_dir = prepare_figure_repo(
        tmp_path,
        "# Figure Mode Regression: captions page\n\nNo inline figure slot.\n\n## References\n\nDummy.\n",
        THREE_FIGURES,
        placement="captions_page",
        caption_position="top",
    )
    text = "\n".join(lines)

    caption_lines = [f"**Fig. 1.** {FIG1}", f"**Fig. 2.** {FIG2}", f"**Fig. S1.** {FIGS1}"]
    for caption in caption_lines:
        assert caption in lines
        assert f"- {caption}" not in text
    assert (
        line_of(lines, "## Figure Captions")
        < lines.index(caption_lines[0])
        < lines.index(caption_lines[1])
        < line_of(lines, "## Supplementary Information")
    )
    assert text.count(CLEARPAGE) >= 5
    assert text.count(DOCX_PAGEBREAK_OPENXML) >= 5

    for label, fig_id, name, title, width in (
        ("Fig. 1", "fig-fixture-main", "fig1_dummy.png", FIG1, "95%"),
        ("Fig. 2", "fig-fixture-richness", "fig2_dummy.png", FIG2, "85%"),
        ("Fig. S1", "fig-fixture-s1", "figS1_dummy.png", FIGS1, "85%"),
    ):
        anchor = f"[**{label}.**]{{#{fig_id}}}"
        assert anchor in lines
        image = f"![{title}]({(figures_dir / name).as_posix()}){{width={width}}}\\ "
        assert image in lines
        assert lines.index(anchor) < lines.index(image)
        assert f"#{fig_id} " not in lines[lines.index(image)]
    assert line_of(lines, "## Supplementary Information") < lines.index("[**Fig. S1.**]{#fig-fixture-s1}")


def test_profile_paths_and_image_paths_resolve_from_config_and_markdown(tmp_path: Path) -> None:
    repo = tmp_path / "with spaces (probe)" / "external paper"
    (repo / "manuscript" / "figures").mkdir(parents=True)
    shutil.copy(FIGURES_DIR / "fig1_dummy.png", repo / "manuscript" / "figures")
    text = repo / "manuscript" / "text"
    text.mkdir()
    (text / "main.md").write_text("# External\n\nBody.\n", encoding="utf-8")
    (text / "figures.md").write_text("![One.](../figures/fig1_dummy.png){#fig-one}\n", encoding="utf-8")
    (repo / "refs.yaml").write_text("references: []\n", encoding="utf-8")
    config = write_config(repo / "settings" / "build.yaml", {"ext": {
        "manuscript_sources": ["../manuscript/text/main.md", "../manuscript/text/figures.md"],
        "bibliography": "../refs.yaml",
        "output_dir": "dist",
        "output_stem": "manuscript",
    }})

    profile = load_profile(config, "ext")
    prepared = prepare_markdown(profile)

    assert profile.manuscript_sources[0] == str((text / "main.md").resolve())
    assert profile.bibliography == str((repo / "refs.yaml").resolve())
    assert profile.output_dir == str((repo / "settings" / "dist").resolve())
    assert (repo / "manuscript" / "figures" / "fig1_dummy.png").resolve().as_posix() in prepared


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

