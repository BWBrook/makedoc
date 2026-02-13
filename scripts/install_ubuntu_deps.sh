#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

MODE="minimal"
DRY_RUN=0
ESTIMATE_ONLY=0
SKIP_UPDATE=0
NO_SUDO=0

MINIMAL_PACKAGES=(
  make
  pandoc
  texlive-xetex
  python3
  python3-yaml
  ripgrep
  poppler-utils
  git
  curl
  jq
)

FULL_EXTRA_PACKAGES=(
  latexmk
  biber
  texlive-latex-extra
  texlive-fonts-recommended
  texlive-fonts-extra
  texlive-science
  hunspell
  hunspell-en-us
  hunspell-en-gb
  hunspell-en-au
  libreoffice
)

usage() {
  cat <<'EOF'
Install Ubuntu dependencies for makedoc.

Usage:
  scripts/install_ubuntu_deps.sh [options]

Options:
  --mode minimal|full   Dependency tier to install (default: minimal)
  --dry-run             Show what would be installed without changing system state
  --estimate-only       Show package list + disk usage estimate, then exit
  --skip-update         Skip apt-get update
  --no-sudo             Run apt-get directly (for already-root shells)
  -h, --help            Show this help

Examples:
  scripts/install_ubuntu_deps.sh --mode minimal --estimate-only
  scripts/install_ubuntu_deps.sh --mode full
  scripts/install_ubuntu_deps.sh --mode full --dry-run

Notes:
  - "minimal" is enough for build/check/CI workflows in this repo.
  - "full" adds heavy optional tooling (LibreOffice, broader TeX extras, hunspell locales).
  - Tectonic is not installed here because it is typically not provided as an Ubuntu apt package.
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode)
        shift
        if [[ $# -eq 0 ]]; then
          echo "Error: --mode requires a value." >&2
          exit 1
        fi
        MODE="$1"
        ;;
      --dry-run)
        DRY_RUN=1
        ;;
      --estimate-only)
        ESTIMATE_ONLY=1
        ;;
      --skip-update)
        SKIP_UPDATE=1
        ;;
      --no-sudo)
        NO_SUDO=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Error: unknown argument '$1'." >&2
        usage
        exit 1
        ;;
    esac
    shift
  done
}

mode_packages() {
  case "$MODE" in
    minimal)
      printf '%s\n' "${MINIMAL_PACKAGES[@]}"
      ;;
    full)
      printf '%s\n' "${MINIMAL_PACKAGES[@]}" "${FULL_EXTRA_PACKAGES[@]}"
      ;;
    *)
      echo "Error: invalid --mode '$MODE' (expected 'minimal' or 'full')." >&2
      exit 1
      ;;
  esac
}

estimate_line() {
  local -a pkgs=("$@")
  local output
  if ! output="$(LC_ALL=C apt-get -s install "${pkgs[@]}" 2>&1)"; then
    return 1
  fi

  local disk_line
  disk_line="$(grep -E "After this operation, .* of additional disk space will be used\." <<<"$output" | tail -n 1 || true)"
  if [[ -n "$disk_line" ]]; then
    echo "$disk_line"
    return 0
  fi

  local summary_line
  summary_line="$(grep -E "^[0-9]+ upgraded, [0-9]+ newly installed, [0-9]+ to remove and [0-9]+ not upgraded\." <<<"$output" | tail -n 1 || true)"
  if [[ "$summary_line" =~ ^([0-9]+)\ upgraded,\ ([0-9]+)\ newly\ installed,\ ([0-9]+)\ to\ remove\ and\ ([0-9]+)\ not\ upgraded\.$ ]]; then
    local newly_installed="${BASH_REMATCH[2]}"
    if [[ "$newly_installed" -eq 0 ]]; then
      echo "All requested packages are already installed; additional disk usage is approximately 0 B."
      return 0
    fi
    echo "$summary_line (apt did not emit an explicit disk-size line in simulation output.)"
    return 0
  fi

  return 1
}

main() {
  parse_args "$@"

  mapfile -t PACKAGES < <(mode_packages)
  if [[ ${#PACKAGES[@]} -eq 0 ]]; then
    echo "Error: package list resolved to empty set." >&2
    exit 1
  fi

  local SUDO=(sudo)
  if [[ "$NO_SUDO" -eq 1 || "${EUID:-$(id -u)}" -eq 0 ]]; then
    SUDO=()
  fi

  echo "Mode: $MODE"
  echo "Package count: ${#PACKAGES[@]}"
  echo "Packages:"
  for pkg in "${PACKAGES[@]}"; do
    echo "  - $pkg"
  done

  local estimate
  if estimate="$(estimate_line "${PACKAGES[@]}")"; then
    echo "Estimated additional disk usage:"
    echo "  $estimate"
  else
    echo "Estimated additional disk usage:"
    echo "  (unable to determine from apt simulation on this host)"
  fi

  if [[ "$ESTIMATE_ONLY" -eq 1 ]]; then
    echo "Estimate requested; exiting without installation."
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    LC_ALL=C apt-get -s install "${PACKAGES[@]}"
    echo "Dry run complete; no packages were installed."
    return 0
  fi

  if [[ "$SKIP_UPDATE" -eq 0 ]]; then
    "${SUDO[@]}" apt-get update
  fi

  "${SUDO[@]}" apt-get install -y "${PACKAGES[@]}"
  echo "Install complete."
}

main "$@"
