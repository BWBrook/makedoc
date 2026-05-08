from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from prepare_markdown_sources import (
    FigureBlock,
    build_figure_blocks,
    extract_figures,
    load_markdown_sources,
    validate_relative_image_resources,
)


class PrepareMarkdownSourcesTests(unittest.TestCase):
    def test_load_markdown_sources_accepts_source_relative_image_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "manuscript" / "text" / "figures.md"
            image_path = root / "manuscript" / "figures" / "fig1.png"

            source_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(b"fixture")
            source_path.write_text(
                "![Figure](../figures/fig1.png){#fig-1 width=90%}\n",
                encoding="utf-8",
            )

            merged = load_markdown_sources([str(source_path)])

            self.assertIn(image_path.resolve().as_posix(), merged)
            self.assertNotIn("../figures/fig1.png", merged)

    def test_load_markdown_sources_rewrites_colliding_relative_image_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_a = root / "a" / "text" / "figures.md"
            source_b = root / "b" / "text" / "figures.md"
            image_a = root / "a" / "figures" / "shared.png"
            image_b = root / "b" / "figures" / "shared.png"

            for path in (source_a, source_b, image_a, image_b):
                path.parent.mkdir(parents=True, exist_ok=True)
            image_a.write_bytes(b"first")
            image_b.write_bytes(b"second")
            source_a.write_text(
                "![First](../figures/shared.png){#fig-first}\n",
                encoding="utf-8",
            )
            source_b.write_text(
                "![Second](../figures/shared.png){#fig-second}\n",
                encoding="utf-8",
            )

            merged = load_markdown_sources([str(source_a), str(source_b)])

            self.assertIn(image_a.resolve().as_posix(), merged)
            self.assertIn(image_b.resolve().as_posix(), merged)
            self.assertEqual(merged.count("../figures/shared.png"), 0)

    def test_missing_relative_image_reports_resolved_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "manuscript" / "text" / "figures.md"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text(
                "![Figure](../figures/missing.png){#fig-1 width=90%}\n",
                encoding="utf-8",
            )

            expected_resolved = (source_path.parent / "../figures/missing.png").resolve()
            with self.assertRaisesRegex(ValueError, str(expected_resolved)):
                validate_relative_image_resources(source_path)

    def test_inline_code_image_example_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "manuscript" / "text" / "notes.md"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text(
                "Use `![Example](../figures/missing.png)` in docs.\n",
                encoding="utf-8",
            )

            validate_relative_image_resources(source_path)

    def test_tilde_fenced_figure_example_is_not_extracted(self) -> None:
        lines = [
            "# Demo",
            "",
            "~~~markdown",
            "![Example](../figures/example.png){#fig-example}",
            "~~~",
            "",
            "Body",
        ]

        remaining, figures = extract_figures(lines)

        self.assertEqual(figures, [])
        self.assertEqual(remaining, lines)

    def test_uppercase_supplementary_id_orders_without_crashing(self) -> None:
        figure = FigureBlock(
            raw="![Supplement](fig.png){#fig-main-S1}",
            figure_id="fig-main-S1",
            title="Supplement",
            src="fig.png",
            attrs="#fig-main-S1",
        )

        content = build_figure_blocks([figure], "top", "pages")

        self.assertIn("**Fig. S1.**", content)


if __name__ == "__main__":
    unittest.main()
