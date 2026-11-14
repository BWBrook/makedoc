"""Record what a build used and produced."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .profile import Profile


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
    }


def _first_line(command: list[str], cwd: Path | None = None) -> str:
    try:
        proc = subprocess.run(command, check=False, capture_output=True, text=True, cwd=cwd)
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    lines = (proc.stdout or proc.stderr).splitlines()
    return lines[0].strip() if lines else ""


def manifest_path(profile: Profile) -> Path:
    return Path(profile.output_dir) / f"{profile.output_stem}_build_manifest.json"


def write_manifest(
    profile: Profile, config_path: Path, outputs: list[Path], warnings: list[str], images: list[Path]
) -> Path:
    repo = config_path.resolve().parent
    inputs = [config_path.resolve(), *(Path(item) for item in profile.manuscript_sources)]
    inputs.extend(images)
    for optional in (profile.author_metadata, profile.bibliography, profile.csl):
        if optional:
            inputs.append(Path(optional))

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "makedoc_version": __version__,
        "manuscript_git": {
            "sha": _first_line(["git", "rev-parse", "HEAD"], cwd=repo),
            "dirty": bool(_first_line(["git", "status", "--porcelain"], cwd=repo)),
        },
        "tool_versions": {
            "pandoc": _first_line(["pandoc", "--version"]),
            "xelatex": _first_line(["xelatex", "--version"]),
            "python": sys.version.split()[0],
        },
        "profile": profile.to_dict(),
        "inputs": [file_record(path) for path in inputs],
        "outputs": [file_record(path) for path in outputs],
        "warnings": warnings,
    }
    target = manifest_path(profile)
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return target
