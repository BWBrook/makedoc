from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lint_manuscript import lint_source
from refs_audit import scan_citations


class MarkdownScanningTests(unittest.TestCase):
    def write_source(self, content: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "source.md"
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        return path

    def test_lint_ignores_placeholders_and_manual_cites_inside_fenced_blocks(self) -> None:
        source = self.write_source(
            """
            # Demo

            ```python
            placeholder = "[REF]"
            example = "(Smith 2020)"
            ```

            ```{=openxml}
            <w:t>@literalCodeExample</w:t>
            ```
            """
        )

        errors = lint_source(source)

        self.assertEqual(errors, [])

    def test_reference_audit_ignores_citations_inside_fences_and_inline_code(self) -> None:
        source = self.write_source(
            """
            # Demo

            Use `[@literalExample2026]` syntax in documentation.

            Narrative cite: @realKey2026.

            ~~~markdown
            [@fencedOut2026]
            ~~~
            """
        )

        hits = scan_citations(source)

        self.assertEqual([(hit.key, hit.line) for hit in hits], [("realKey2026", 5)])

    def test_lint_accepts_escaped_pipe_table_cells(self) -> None:
        source = self.write_source(
            r"""
            # Demo

            | Column A | Column B |
            | --- | --- |
            | alpha \| beta | value |
            | gamma | another value |
            """
        )

        errors = lint_source(source)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
