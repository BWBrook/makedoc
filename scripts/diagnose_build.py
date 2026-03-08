#!/usr/bin/env python3
"""Collect build diagnostics bundle for local or CI triage."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_profile import load_config, resolve_profile


LOG_PATTERNS = ["*.log", "*.blg", "*.out", "*.aux", "*.bcf", "*.run.xml"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="settings/build.yaml", help="Path to build config YAML.")
    parser.add_argument("--profile", default=None, help="Profile name for diagnostics context.")
    parser.add_argument(
        "--output-root",
        default="dist/diagnostics",
        help="Output directory root for diagnostics bundles.",
    )
    parser.add_argument("--manifest", help="Optional path to existing build manifest.")
    return parser.parse_args()


def run_cmd(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(args, check=False, capture_output=True, text=True)
    merged = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return proc.returncode, merged.strip()


def command_version(cmd: str, args: list[str]) -> str:
    code, output = run_cmd([cmd, *args])
    if code != 0:
        return ""
    return output.splitlines()[0].strip() if output else ""


def with_line_numbers(path: Path, max_lines: int = 200) -> str:
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for idx, raw in enumerate(handle, start=1):
            lines.append(f"{idx:5d}: {raw.rstrip()}")
            if idx >= max_lines:
                lines.append("... (truncated)")
                break
    return "\n".join(lines) + "\n"


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def gather_logs(bundle_dir: Path) -> list[str]:
    copied: list[str] = []
    search_roots = [Path("."), Path("dist")]
    logs_dir = bundle_dir / "logs"

    seen: set[Path] = set()
    for root in search_roots:
        if not root.exists():
            continue
        for pattern in LOG_PATTERNS:
            for candidate in root.rglob(pattern):
                if not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                rel = candidate
                destination = logs_dir / rel
                if copy_if_exists(candidate, destination):
                    copied.append(str(rel))

    return copied


def main() -> int:
    args = parse_args()
    try:
        config_path = Path(args.config)
        config = load_config(config_path)
        profile = resolve_profile(config, args.profile, config_path=config_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = Path(args.output_root) / f"{timestamp}_{profile.name}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    git_sha_code, git_sha = run_cmd(["git", "rev-parse", "HEAD"])
    git_branch_code, git_branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    _, git_status = run_cmd(["git", "status", "--porcelain"])

    metadata: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_dir": str(bundle_dir),
        "config_path": args.config,
        "profile": profile.to_dict(),
        "git": {
            "sha": git_sha if git_sha_code == 0 else "",
            "branch": git_branch if git_branch_code == 0 else "",
            "dirty": bool(git_status),
        },
        "tool_versions": {
            "pandoc": command_version("pandoc", ["--version"]),
            "xelatex": command_version("xelatex", ["--version"]),
            "python": sys.version.splitlines()[0],
            "make": command_version("make", ["--version"]),
        },
        "manifest_path": args.manifest or "",
    }

    (bundle_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "profile.json").write_text(
        json.dumps(profile.to_dict(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    if args.manifest:
        manifest_path = Path(args.manifest)
        if manifest_path.exists():
            copy_if_exists(manifest_path, bundle_dir / "build_manifest.json")

    sources_dir = bundle_dir / "sources"
    for src_path in profile.manuscript_sources:
        src = Path(src_path)
        if src.exists():
            target = sources_dir / (src.name + ".excerpt.txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(with_line_numbers(src), encoding="utf-8")

    bib_path = Path(profile.bibliography)
    if bib_path.exists():
        target = sources_dir / (bib_path.name + ".excerpt.txt")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(with_line_numbers(bib_path), encoding="utf-8")

    logs = gather_logs(bundle_dir)
    if not logs:
        readme = bundle_dir / "logs" / "README.txt"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text("No matching log files were found.\n", encoding="utf-8")

    summary_lines = [
        "Build diagnostics bundle",
        f"Generated: {metadata['generated_at_utc']}",
        f"Profile: {profile.name}",
        f"Bundle path: {bundle_dir}",
        f"Manifest copied: {'yes' if (bundle_dir / 'build_manifest.json').exists() else 'no'}",
        f"Log files copied: {len(logs)}",
    ]
    (bundle_dir / "SUMMARY.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Diagnostics bundle created: {bundle_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
