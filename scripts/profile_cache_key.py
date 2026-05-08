#!/usr/bin/env python3
"""Compute a stable cache key for a selected build profile config."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to build profile YAML.")
    parser.add_argument("--profile", default="", help="Selected profile name.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser()

    digest = hashlib.sha256()
    digest.update(str(config_path.resolve()).encode("utf-8"))
    digest.update(b"\0")
    digest.update(args.profile.encode("utf-8"))
    digest.update(b"\0")
    if config_path.exists():
        digest.update(config_path.read_bytes())
    else:
        digest.update(b"<missing-config>")

    print(digest.hexdigest()[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
