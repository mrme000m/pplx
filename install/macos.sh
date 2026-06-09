#!/usr/bin/env bash
# install-macos.sh — Install PPLX CLI + Plugin on macOS
# Usage: bash install/macos.sh [--dev-dir /path/to/install]

set -euo pipefail

REPO_URL="https://github.com/mrme000m/pplx.git"
DEV_DIR="${1:-$HOME/dev}"
INSTALL_DIR="$DEV_DIR/pplx"
VENV_DIR="$INSTALL_DIR/.venv"
PYTHON="${PYTHON:-python3}"

check_prereqs() {
    echo "Checking prerequisites..."

    if ! command -v git &>/dev/null; then
        echo "git is required. Install with: xcode-select --install"
        exit 1
    fi

    if ! command -v "$PYTHON" &>/dev/null; then
        echo "Python 3 is required. Install with: brew install python"
        exit 1
    fi

    local py_ver
    py_ver=$("$PYTHON" --version 2>&1 | awk '{print $2}')
    echo "  Python: $py_ver"

    if ! "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
        echo "Python 3.10+ is required. Found: $py_ver"
        exit 1
    fi

    echo "  git: OK"
    echo "  Python 3.10+: OK"
}

clone_repo() {
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "Updating existing repo at $INSTALL_DIR..."
        cd "$INSTALL_DIR"
        git pull --ff-only
    else
        echo "Cloning $REPO_URL into $INSTALL_DIR..."
        mkdir -p "$DEV_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
}

setup_venv() {
    echo "Setting up virtual environment..."
    if [ ! -d "$VENV_DIR" ]; then
        "$PYTHON" -m venv "$VENV_DIR"
    fi

    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"

    echo "  Upgrading pip..."
    pip install --quiet --upgrade pip
}

install_package() {
    echo "Installing PPLX package..."
    pip install --quiet -e "$INSTALL_DIR"

    echo "Installing plugin dependencies..."
    pip install --quiet curl-cffi bitwarden-sdk python-dotenv
}

verify_install() {
    echo "Verifying installation..."

    if command -v pplx &>/dev/null; then
        echo "  pplx CLI: $(command -v pplx)"
        pplx --version
    else
        echo "  pplx CLI: not in PATH (add $VENV_DIR/bin to PATH)"
    fi

    echo ""
    echo "Running health check (no live search)..."
    bash "$INSTALL_DIR/pplx-plugin/scripts/pplx-health.sh" --no-search 2>/dev/null || true
}

print_next_steps() {
    cat <<'EOF'

========================================
  PPLX Installation Complete!
========================================

Next steps:

1. Activate the virtual environment:
   source ~/.venv/bin/activate

2. Set up Bitwarden authentication:
   - Ensure 'bw' CLI is installed: brew install bitwarden-cli
   - Create a Secure Note named "perplexity.ai" with your cookies JSON

3. Or use BWS (preferred):
   export BWS_ACCESS_TOKEN=<your-token>
   python scripts/setup_bws_secret.py setup-cookies /path/to/cookies.json

4. Test a search:
   pplx search "Hello world" --mode auto

5. Add to your agent harness:
   Claude Code: claude --plugin-dir INSTALL_DIR/pplx-plugin
   OpenCode:    add INSTALL_DIR/pplx-plugin to skills.paths

For help: pplx --help
For plugin commands: ls INSTALL_DIR/pplx-plugin/commands/

EOF
}

main() {
    echo "PPLX Installer for macOS"
    echo "========================"

    check_prereqs
    clone_repo
    setup_venv
    install_package
    verify_install
    print_next_steps
}

main "$@"
