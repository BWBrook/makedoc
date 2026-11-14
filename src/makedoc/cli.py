"""Command-line interface."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path
from types import SimpleNamespace

import yaml

from . import __version__, csl
from .build import FORMATS, PDF_ENGINE, BuildError, build_profile
from .lint import lint_sources
from .profile import Profile, load_config, load_profile, profile_names
from .refs import audit_references
from .validate import validate_config

DEFAULT_CONFIG = "settings/build.yaml"
REQUIRED_TEX_PACKAGES = (
    "fontspec", "unicode-math", "geometry", "lineno", "etoolbox", "needspace", "newunicodechar",
)
INSTALL_HINTS = {
    "darwin": "brew install pandoc texlive poppler",
    "linux": (
        "sudo apt-get install pandoc texlive-xetex texlive-latex-extra "
        "texlive-fonts-recommended lmodern poppler-utils"
    ),
}


def _add_selection(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-c", "--config", default=DEFAULT_CONFIG,
        help=f"build profile YAML (default: {DEFAULT_CONFIG})",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-p", "--profile", action="append", default=[],
        help="profile to act on; repeatable (default: the config's default_profile)",
    )
    group.add_argument("--all", action="store_true", help="act on every profile in the config")


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="makedoc", description=__doc__.strip() and
                                  "Build journal-ready PDF and DOCX manuscripts from Markdown.")
    top.add_argument("--version", action="version", version=f"makedoc {__version__}")
    sub = top.add_subparsers(dest="command", required=True, metavar="command")

    build = sub.add_parser("build", help="build PDF and DOCX for the selected profiles")
    _add_selection(build)
    build.add_argument("--pdf", action="store_true", help="build only the PDF")
    build.add_argument("--docx", action="store_true", help="build only the DOCX")
    build.add_argument("--strict", action="store_true", help="treat warnings as errors")
    build.add_argument(
        "--workdir", help="keep intermediate files (prepared.md, layout.tex, LaTeX logs) here"
    )
    build.set_defaults(func=cmd_build)

    check = sub.add_parser(
        "check", help="validate the config, lint the sources and audit citations (no build)"
    )
    _add_selection(check)
    check.set_defaults(func=cmd_check)

    profiles = sub.add_parser("profiles", help="list the profiles in a config")
    profiles.add_argument("-c", "--config", default=DEFAULT_CONFIG)
    profiles.set_defaults(func=cmd_profiles)

    show = sub.add_parser("show", help="print a profile with every path and default resolved")
    _add_selection(show)
    show.set_defaults(func=cmd_show)

    init = sub.add_parser("init", help="write a starter manuscript layout into a directory")
    init.add_argument("directory", nargs="?", default=".", help="target directory (default: .)")
    init.set_defaults(func=cmd_init)

    doctor = sub.add_parser("doctor", help="check that Pandoc, xelatex and LaTeX packages are present")
    doctor.set_defaults(func=cmd_doctor)

    csl_parser = sub.add_parser("csl", help="find or download a citation style by journal name")
    csl_sub = csl_parser.add_subparsers(dest="csl_command", required=True, metavar="action")
    for name, func, text in (
        ("search", cmd_csl_search, "list matching styles, local and from the Zotero repository"),
        ("fetch", cmd_csl_fetch, "download the best match unless a local one exists"),
    ):
        action = csl_sub.add_parser(name, help=text)
        action.add_argument("journal", help="journal name, for example 'Ecology Letters'")
        action.add_argument(
            "--dir", action="append", default=[], dest="search_dir",
            help="directory to search for local *.csl files; repeatable (default: ./csl)",
        )
        if name == "fetch":
            action.add_argument("--dest", default="csl", help="download directory (default: ./csl)")
            action.add_argument("--force", action="store_true", help="overwrite an existing file")
        action.set_defaults(func=func)
    return top


def _selected_profiles(args: argparse.Namespace) -> tuple[Path, list[Profile]]:
    config_path = Path(args.config)
    config = load_config(config_path)
    names: list[str | None]
    if getattr(args, "all", False):
        names = list(profile_names(config))
    else:
        names = list(dict.fromkeys(args.profile)) or [None]
    return config_path, [load_profile(config_path, name) for name in names]


def _config_problems(args: argparse.Namespace) -> list[str]:
    config_path = Path(args.config)
    config = load_config(config_path)
    names = profile_names(config) if args.all else list(dict.fromkeys(args.profile))
    return validate_config(config_path, names)


def cmd_build(args: argparse.Namespace) -> int:
    problems = _config_problems(args)
    if problems:
        for problem in problems:
            print(f"config: {problem}", file=sys.stderr)
        return 1
    config_path, profiles = _selected_profiles(args)
    formats = tuple(fmt for fmt in FORMATS if getattr(args, fmt)) or FORMATS
    status = 0
    for profile in profiles:
        workdir = None
        if args.workdir:
            workdir = Path(args.workdir) / profile.name if len(profiles) > 1 else Path(args.workdir)
        try:
            result = build_profile(profile, config_path, formats, workdir)
        except BuildError as exc:
            print(f"error [{profile.name}]: {exc}", file=sys.stderr)
            status = 1
            continue
        for warning in result.warnings:
            print(f"warning [{profile.name}]: {warning}", file=sys.stderr)
        for output in result.outputs:
            print(f"[{profile.name}] wrote {output}")
        if args.strict and result.warnings:
            print(f"error [{profile.name}]: {len(result.warnings)} warning(s) with --strict", file=sys.stderr)
            status = 1
    return status


def cmd_check(args: argparse.Namespace) -> int:
    problems = _config_problems(args)
    if problems:
        for problem in problems:
            print(f"config: {problem}", file=sys.stderr)
        return 1

    _, profiles = _selected_profiles(args)
    failed = False
    for profile in profiles:
        errors = lint_sources([Path(item) for item in profile.lint_sources])
        for err in errors:
            print(f"{err.source}:{err.line}: {err.message}", file=sys.stderr)
        audit = audit_references(
            Path(profile.bibliography), [Path(item) for item in profile.manuscript_sources]
        )
        for hit in audit.unknown:
            print(f"{hit.source}:{hit.line}: citation key '{hit.key}' is not in the bibliography", file=sys.stderr)
        failed = failed or bool(errors or audit.unknown)
        print(
            f"[{profile.name}] {len(errors)} lint error(s); {len(audit.cited)} keys cited, "
            f"{len({hit.key for hit in audit.unknown})} unknown, {len(audit.unused)} unused in bibliography"
        )
    return 1 if failed else 0


def cmd_profiles(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config))
    default = config.get("default_profile")
    for name, raw in (config.get("profiles") or {}).items():
        marker = "*" if name == default else " "
        description = raw.get("description", "") if isinstance(raw, dict) else ""
        print(f"{marker} {name}  {description}".rstrip())
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    _, profiles = _selected_profiles(args)
    data = {profile.name: profile.to_dict() for profile in profiles}
    print(yaml.safe_dump(data, sort_keys=False).strip())
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.directory)
    template = resources.files("makedoc") / "template"
    written = []
    with resources.as_file(template) as source_root:
        files = [path for path in sorted(source_root.rglob("*")) if path.is_file()]
        clashes = [path for path in files if (target / path.relative_to(source_root)).exists()]
        if clashes:
            names = ", ".join(str(path.relative_to(source_root)) for path in clashes)
            print(f"error: refusing to overwrite existing files in {target}: {names}", file=sys.stderr)
            return 1
        for path in files:
            destination = target / path.relative_to(source_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            written.append(destination)
    for path in written:
        print(f"wrote {path}")
    print(f"Next: makedoc build -c {target / DEFAULT_CONFIG}")
    return 0


def _kpsewhich(name: str) -> bool:
    try:
        proc = subprocess.run(["kpsewhich", name], capture_output=True, text=True, check=False)
    except OSError:
        return False
    return bool(proc.stdout.strip())


def cmd_doctor(args: argparse.Namespace) -> int:
    missing: list[str] = []
    for tool in ("pandoc", PDF_ENGINE):
        path = shutil.which(tool)
        if path:
            first = subprocess.run([tool, "--version"], capture_output=True, text=True, check=False)
            print(f"ok       {tool}: {(first.stdout.splitlines() or [''])[0]}")
        else:
            print(f"MISSING  {tool}")
            missing.append(tool)
    for package in REQUIRED_TEX_PACKAGES:
        if _kpsewhich(f"{package}.sty"):
            print(f"ok       LaTeX package {package}")
        else:
            print(f"MISSING  LaTeX package {package}")
            missing.append(package)
    if missing:
        platform = "darwin" if sys.platform == "darwin" else "linux"
        print(f"\nInstall hint: {INSTALL_HINTS[platform]}")
        return 1
    print("\nAll required tools are present.")
    return 0


def _csl_args(args: argparse.Namespace, **extra: object) -> SimpleNamespace:
    cache = Path.home() / ".cache" / "makedoc" / "zotero_styles.json"
    return SimpleNamespace(
        journal=args.journal,
        search_dir=args.search_dir or ["csl"],
        max_results=8,
        cache_file=str(cache),
        cache_ttl_hours=24.0,
        **extra,
    )


def cmd_csl_search(args: argparse.Namespace) -> int:
    return csl.cmd_search(_csl_args(args))


def cmd_csl_fetch(args: argparse.Namespace) -> int:
    return csl.cmd_source(
        _csl_args(args, dest_dir=args.dest, filename=None, local_only=False, force=args.force, path_only=False)
    )


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
