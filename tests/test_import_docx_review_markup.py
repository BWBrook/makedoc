from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import import_docx_review_markup as importer  # noqa: E402
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
    def _candidate_generator(self):
        generator = getattr(importer, "generate_revised_candidate", None)
        self.assertIsNotNone(generator, "generate_revised_candidate should exist")
        return generator

    def _candidate_error(self) -> type[Exception]:
        return getattr(importer, "CandidateGenerationError", ValueError)

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

    def test_revised_candidate_writes_simple_paragraph_with_review_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            output_path = tmp_path / "candidate.md"
            original_path.write_text("alpha beta remove gamma old\n", encoding="utf-8")
            _write_docx(
                revised_docx,
                (
                    "<w:p>"
                    "<w:r><w:t>alpha inserted beta gamma new</w:t></w:r>"
                    "</w:p>"
                ),
            )

            candidate = self._candidate_generator()(
                original_path,
                revised_docx,
                output_path,
            )

            expected = (
                "alpha {++ inserted ++} beta {-- remove --} "
                "gamma {~~ old ~> new ~~}\n"
            )
            self.assertEqual(candidate, expected)
            self.assertEqual(output_path.read_text(encoding="utf-8"), expected)

    def test_revised_candidate_preserves_multiple_paragraph_breaks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            output_path = tmp_path / "candidate.md"
            original_path.write_text("first old\n\nsecond keep\n", encoding="utf-8")
            _write_docx(
                revised_docx,
                (
                    "<w:p><w:r><w:t>first new</w:t></w:r></w:p>"
                    "<w:p><w:r><w:t>second keep inserted</w:t></w:r></w:p>"
                ),
            )

            self._candidate_generator()(original_path, revised_docx, output_path)

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "first {~~ old ~> new ~~}\n\nsecond keep {++ inserted ++}\n",
            )

    def test_revised_candidate_refuses_paragraph_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            output_path = tmp_path / "candidate.md"
            original_path.write_text("first paragraph\n\nsecond paragraph\n", encoding="utf-8")
            _write_docx(
                revised_docx,
                "<w:p><w:r><w:t>first paragraph only</w:t></w:r></w:p>",
            )

            with self.assertRaisesRegex(self._candidate_error(), "paragraph count"):
                self._candidate_generator()(original_path, revised_docx, output_path)

            self.assertFalse(output_path.exists())

    def test_revised_candidate_refuses_figure_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            output_path = tmp_path / "candidate.md"
            original_path.write_text("![Caption](figure.png)\n", encoding="utf-8")
            _write_docx(revised_docx, "<w:p><w:r><w:t>Caption</w:t></w:r></w:p>")

            with self.assertRaisesRegex(self._candidate_error(), "image"):
                self._candidate_generator()(original_path, revised_docx, output_path)

            self.assertFalse(output_path.exists())

    def test_revised_candidate_refuses_markdown_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            output_path = tmp_path / "candidate.md"
            original_path.write_text(
                "Column A | Column B\n--- | ---\nvalue | other\n",
                encoding="utf-8",
            )
            _write_docx(revised_docx, "<w:p><w:r><w:t>table</w:t></w:r></w:p>")

            with self.assertRaisesRegex(self._candidate_error(), "table"):
                self._candidate_generator()(original_path, revised_docx, output_path)

            self.assertFalse(output_path.exists())

    def test_revised_candidate_refuses_output_equal_to_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            original_path.write_text("alpha beta\n", encoding="utf-8")
            _write_docx(revised_docx, "<w:p><w:r><w:t>alpha gamma</w:t></w:r></w:p>")

            with self.assertRaisesRegex(self._candidate_error(), "same path"):
                self._candidate_generator()(original_path, revised_docx, original_path)

            self.assertEqual(original_path.read_text(encoding="utf-8"), "alpha beta\n")

    def test_revised_candidate_refuses_overwrite_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            output_path = tmp_path / "candidate.md"
            original_path.write_text("alpha beta\n", encoding="utf-8")
            output_path.write_text("existing\n", encoding="utf-8")
            _write_docx(revised_docx, "<w:p><w:r><w:t>alpha gamma</w:t></w:r></w:p>")

            with self.assertRaisesRegex(self._candidate_error(), "already exists"):
                self._candidate_generator()(original_path, revised_docx, output_path)

            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing\n")

    def test_revised_candidate_cli_returns_nonzero_on_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            output_path = tmp_path / "candidate.md"
            original_path.write_text("# Heading\n\nalpha beta\n", encoding="utf-8")
            _write_docx(revised_docx, "<w:p><w:r><w:t>alpha gamma</w:t></w:r></w:p>")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = importer.main(
                    [
                        "revised-candidate",
                        "--original-path",
                        str(original_path),
                        "--revised-docx",
                        str(revised_docx),
                        "--output",
                        str(output_path),
                    ]
                )

            self.assertEqual(status, 2)
            self.assertIn("unsupported Markdown", stderr.getvalue())
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
