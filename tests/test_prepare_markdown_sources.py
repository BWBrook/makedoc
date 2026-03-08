from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from prepare_markdown_sources import load_markdown_sources, validate_relative_image_resources


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

            self.assertIn("../figures/fig1.png", merged)

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


if __name__ == "__main__":
    unittest.main()
