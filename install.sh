#!/usr/bin/env bash
# install.sh — Cross-platform PPLX installer with agent harness plugin setup
# Detects OS, installs CLI, and sets up the plugin for Claude Code, OpenCode, Codex, etc.
#
# Usage:
#   bash install.sh [--dev-dir /path/to/install] [--skip-plugin] [--plugin-for claude|opencode|codex|all]
#
# Can be run directly or piped from curl:
#   curl -fsSL https://raw.githubusercontent.com/mrme000m/pplx/main/install.sh | bash
#   curl -fsSL ... | bash -s -- --dev-dir ~/projects --plugin-for claude

set -euo pipefail

REPO_URL="https://github.com/mrme000m/pplx.git"
TEMP_DIR=""

# Detect if we're being piped (BASH_SOURCE is not a real file on disk).
# When piping curl -> bash, BASH_SOURCE is unset. We temporarily disable
# nounset (-u) to test for its presence safely.
is_piped() {
  set +u
  local src="${BASH_SOURCE[0]}"
  set -u
  [[ -z "$src" || ! -f "$src" ]]
}

# Determine OS
OS=""
if [[ "$OSTYPE" == "darwin"* ]]; then
  OS="macos"
elif [[ "$OSTYPE" == "linux"* ]]; then
  OS="linux"
else
  echo "Unsupported OS: $OSTYPE"
  echo "Please run the platform-specific script directly:"
  echo "  Windows: powershell -ExecutionPolicy Bypass -File install/windows.ps1"
  exit 1
fi

if is_piped; then
  # When piped, we don't have the platform script locally.
  # Clone to a temp directory and run from there.
  TEMP_DIR="$(mktemp -d)"
  echo "Downloading installer scripts..."
  git clone --depth 1 "$REPO_URL" "$TEMP_DIR/pplx" >/dev/null 2>&1
  SCRIPT_DIR="$TEMP_DIR/pplx"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# Run the platform-specific installer
bash "$SCRIPT_DIR/install/${OS}.sh" "$@"

# Cleanup temp clone on piped runs
if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
  rm -rf "$TEMP_DIR"
fi
