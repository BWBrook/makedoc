from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_profile import load_config, resolve_profile


class ResolveProfileOutputDirTests(unittest.TestCase):
    def write_config(
        self,
        *,
        config_path: Path,
        source_path: Path,
        bibliography_path: Path,
        csl_path: Path,
        output_dir: str = "dist",
    ) -> None:
        config_path.write_text(
            textwrap.dedent(
                f"""
                default_profile: sample

                profiles:
                  sample:
                    manuscript_sources:
                      - {source_path}
                    lint_sources:
                      - {source_path}
                    bibliography: {bibliography_path}
                    csl: {csl_path}
                    output_dir: {output_dir}
                    output_stem: manuscript
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def test_output_dir_prefers_manuscript_container_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "demo-paper"
            source_path = project_dir / "manuscript" / "text" / "main.md"
            bibliography_path = project_dir / "references.yaml"
            csl_path = project_dir / "journal.csl"
            config_path = root / "build.yaml"

            source_path.parent.mkdir(parents=True)
            source_path.write_text("# Demo\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")
            self.write_config(
                config_path=config_path,
                source_path=source_path,
                bibliography_path=bibliography_path,
                csl_path=csl_path,
            )

            profile = resolve_profile(load_config(config_path), "sample")

            self.assertEqual(profile.output_dir, "dist/demo-paper")
            self.assertEqual(profile.pdf_out, "dist/demo-paper/manuscript.pdf")
            self.assertEqual(profile.docx_out, "dist/demo-paper/manuscript.docx")

    def test_output_dir_falls_back_to_repo_name_when_no_manuscript_dir_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_dir = root / "paper-engine"
            source_path = repo_dir / "text" / "main.md"
            bibliography_path = repo_dir / "references.yaml"
            csl_path = repo_dir / "journal.csl"
            config_path = root / "build.yaml"

            (repo_dir / ".git").mkdir(parents=True)
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# Demo\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")
            self.write_config(
                config_path=config_path,
                source_path=source_path,
                bibliography_path=bibliography_path,
                csl_path=csl_path,
            )

            profile = resolve_profile(load_config(config_path), "sample")

            self.assertEqual(profile.output_dir, "dist/paper-engine")

    def test_explicit_non_dist_output_dir_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "manuscript" / "text" / "main.md"
            bibliography_path = root / "references.yaml"
            csl_path = root / "journal.csl"
            config_path = root / "build.yaml"

            source_path.parent.mkdir(parents=True)
            source_path.write_text("# Demo\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")
            self.write_config(
                config_path=config_path,
                source_path=source_path,
                bibliography_path=bibliography_path,
                csl_path=csl_path,
                output_dir="dist/custom-output",
            )

            profile = resolve_profile(load_config(config_path), "sample")

            self.assertEqual(profile.output_dir, "dist/custom-output")


if __name__ == "__main__":
    unittest.main()
