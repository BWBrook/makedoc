from __future__ import annotations

import contextlib
import io
import json
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

    def _preflight_source(self):
        preflight = getattr(importer, "preflight_markdown_source", None)
        self.assertIsNotNone(preflight, "preflight_markdown_source should exist")
        return preflight

    def _format_preflight_report(self):
        formatter = getattr(importer, "format_preflight_report", None)
        self.assertIsNotNone(formatter, "format_preflight_report should exist")
        return formatter

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

    def test_revised_candidate_handles_synthetic_manuscript_like_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "synthetic_source.md"
            revised_docx = tmp_path / "synthetic_revised.docx"
            output_path = tmp_path / "synthetic_candidate.md"
            original_path.write_text(
                (
                    "Survival increased during the cool season when rainfall "
                    "remained stable.\n\n"
                    "We measured habitat condition using field surveys and remote "
                    "checks across sites.\n\n"
                    "These results suggest a cautious management response for "
                    "drought-sensitive populations.\n"
                ),
                encoding="utf-8",
            )
            _write_docx(
                revised_docx,
                (
                    "<w:p><w:r><w:t>Survival increased during the cool season "
                    "when rainfall remained unusually stable.</w:t></w:r></w:p>"
                    "<w:p><w:r><w:t>We measured habitat condition using field "
                    "surveys across sites.</w:t></w:r></w:p>"
                    "<w:p><w:r><w:t>These results suggest a targeted management "
                    "response for drought-sensitive populations.</w:t></w:r></w:p>"
                ),
            )

            candidate = self._candidate_generator()(
                original_path,
                revised_docx,
                output_path,
            )

            expected = (
                "Survival increased during the cool season when rainfall remained "
                "{++ unusually ++} stable.\n\n"
                "We measured habitat condition using field surveys "
                "{-- and remote checks --} across sites.\n\n"
                "These results suggest a {~~ cautious ~> targeted ~~} management "
                "response for drought-sensitive populations.\n"
            )
            self.assertEqual(candidate, expected)
            self.assertEqual(output_path.read_text(encoding="utf-8"), expected)

    def test_revised_candidate_cli_positive_dry_run_writes_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "synthetic_source.md"
            revised_docx = tmp_path / "synthetic_revised.docx"
            output_path = tmp_path / "synthetic_candidate.md"
            original_path.write_text(
                "The baseline model retained signal.\n\nThe field check was cautious.\n",
                encoding="utf-8",
            )
            _write_docx(
                revised_docx,
                (
                    "<w:p><w:r><w:t>The baseline model retained stronger signal."
                    "</w:t></w:r></w:p>"
                    "<w:p><w:r><w:t>The field check was targeted.</w:t></w:r></w:p>"
                ),
            )

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

            self.assertEqual(status, 0)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                (
                    "The baseline model retained {++ stronger ++} signal.\n\n"
                    "The field check was {~~ cautious. ~> targeted. ~~}\n"
                ),
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

    def test_revised_candidate_refuses_front_matter_or_thematic_break(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_path = tmp_path / "original.md"
            revised_docx = tmp_path / "revised.docx"
            output_path = tmp_path / "candidate.md"
            original_path.write_text(
                "---\ntitle: Secret title\n---\n\nPlain prose.\n",
                encoding="utf-8",
            )
            _write_docx(revised_docx, "<w:p><w:r><w:t>Plain revised prose.</w:t></w:r></w:p>")

            with self.assertRaisesRegex(
                self._candidate_error(),
                "front matter or thematic break",
            ):
                self._candidate_generator()(original_path, revised_docx, output_path)

            self.assertFalse(output_path.exists())

    def test_revised_candidate_refuses_pandoc_citations(self) -> None:
        citation_sources = {
            "bracketed": "Prior work reported this pattern [@smith2020].\n",
            "suppressed": "Prior work reported this pattern [-@smith2020].\n",
            "narrative": "Prior work by @smith2020 reported this pattern.\n",
        }
        for label, source in citation_sources.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = Path(tmp)
                    original_path = tmp_path / "original.md"
                    revised_docx = tmp_path / "revised.docx"
                    output_path = tmp_path / "candidate.md"
                    original_path.write_text(source, encoding="utf-8")
                    _write_docx(
                        revised_docx,
                        "<w:p><w:r><w:t>Prior work reported this pattern.</w:t></w:r></w:p>",
                    )

                    with self.assertRaisesRegex(self._candidate_error(), "Pandoc citation"):
                        self._candidate_generator()(original_path, revised_docx, output_path)

                    self.assertFalse(output_path.exists())

    def test_revised_candidate_refuses_heading_and_list_structures(self) -> None:
        unsupported_sources = {
            "heading": "# Abstract\n\nSimple prose follows.\n",
            "bullet": "- first result\n- second result\n",
            "numbered": "1. first result\n2. second result\n",
        }
        for label, source in unsupported_sources.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = Path(tmp)
                    original_path = tmp_path / "original.md"
                    revised_docx = tmp_path / "revised.docx"
                    output_path = tmp_path / "candidate.md"
                    original_path.write_text(source, encoding="utf-8")
                    _write_docx(
                        revised_docx,
                        "<w:p><w:r><w:t>Simple prose follows.</w:t></w:r></w:p>",
                    )

                    with self.assertRaisesRegex(
                        self._candidate_error(),
                        "heading|list",
                    ):
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

    def test_preflight_reports_all_simple_prose_as_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = Path(tmp) / "original.md"
            original_path.write_text(
                "The first paragraph is simple prose.\n\n"
                "The second paragraph also stays simple.\n",
                encoding="utf-8",
            )

            report = self._preflight_source()(original_path)
            rendered = self._format_preflight_report()(report)

            self.assertEqual(report["total_blocks"], 2)
            self.assertEqual(report["eligible_blocks"], 2)
            self.assertEqual(report["refused_blocks"], 0)
            self.assertTrue(report["safe_to_attempt"])
            self.assertEqual(report["refusals"], [])
            self.assertEqual(
                report["eligible_blocks_detail"],
                [
                    {"block": 1, "start_line": 1, "end_line": 1},
                    {"block": 2, "start_line": 3, "end_line": 3},
                ],
            )
            self.assertIn("Overall status: SAFE_TO_ATTEMPT", rendered)
            self.assertIn("Eligible simple-prose paragraphs: 2", rendered)
            self.assertIn("Refused blocks: 0", rendered)
            self.assertEqual(report["status"], "SAFE_TO_ATTEMPT")

    def test_preflight_reports_mixed_refusals_without_source_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = Path(tmp) / "original.md"
            original_path.write_text(
                "# Confidential heading text\n\n"
                "UNIQUE_PROSE_SHOULD_NOT_APPEAR in a simple paragraph.\n\n"
                "Prior work by @smith2020 reported the pattern.\n\n"
                "- bullet item with private wording\n\n"
                "1. numbered item with private wording\n\n"
                "Column A | Column B\n--- | ---\nvalue | other\n\n"
                "![Private caption](figure.png)\n\n"
                "Existing {++ private addition ++} token.\n",
                encoding="utf-8",
            )

            report = self._preflight_source()(original_path)
            rendered = self._format_preflight_report()(report)
            reasons = [refusal["reason"] for refusal in report["refusals"]]

            self.assertEqual(report["total_blocks"], 8)
            self.assertEqual(report["eligible_blocks"], 1)
            self.assertEqual(report["refused_blocks"], 7)
            self.assertFalse(report["safe_to_attempt"])
            self.assertEqual(report["status"], "REFUSED")
            self.assertEqual(
                report["eligible_blocks_detail"],
                [{"block": 2, "start_line": 3, "end_line": 3}],
            )
            self.assertIn("unsupported Markdown heading", reasons)
            self.assertIn("unsupported Markdown Pandoc citation", reasons)
            self.assertIn("unsupported Markdown bullet list", reasons)
            self.assertIn("unsupported Markdown numbered list", reasons)
            self.assertIn("unsupported Markdown table", reasons)
            self.assertIn("unsupported Markdown image or figure line", reasons)
            self.assertIn("unsupported existing review-markup token", reasons)
            self.assertIn("Overall status: REFUSED", rendered)
            self.assertIn("block 1", rendered)
            self.assertIn("line 1", rendered)
            self.assertNotIn("UNIQUE_PROSE_SHOULD_NOT_APPEAR", rendered)
            self.assertNotIn("Confidential heading text", rendered)
            self.assertNotIn("Private caption", rendered)

    def test_preflight_reports_front_matter_without_source_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = Path(tmp) / "original.md"
            original_path.write_text(
                "---\ntitle: Secret title\n---\n\nPlain prose.\n",
                encoding="utf-8",
            )

            report = self._preflight_source()(original_path)
            rendered = self._format_preflight_report()(report)
            reasons = [refusal["reason"] for refusal in report["refusals"]]

            self.assertEqual(report["total_blocks"], 2)
            self.assertEqual(report["eligible_blocks"], 1)
            self.assertEqual(report["refused_blocks"], 1)
            self.assertFalse(report["safe_to_attempt"])
            self.assertEqual(report["status"], "REFUSED")
            self.assertIn(
                "unsupported Markdown front matter or thematic break",
                reasons,
            )
            self.assertIn("Overall status: REFUSED", rendered)
            self.assertIn("line 1", rendered)
            self.assertNotIn("Secret title", rendered)
            self.assertNotIn("Plain prose", rendered)

    def test_preflight_cli_returns_zero_even_with_refusals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = Path(tmp) / "original.md"
            original_path.write_text(
                "# Heading with private words\n\nPlain prose remains.\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = importer.main(
                    [
                        "preflight",
                        "--original-path",
                        str(original_path),
                    ]
                )

            rendered = stdout.getvalue()
            self.assertEqual(status, 0)
            self.assertIn("Overall status: REFUSED", rendered)
            self.assertIn("unsupported Markdown heading", rendered)
            self.assertNotIn("Heading with private words", rendered)
            self.assertNotIn("Plain prose remains", rendered)

    def test_preflight_cli_json_reports_safe_simple_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = Path(tmp) / "original.md"
            original_path.write_text(
                "UNIQUE_SAFE_PROSE_ONE.\n\nUNIQUE_SAFE_PROSE_TWO.\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = importer.main(
                    [
                        "preflight",
                        "--original-path",
                        str(original_path),
                        "--format",
                        "json",
                    ]
                )

            rendered = stdout.getvalue()
            payload = json.loads(rendered)
            self.assertEqual(status, 0)
            self.assertEqual(payload["status"], "SAFE_TO_ATTEMPT")
            self.assertEqual(payload["path"], str(original_path.resolve()))
            self.assertEqual(payload["total_blocks"], 2)
            self.assertEqual(payload["eligible_blocks"], 2)
            self.assertEqual(payload["refused_blocks"], 0)
            self.assertTrue(payload["safe_to_attempt"])
            self.assertEqual(payload["refusals"], [])
            self.assertEqual(
                payload["eligible_blocks_detail"],
                [
                    {"block": 1, "start_line": 1, "end_line": 1},
                    {"block": 2, "start_line": 3, "end_line": 3},
                ],
            )
            self.assertNotIn("UNIQUE_SAFE_PROSE_ONE", rendered)
            self.assertNotIn("UNIQUE_SAFE_PROSE_TWO", rendered)

    def test_preflight_cli_json_reports_refusals_without_source_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = Path(tmp) / "original.md"
            original_path.write_text(
                "# Secret Heading\n\n"
                "UNIQUE_REFUSED_PROSE should stay out of JSON.\n\n"
                "Prior work by @smith2020 reported the pattern.\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = importer.main(
                    [
                        "preflight",
                        "--original-path",
                        str(original_path),
                        "--format",
                        "json",
                    ]
                )

            rendered = stdout.getvalue()
            payload = json.loads(rendered)
            reasons = [refusal["reason"] for refusal in payload["refusals"]]
            self.assertEqual(status, 0)
            self.assertEqual(payload["status"], "REFUSED")
            self.assertEqual(payload["total_blocks"], 3)
            self.assertEqual(payload["eligible_blocks"], 1)
            self.assertEqual(payload["refused_blocks"], 2)
            self.assertFalse(payload["safe_to_attempt"])
            self.assertEqual(
                payload["eligible_blocks_detail"],
                [{"block": 2, "start_line": 3, "end_line": 3}],
            )
            self.assertIn("unsupported Markdown heading", reasons)
            self.assertIn("unsupported Markdown Pandoc citation", reasons)
            self.assertEqual(payload["refusals"][0]["block"], 1)
            self.assertEqual(payload["refusals"][0]["line"], 1)
            self.assertNotIn("Secret Heading", rendered)
            self.assertNotIn("UNIQUE_REFUSED_PROSE", rendered)
            self.assertNotIn("smith2020", rendered)

    def test_preflight_cli_json_reports_front_matter_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = Path(tmp) / "original.md"
            original_path.write_text(
                "---\ntitle: Secret title\n---\n\nPlain prose.\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = importer.main(
                    [
                        "preflight",
                        "--original-path",
                        str(original_path),
                        "--format",
                        "json",
                    ]
                )

            rendered = stdout.getvalue()
            payload = json.loads(rendered)
            self.assertEqual(status, 0)
            self.assertEqual(payload["status"], "REFUSED")
            self.assertEqual(payload["refused_blocks"], 1)
            self.assertEqual(
                payload["eligible_blocks_detail"],
                [{"block": 2, "start_line": 5, "end_line": 5}],
            )
            self.assertEqual(
                payload["refusals"][0]["reason"],
                "unsupported Markdown front matter or thematic break",
            )
            self.assertEqual(payload["refusals"][0]["line"], 1)
            self.assertNotIn("Secret title", rendered)
            self.assertNotIn("Plain prose", rendered)

    def test_preflight_cli_rejects_invalid_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = Path(tmp) / "original.md"
            original_path.write_text("Plain prose.\n", encoding="utf-8")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    importer.main(
                        [
                            "preflight",
                            "--original-path",
                            str(original_path),
                            "--format",
                            "yaml",
                        ]
                    )

            self.assertEqual(raised.exception.code, 2)
            self.assertIn("invalid choice", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
