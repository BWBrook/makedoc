from __future__ import annotations

from pathlib import Path

import pytest

from makedoc.build import BuildError
from makedoc.prepare import apply_review_markup, prepare_markdown
from support import FIGURES_DIR, manuscript, needs_pandoc, nodes, resolve, text

FIG = FIGURES_DIR / "fig1_dummy.png"


def image_sources(blocks: list) -> list[str]:
    return [image["c"][2][0] for image in nodes(blocks, "Image")]


def labels(blocks: list) -> list[str]:
    return [text(strong) for strong in nodes(blocks, "Strong") if text(strong).startswith("Fig. ")]


@needs_pandoc
def test_source_relative_image_path_resolves(tmp_path: Path) -> None:
    image = tmp_path / "manuscript" / "figures" / "fig1.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(FIG.read_bytes())

    resolved = resolve(manuscript(tmp_path, {
        "manuscript/text/figures.md": "![Figure](../figures/fig1.png){#fig-1 width=90%}\n",
    }))

    assert resolved.images == [image.resolve()]
    assert all(Path(src).is_absolute() for src in image_sources(resolved.blocks))


@needs_pandoc
def test_colliding_relative_image_paths_resolve_per_source_file(tmp_path: Path) -> None:
    for name in ("a", "b"):
        image = tmp_path / name / "figures" / "shared.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(FIG.read_bytes())

    resolved = resolve(manuscript(tmp_path, {
        "a/text/figures.md": "![First](../figures/shared.png){#fig-first}\n",
        "b/text/figures.md": "![Second](../figures/shared.png){#fig-second}\n",
    }))

    assert resolved.images == [
        (tmp_path / "a" / "figures" / "shared.png").resolve(),
        (tmp_path / "b" / "figures" / "shared.png").resolve(),
    ]


@needs_pandoc
def test_missing_relative_image_reports_where_it_looked(tmp_path: Path) -> None:
    profile = manuscript(tmp_path, {
        "manuscript/text/figures.md": "![Figure](../figures/missing.png){#fig-1 width=90%}\n",
    })

    with pytest.raises(BuildError, match="Image file not found") as caught:
        resolve(profile)
    assert "../figures/missing.png" in str(caught.value)
    assert str((tmp_path / "manuscript" / "figures" / "missing.png").resolve()) in str(caught.value)


@needs_pandoc
def test_image_example_in_inline_code_is_ignored(tmp_path: Path) -> None:
    resolved = resolve(manuscript(tmp_path, "Use `![Example](../figures/missing.png)` in docs.\n"))

    assert nodes(resolved.blocks, "Image") == []
    assert [code["c"][1] for code in nodes(resolved.blocks, "Code")] == ["![Example](../figures/missing.png)"]


@needs_pandoc
def test_tilde_fenced_figure_example_is_not_extracted(tmp_path: Path) -> None:
    figure_line = "![Example](../figures/example.png){#fig-example}"
    resolved = resolve(manuscript(tmp_path, f"# Demo\n\n~~~markdown\n{figure_line}\n~~~\n\nBody\n"))

    assert [block["c"][1] for block in resolved.blocks if block["t"] == "CodeBlock"] == [figure_line]
    assert labels(resolved.blocks) == []
    assert resolved.warnings == []


@needs_pandoc
def test_uppercase_supplementary_id_is_labelled_as_supplementary(tmp_path: Path) -> None:
    resolved = resolve(manuscript(tmp_path, f"# T\n\n![Supplement]({FIG}){{#fig-main-S1}}\n"))

    assert labels(resolved.blocks) == ["Fig. S1."]


@needs_pandoc
@pytest.mark.parametrize("placement", ["pages", "captions_page"])
def test_supplementary_heading_only_separates_mixed_figure_sets(tmp_path: Path, placement: str) -> None:
    supplementary = f"![Supplement]({FIG}){{#fig-main-s1}}\n"
    main = f"![Main]({FIG}){{#fig-main-1}}\n\n"
    figures = {"placement": placement}

    standalone = resolve(manuscript(tmp_path / "standalone", "# T\n\n" + supplementary, figures=figures))
    mixed = resolve(manuscript(tmp_path / "mixed", "# T\n\n" + main + supplementary, figures=figures))

    assert "## Supplementary Information" not in standalone.lines
    assert "## Supplementary Information" in mixed.lines
    assert labels(standalone.blocks)[-1] == "Fig. S1."
    assert mixed.lines.index("## Supplementary Information") < max(
        i for i, line in enumerate(mixed.lines) if "Fig. S1." in line
    )


def test_prepare_markdown_marks_each_source_directory(tmp_path: Path) -> None:
    profile = manuscript(tmp_path, {"one/a.md": "A.\n", "two/b.md": "B.\n"})

    prepared = prepare_markdown(profile)

    first = f"```{{=makedoc-source}}\n{(tmp_path / 'one').resolve()}\n```"
    second = f"```{{=makedoc-source}}\n{(tmp_path / 'two').resolve()}\n```"
    assert prepared.index(first) < prepared.index("A.") < prepared.index(second) < prepared.index("B.")


def test_review_markup_is_default_off() -> None:
    lines = ["This keeps {++ draft markup ++} untouched."]

    assert apply_review_markup(lines) == lines


def test_review_markup_renders_visible_markdown_when_enabled() -> None:
    lines = [
        "This {++ adds text ++}, {-- removes text --}, "
        "{~~ replaces old ~> adds new ~~}, and {>> check this <<}."
    ]

    assert apply_review_markup(lines, enabled=True) == [
        "This **[+ adds text +]**, **[- removes text -]**, "
        "**[- replaces old -]** **[+ adds new +]**, "
        "and **[Reviewer note: check this]**."
    ]


def test_review_markup_skips_inline_code_and_fenced_blocks() -> None:
    lines = [
        "Visible {++ added ++} but `literal {-- deletion --}` remains.",
        "",
        "```markdown",
        "{++ fenced addition ++}",
        "```",
    ]

    assert apply_review_markup(lines, enabled=True) == [
        "Visible **[+ added +]** but `literal {-- deletion --}` remains.",
        "",
        "```markdown",
        "{++ fenced addition ++}",
        "```",
    ]


def test_review_markup_expands_figure_captions() -> None:
    rendered = apply_review_markup(["![Caption {++ addition ++}.](../figures/fig1.png){#fig-1}"], enabled=True)

    assert rendered == ["![Caption **[+ addition +]**.](../figures/fig1.png){#fig-1}"]


def test_review_markup_skips_html_comment_blocks() -> None:
    lines = ["<!--", "{++ hidden addition ++}", "-->", "Visible {++ addition ++}."]

    assert apply_review_markup(lines, enabled=True) == [
        "<!--", "{++ hidden addition ++}", "-->", "Visible **[+ addition +]**.",
    ]


def test_review_markup_is_line_local() -> None:
    lines = ["{++ multiline", "addition ++}", "{~~ old", "~> new ~~}"]

    assert apply_review_markup(lines, enabled=True) == lines
