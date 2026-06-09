#!/usr/bin/env bash
# install.sh — Cross-platform PPLX installer
# Detects OS and delegates to the appropriate platform script.
# Usage: bash install.sh [--dev-dir /path/to/install]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

bash "$SCRIPT_DIR/install/${OS}.sh" "$@"
