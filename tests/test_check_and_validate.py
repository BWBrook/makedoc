from __future__ import annotations

from pathlib import Path

import pytest

from makedoc.cli import main
from makedoc.validate import validate_config
from support import FIXTURE_CSL, FIXTURE_REFS, TESTBED, TESTBED_CONFIG, write_config

EDGECASES = TESTBED / "edgecases"


def test_fixture_profiles_pass_check() -> None:
    assert main(["check", "-c", str(TESTBED_CONFIG), "--all"]) == 0


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("unknown_cite_main.md", ":3: citation key 'unknownEdgeKey2026' is not in the bibliography"),
        ("manual_cite_main.md", ":3: Possible manual author-year citation"),
        ("malformed_table_main.md", ":8: Malformed markdown table row"),
    ],
)
def test_check_fails_on_edge_case(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], source: str, expected: str
) -> None:
    path = EDGECASES / source
    config = write_config(tmp_path / "build.yaml", {"edge": {
        "manuscript_sources": [str(path)],
        "bibliography": str(FIXTURE_REFS),
        "csl": str(FIXTURE_CSL),
        "output_dir": "out",
        "output_stem": "edge",
    }})

    assert main(["check", "-c", str(config)]) == 1
    assert f"{path}{expected}" in capsys.readouterr().err


@pytest.mark.parametrize("key", ["golden_contract", "edgecases"])
def test_validate_reports_removed_v1_keys(tmp_path: Path, key: str) -> None:
    source = tmp_path / "main.md"
    source.write_text("# Main\n", encoding="utf-8")
    config = write_config(tmp_path / "build.yaml", {"old": {
        "manuscript_sources": [str(source)],
        "bibliography": str(FIXTURE_REFS),
        "output_dir": "out",
        "output_stem": "old",
        key: "anything",
    }})

    problems = validate_config(config, ["old"])

    matching = [problem for problem in problems if f"'{key}'" in problem]
    assert len(matching) == 1
    assert "removed" in matching[0]
    assert "MIGRATING.md" in matching[0]
