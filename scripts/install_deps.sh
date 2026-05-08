#!/usr/bin/env bash
set -euo pipefail

PLATFORM="$(uname -s)"

MODE="minimal"
DRY_RUN=0
ESTIMATE_ONLY=0
SKIP_UPDATE=0
NO_SUDO=0

UBUNTU_MINIMAL_PACKAGES=(
  make
  pandoc
  texlive-xetex
  texlive-latex-extra
  python3
  python3-yaml
  ripgrep
  poppler-utils
  git
  curl
  jq
)

UBUNTU_FULL_EXTRA_PACKAGES=(
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

MACOS_MINIMAL_FORMULAE=(
  pandoc
  poppler
  jq
  ripgrep
  git
  curl
)

MACOS_FULL_EXTRA_FORMULAE=(
  hunspell
)

MACOS_MINIMAL_CASKS=(
  mactex-no-gui
)

MACOS_FULL_EXTRA_CASKS=(
  libreoffice
)

usage() {
  cat <<'EOF'
Install makedoc dependencies for Ubuntu/WSL or macOS.

Usage:
  scripts/install_deps.sh [options]

Options:
  --mode minimal|full   Dependency tier to install (default: minimal)
  --dry-run             Show what would be installed without changing system state
  --estimate-only       Show package plan and any available size estimate, then exit
  --skip-update         Skip apt-get update on Ubuntu/WSL
  --no-sudo             Run apt-get directly (for already-root shells on Ubuntu/WSL)
  -h, --help            Show this help

Examples:
  scripts/install_deps.sh --mode minimal --estimate-only
  scripts/install_deps.sh --mode full --dry-run
  scripts/install_deps.sh --mode minimal

Notes:
  - "minimal" is enough for build/check workflows in this repo.
  - "full" adds optional tooling such as hunspell and LibreOffice.
  - On macOS, the minimal tier uses MacTeX (no GUI) rather than BasicTeX so the
    default xelatex-based manuscript workflow has the LaTeX packages it expects.
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

validate_mode() {
  case "$MODE" in
    minimal|full) ;;
    *)
      echo "Error: invalid --mode '$MODE' (expected 'minimal' or 'full')." >&2
      exit 1
      ;;
  esac
}

ubuntu_packages() {
  local -a packages=("${UBUNTU_MINIMAL_PACKAGES[@]}")
  if [[ "$MODE" == "full" ]]; then
    packages+=("${UBUNTU_FULL_EXTRA_PACKAGES[@]}")
  fi
  printf '%s\n' "${packages[@]}"
}

macos_formulae() {
  local -a packages=("${MACOS_MINIMAL_FORMULAE[@]}")
  if [[ "$MODE" == "full" ]]; then
    packages+=("${MACOS_FULL_EXTRA_FORMULAE[@]}")
  fi
  printf '%s\n' "${packages[@]}"
}

macos_casks() {
  local -a packages=("${MACOS_MINIMAL_CASKS[@]}")
  if [[ "$MODE" == "full" ]]; then
    packages+=("${MACOS_FULL_EXTRA_CASKS[@]}")
  fi
  printf '%s\n' "${packages[@]}"
}

ubuntu_estimate_line() {
  local output
  if ! output="$(LC_ALL=C apt-get -s install "$@" 2>&1)"; then
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
    if [[ "${BASH_REMATCH[2]}" -eq 0 ]]; then
      echo "All requested packages are already installed; additional disk usage is approximately 0 B."
    else
      echo "$summary_line (apt did not emit an explicit disk-size line in simulation output.)"
    fi
    return 0
  fi

  return 1
}

print_macos_plan() {
  local -a formulae=("$@")
  local cask_count="${MACOS_CASK_COUNT:-0}"
  local idx=0

  echo "Homebrew formulae:"
  while [[ "$idx" -lt "${#formulae[@]}" ]]; do
    echo "  - ${formulae[$idx]}"
    idx=$((idx + 1))
  done

  if [[ "$cask_count" -gt 0 ]]; then
    echo "Homebrew casks:"
    idx=0
    while [[ "$idx" -lt "$cask_count" ]]; do
      echo "  - ${MACOS_CASK_ITEMS[$idx]}"
      idx=$((idx + 1))
    done
  fi
}

