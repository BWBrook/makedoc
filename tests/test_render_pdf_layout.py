from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from render_pdf_layout import build_block


class RenderPdfLayoutTests(unittest.TestCase):
    def test_build_block_redefines_lower_level_headings_as_block_style(self) -> None:
        profile = SimpleNamespace(
            page_numbers="none",
            line_spacing="single",
            line_numbering="none",
        )

        lines = build_block(profile)
        content = "\n".join(lines)

        self.assertIn("\\usepackage{needspace}", lines)
        self.assertIn("\\renewcommand\\paragraph{\\@startsection{paragraph}{4}{\\z@}", content)
        self.assertIn("\\renewcommand\\subparagraph{\\@startsection{subparagraph}{5}{\\z@}", content)


if __name__ == "__main__":
    unittest.main()
