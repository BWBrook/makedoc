from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import fixture_golden_check


class FixtureGoldenCheckTests(unittest.TestCase):
    def test_read_pdf_text_reports_missing_pdftotext(self) -> None:
        with mock.patch.object(fixture_golden_check, "run_cmd", side_effect=FileNotFoundError()):
            with self.assertRaisesRegex(RuntimeError, "pdftotext not found"):
                fixture_golden_check.read_pdf_text(Path("fixture.pdf"))

    def test_read_pdf_page_count_reports_missing_pdfinfo(self) -> None:
        with mock.patch.object(fixture_golden_check, "run_cmd", side_effect=FileNotFoundError()):
            with self.assertRaisesRegex(RuntimeError, "pdfinfo not found"):
                fixture_golden_check.read_pdf_page_count(Path("fixture.pdf"))

    def test_load_contract_rejects_non_mapping_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contract_path = Path(tmp) / "contract.yaml"
            contract_path.write_text("- unexpected\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "mapping root"):
                fixture_golden_check.load_contract(contract_path)


if __name__ == "__main__":
    unittest.main()