run_macos() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "Error: Homebrew is required on macOS." >&2
    exit 1
  fi

  local -a formulae
  local -a casks
  formulae=()
  casks=()
  while IFS= read -r pkg; do
    [[ -n "$pkg" ]] && formulae+=("$pkg")
  done < <(macos_formulae)
  while IFS= read -r pkg; do
    [[ -n "$pkg" ]] && casks+=("$pkg")
  done < <(macos_casks)

  MACOS_CASK_COUNT="${#casks[@]}"
  MACOS_CASK_ITEMS=("${casks[@]}")

  echo "Platform: macOS"
  echo "Mode: $MODE"
  echo "Formula count: ${#formulae[@]}"
  echo "Cask count: ${#casks[@]}"
  print_macos_plan "${formulae[@]}"
  echo "Estimated additional disk usage:"
  echo "  Homebrew does not provide a reliable host-specific install-size estimate here; review the package plan above."

  if [[ "$ESTIMATE_ONLY" -eq 1 ]]; then
    echo "Estimate requested; exiting without installation."
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ "${#formulae[@]}" -gt 0 ]]; then
      brew install --formula --dry-run "${formulae[@]}"
    fi
    if [[ "${#casks[@]}" -gt 0 ]]; then
      brew install --cask --dry-run "${casks[@]}"
    fi
    echo "Dry run complete; no packages were installed."
    return 0
  fi

  if [[ "${#formulae[@]}" -gt 0 ]]; then
    brew install "${formulae[@]}"
  fi
  if [[ "${#casks[@]}" -gt 0 ]]; then
    brew install --cask "${casks[@]}"
  fi

  if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user pyyaml
  else
    echo "Warning: python3 was not found after macOS dependency install; PyYAML was not installed." >&2
  fi

  if [[ -d /Library/TeX/texbin ]]; then
    echo "MacTeX command-line tools are available under /Library/TeX/texbin."
    echo "New shells may need: eval \"\$(/usr/libexec/path_helper)\""
  fi

  echo "Install complete."
}

run_ubuntu() {
  if ! command -v apt-get >/dev/null 2>&1; then
    echo "Error: apt-get is required on Linux for this installer path." >&2
    exit 1
  fi

  local -a packages
  packages=()
  while IFS= read -r pkg; do
    [[ -n "$pkg" ]] && packages+=("$pkg")
  done < <(ubuntu_packages)

  local -a sudo_cmd=(sudo)
  if [[ "$NO_SUDO" -eq 1 || "${EUID:-$(id -u)}" -eq 0 ]]; then
    sudo_cmd=()
  fi

  echo "Platform: Linux/Ubuntu"
  echo "Mode: $MODE"
  echo "Package count: ${#packages[@]}"
  echo "Packages:"
  local pkg
  for pkg in "${packages[@]}"; do
    echo "  - $pkg"
  done

  local estimate
  if estimate="$(ubuntu_estimate_line "${packages[@]}")"; then
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
    LC_ALL=C apt-get -s install "${packages[@]}"
    echo "Dry run complete; no packages were installed."
    return 0
  fi

  if [[ "$SKIP_UPDATE" -eq 0 ]]; then
    "${sudo_cmd[@]}" apt-get update
  fi

  "${sudo_cmd[@]}" apt-get install -y "${packages[@]}"
  echo "Install complete."
}

main() {
  parse_args "$@"
  validate_mode

  case "$PLATFORM" in
    Linux)
      run_ubuntu
      ;;
    Darwin)
      run_macos
      ;;
    *)
      echo "Error: unsupported platform '$PLATFORM'. Expected Linux or Darwin." >&2
      exit 1
      ;;
  esac
}

main "$@"
