from __future__ import annotations

import sys
import unittest
from pathlib import Path


from makedoc.validate import validate_schema


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

    def test_unknown_review_markup_keys_are_reported(self) -> None:
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
                        "review_markup": {
                            "enabled": True,
                            "colour": "red",
                        },
                    }
                },
            },
            errors,
        )

        self.assertIn("Profile 'sample' review_markup has unknown keys: colour", errors)


if __name__ == "__main__":
    unittest.main()
