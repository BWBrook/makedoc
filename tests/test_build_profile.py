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

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertEqual(profile.output_dir, "dist/demo-paper")
            self.assertEqual(profile.pdf_out, "dist/demo-paper/manuscript.pdf")
            self.assertEqual(profile.docx_out, "dist/demo-paper/manuscript.docx")

    def test_inferred_dist_subdir_is_safe_for_make_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "demo paper (probe)"
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

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertEqual(profile.output_dir, "dist/demo-paper-probe")

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

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertEqual(profile.output_dir, "dist/paper-engine")

    def test_explicit_dist_subdir_output_dir_is_preserved(self) -> None:
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

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertEqual(profile.output_dir, "dist/custom-output")
            self.assertEqual(profile.pdf_out, "dist/custom-output/manuscript.pdf")
            self.assertEqual(profile.docx_out, "dist/custom-output/manuscript.docx")

    def test_explicit_non_dist_output_dir_resolves_relative_to_config_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "manuscript" / "text" / "main.md"
            bibliography_path = root / "references.yaml"
            csl_path = root / "journal.csl"
            config_path = root / "settings" / "build.yaml"

            source_path.parent.mkdir(parents=True)
            source_path.write_text("# Demo\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")
            config_path.parent.mkdir(parents=True)
            self.write_config(
                config_path=config_path,
                source_path=source_path,
                bibliography_path=bibliography_path,
                csl_path=csl_path,
                output_dir="../../build",
            )

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            expected_output = str((config_path.parent / "../../build").resolve())
            self.assertEqual(profile.output_dir, expected_output)
            self.assertEqual(profile.pdf_out, str(Path(expected_output) / "manuscript.pdf"))
            self.assertEqual(profile.docx_out, str(Path(expected_output) / "manuscript.docx"))


