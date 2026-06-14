from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from import_docx_review_markup import (  # noqa: E402
    extract_revised_text_from_docx,
    revised_docx_to_review_markup,
    track_changes_docx_to_review_markup,
)


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _write_docx(path: Path, body_xml: str) -> None:
    document_xml = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{WORD_NS}"><w:body>{body_xml}</w:body></w:document>'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)


class ImportDocxReviewMarkupTests(unittest.TestCase):
    def test_revised_docx_route_marks_insert_delete_and_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "revised.docx"
            _write_docx(
                docx_path,
                (
                    "<w:p>"
                    "<w:r><w:t>alpha inserted beta gamma new</w:t></w:r>"
                    "</w:p>"
                ),
            )

            rendered = revised_docx_to_review_markup(
                "alpha beta remove gamma old",
                docx_path,
            )

            self.assertEqual(
                rendered,
                "alpha {++ inserted ++} beta {-- remove --} gamma {~~ old ~> new ~~}",
            )

    def test_revised_text_extraction_ignores_native_deleted_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "tracked.docx"
            _write_docx(
                docx_path,
                (
                    "<w:p>"
                    "<w:r><w:t>keep </w:t></w:r>"
                    "<w:del><w:r><w:delText>old</w:delText></w:r></w:del>"
                    "<w:ins><w:r><w:t>new</w:t></w:r></w:ins>"
                    "</w:p>"
                ),
            )

            self.assertEqual(extract_revised_text_from_docx(docx_path), "keep new")

    def test_track_changes_route_reads_insertions_and_deletions_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "tracked.docx"
            _write_docx(
                docx_path,
                (
                    "<w:p>"
                    "<w:r><w:t>alpha </w:t></w:r>"
                    "<w:ins><w:r><w:t>inserted</w:t></w:r></w:ins>"
                    "<w:r><w:t> beta </w:t></w:r>"
                    "<w:del><w:r><w:delText>removed</w:delText></w:r></w:del>"
                    "<w:r><w:t> gamma</w:t></w:r>"
                    "</w:p>"
                ),
            )

            self.assertEqual(
                track_changes_docx_to_review_markup(docx_path),
                "alpha {++ inserted ++} beta {-- removed --} gamma",
            )


if __name__ == "__main__":
    unittest.main()
