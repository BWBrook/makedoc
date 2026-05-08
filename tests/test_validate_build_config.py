from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from validate_build_config import validate_schema


class ValidateBuildConfigTests(unittest.TestCase):
    def test_unknown_margin_keys_are_reported(self) -> None:
        errors: list[str] = []
        validate_schema(
            {
                "default_profile": "sample",
                "profiles": {
                    "sample": {
                        "manuscript_sources": ["manuscript.md"],
                        "bibliography": "refs.yaml",
                        "csl": "style.csl",
                        "output_dir": "dist",
                        "output_stem": "manuscript",
                        "margins": {
                            "unit": "cm",
                            "paper_size": "a4",
                            "right_typo": 99,
                        },
                    }
                },
            },
            errors,
        )

        self.assertIn("Profile 'sample' margins has unknown keys: right_typo", errors)


if __name__ == "__main__":
    unittest.main()