class ResolveProfileRelativePathTests(unittest.TestCase):
    def test_profile_paths_resolve_relative_to_config_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "settings" / "build.yaml"
            main_path = root / "manuscript" / "text" / "main.md"
            figures_path = root / "manuscript" / "text" / "figures.md"
            authors_path = root / "manuscript" / "authors.yaml"
            bibliography_path = root / "references" / "refs.yaml"
            csl_path = root / "csl" / "journal.csl"
            contract_path = root / "expected" / "golden.yaml"
            edgecase_path = root / "edgecases" / "unknown.md"

            for path in (main_path, figures_path, authors_path, bibliography_path, csl_path, contract_path, edgecase_path):
                path.parent.mkdir(parents=True, exist_ok=True)
            main_path.write_text("# Main\n", encoding="utf-8")
            figures_path.write_text("![Fig](../figures/figure.png){#fig-1}\n", encoding="utf-8")
            authors_path.write_text("authors: []\naffiliations: {}\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")
            contract_path.write_text("required_text: []\nexpect_tables: 0\nexpect_drawings: 0\nmin_pdf_pages: 0\n", encoding="utf-8")
            edgecase_path.write_text("# Edge\n", encoding="utf-8")

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                textwrap.dedent(
                    """
                    default_profile: sample

                    profiles:
                      sample:
                        manuscript_sources:
                          - ../manuscript/text/main.md
                          - ../manuscript/text/figures.md
                        lint_sources:
                          - ../manuscript/text/main.md
                        author_metadata: ../manuscript/authors.yaml
                        bibliography: ../references/refs.yaml
                        csl: ../csl/journal.csl
                        golden_contract: ../expected/golden.yaml
                        csl_search_dirs:
                          - ../csl
                        edgecases:
                          unknown_cite: ../edgecases/unknown.md
                        output_dir: dist
                        output_stem: manuscript
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertEqual(profile.manuscript_sources, [str(main_path.resolve()), str(figures_path.resolve())])
            self.assertEqual(profile.lint_sources, [str(main_path.resolve())])
            self.assertEqual(profile.author_metadata, str(authors_path.resolve()))
            self.assertEqual(profile.bibliography, str(bibliography_path.resolve()))
            self.assertEqual(profile.csl, str(csl_path.resolve()))
            self.assertEqual(profile.golden_contract, str(contract_path.resolve()))
            self.assertEqual(profile.edgecase_unknown_cite, str(edgecase_path.resolve()))
            self.assertEqual(profile.csl_search_dirs, [str(csl_path.parent.resolve())])

    def test_default_csl_search_dirs_use_resolved_csl_parent_and_config_csl_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "settings" / "build.yaml"
            source_path = root / "manuscript" / "text" / "main.md"
            bibliography_path = root / "references" / "refs.yaml"
            csl_path = root / "styles" / "journal.csl"
            config_csl_dir = root / "settings" / "csl"

            source_path.parent.mkdir(parents=True, exist_ok=True)
            bibliography_path.parent.mkdir(parents=True, exist_ok=True)
            csl_path.parent.mkdir(parents=True, exist_ok=True)
            config_csl_dir.mkdir(parents=True, exist_ok=True)

            source_path.write_text("# Demo\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")
            (config_csl_dir / "backup.csl").write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                textwrap.dedent(
                    """
                    default_profile: sample

                    profiles:
                      sample:
                        manuscript_sources:
                          - ../manuscript/text/main.md
                        bibliography: ../references/refs.yaml
                        csl: ../styles/journal.csl
                        output_dir: dist
                        output_stem: manuscript
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertEqual(
                profile.csl_search_dirs,
                [str(csl_path.parent.resolve()), str(config_csl_dir.resolve())],
            )

    def test_resource_paths_use_unique_source_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "settings" / "build.yaml"
            main_path = root / "manuscript" / "text" / "main.md"
            figures_path = root / "appendix" / "text" / "figures.md"
            bibliography_path = root / "references" / "refs.yaml"
            csl_path = root / "csl" / "journal.csl"

            for path in (main_path, figures_path, bibliography_path, csl_path):
                path.parent.mkdir(parents=True, exist_ok=True)
            main_path.write_text("# Main\n", encoding="utf-8")
            figures_path.write_text("# Figures\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                textwrap.dedent(
                    """
                    default_profile: sample

                    profiles:
                      sample:
                        manuscript_sources:
                          - ../manuscript/text/main.md
                          - ../appendix/text/figures.md
                        bibliography: ../references/refs.yaml
                        csl: ../csl/journal.csl
                        output_dir: dist
                        output_stem: manuscript
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertEqual(
                profile.resource_paths,
                [str(main_path.parent.resolve()), str(figures_path.parent.resolve())],
            )

    def test_review_markup_defaults_to_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "settings" / "build.yaml"
            source_path = root / "manuscript" / "text" / "main.md"
            bibliography_path = root / "references" / "refs.yaml"
            csl_path = root / "csl" / "journal.csl"

            for path in (source_path, bibliography_path, csl_path):
                path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("# Demo\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                textwrap.dedent(
                    """
                    default_profile: sample

                    profiles:
                      sample:
                        manuscript_sources:
                          - ../manuscript/text/main.md
                        bibliography: ../references/refs.yaml
                        csl: ../csl/journal.csl
                        output_dir: dist
                        output_stem: manuscript
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertFalse(profile.review_markup.enabled)
            self.assertEqual(profile.to_dict()["review_markup"], {"enabled": False})

    def test_review_markup_can_be_enabled_with_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "settings" / "build.yaml"
            source_path = root / "manuscript" / "text" / "main.md"
            bibliography_path = root / "references" / "refs.yaml"
            csl_path = root / "csl" / "journal.csl"

            for path in (source_path, bibliography_path, csl_path):
                path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("# Demo\n", encoding="utf-8")
            bibliography_path.write_text("references: []\n", encoding="utf-8")
            csl_path.write_text("<style xmlns='http://purl.org/net/xbiblio/csl' />\n", encoding="utf-8")

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                textwrap.dedent(
                    """
                    default_profile: sample

                    profiles:
                      sample:
                        manuscript_sources:
                          - ../manuscript/text/main.md
                        bibliography: ../references/refs.yaml
                        csl: ../csl/journal.csl
                        output_dir: dist
                        output_stem: manuscript
                        review_markup:
                          enabled: true
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            profile = resolve_profile(load_config(config_path), "sample", config_path=config_path)

            self.assertTrue(profile.review_markup.enabled)


if __name__ == "__main__":
    unittest.main()
