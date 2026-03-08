#!/usr/bin/env python3
"""Generate reproducibility metadata manifest for manuscript builds."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_profile import load_config, resolve_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="settings/build.yaml", help="Path to build config YAML.")
    parser.add_argument("--profile", required=True, help="Profile name used for the build.")
    parser.add_argument("--output", required=True, help="Manifest output path.")
    parser.add_argument("--pdf", required=True, help="Expected PDF output path.")
    parser.add_argument("--docx", required=True, help="Expected DOCX output path.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    exists = path.exists()
    record: dict[str, Any] = {
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
    }
    return record


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def command_version(cmd: str, args: list[str]) -> str:
    proc = subprocess.run([cmd, *args], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    line = (proc.stdout or proc.stderr).splitlines()
    return line[0].strip() if line else ""


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    output_path = Path(args.output)
    pdf_path = Path(args.pdf)
    docx_path = Path(args.docx)

    try:
        config = load_config(config_path)
        profile = resolve_profile(config, args.profile, config_path=config_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for artifact in (pdf_path, docx_path):
        if not artifact.exists():
            print(f"Error: expected build artifact missing: {artifact}", file=sys.stderr)
            return 1

    input_paths: list[Path] = [Path(item) for item in profile.manuscript_sources]
    input_paths.extend([Path(profile.bibliography), Path(profile.csl)])
    if profile.golden_contract:
        input_paths.append(Path(profile.golden_contract))

    manifest: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": {
            "sha": run_git(["rev-parse", "HEAD"]),
            "branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]),
            "dirty": bool(run_git(["status", "--porcelain"])),
        },
        "profile": profile.to_dict(),
        "config_path": str(config_path),
        "tool_versions": {
            "pandoc": command_version("pandoc", ["--version"]),
            "xelatex": command_version("xelatex", ["--version"]),
            "python": sys.version.splitlines()[0],
            "make": command_version("make", ["--version"]),
        },
        "inputs": [file_record(path) for path in input_paths],
        "outputs": [file_record(pdf_path), file_record(docx_path)],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"Wrote build manifest: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
