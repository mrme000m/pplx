#!/usr/bin/env bash
# install-linux.sh — Install PPLX CLI + Plugin on Linux with agent harness setup
# Usage: bash install/linux.sh [--dev-dir /path/to/install] [--skip-plugin] [--plugin-for claude|opencode|codex|all]

set -euo pipefail

REPO_URL="https://github.com/mrme000m/pplx.git"
DEV_DIR="${HOME}/dev"
SKIP_PLUGIN=false
PLUGIN_FOR="all"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev-dir)
            DEV_DIR="$2"
            shift 2
            ;;
        --skip-plugin)
            SKIP_PLUGIN=true
            shift
            ;;
        --plugin-for)
            PLUGIN_FOR="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

INSTALL_DIR="$DEV_DIR/pplx"
VENV_DIR="$INSTALL_DIR/.venv"
PYTHON="${PYTHON:-python3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

check_prereqs() {
    echo "Checking prerequisites..."

    if ! command -v git &>/dev/null; then
        echo "git is required. Install with your package manager:"
        echo "  apt:  sudo apt install git"
        echo "  yum:  sudo yum install git"
        echo "  pacman: sudo pacman -S git"
        exit 1
    fi

    if ! command -v "$PYTHON" &>/dev/null; then
        echo "Python 3 is required. Install with your package manager:"
        echo "  apt:  sudo apt install python3 python3-venv python3-pip"
        echo "  yum:  sudo yum install python3"
        echo "  pacman: sudo pacman -S python python-pip"
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
    PPLX_PYTHON="$VENV_DIR/bin/python" bash "$INSTALL_DIR/pplx-plugin/scripts/pplx-health.sh" --no-search 2>/dev/null || true

    echo ""
    echo "Running Pro feature check..."
    bash "$INSTALL_DIR/pplx-plugin/scripts/pplx-pro-check.sh" --verbose 2>/dev/null || true
}

install_plugin() {
    if [ "$SKIP_PLUGIN" = true ]; then
        echo "Skipping plugin installation (--skip-plugin)"
        return 0
    fi

    echo ""
    echo "========================================"
    echo "  Installing Plugin for Agent Harnesses"
    echo "========================================"
    echo ""

    if [ -f "$SCRIPT_DIR/install-plugin.sh" ]; then
        bash "$SCRIPT_DIR/install-plugin.sh" "$INSTALL_DIR/pplx-plugin" "$PLUGIN_FOR"
    else
        echo "Plugin installer not found at $SCRIPT_DIR/install-plugin.sh"
        echo "You can manually link the plugin directory to your agent harness."
    fi
}

print_next_steps() {
    cat <<EOF

========================================
  PPLX Installation Complete!
========================================

Installation directory: $INSTALL_DIR
Virtual environment:    $VENV_DIR
Plugin directory:       $INSTALL_DIR/pplx-plugin

1. Activate the virtual environment:
   source $VENV_DIR/bin/activate

2. Set up Bitwarden authentication:
   - Install bw CLI: https://bitwarden.com/help/article/cli/
   - Create a Secure Note named "perplexity.ai" with your cookies JSON

3. Or use BWS (preferred):
   export BWS_ACCESS_TOKEN=<your-token>
   python scripts/setup_bws_secret.py setup-cookies /path/to/cookies.json

4. Test a search:
   pplx search "Hello world" --mode auto

5. Plugin commands available:
   /pplx-research      - Grounded web/Space research
   /pplx-orchestrate   - Multi-step research chains
   /pplx-space         - Space management
   /pplx-threads       - Thread workflows
   /pplx-upload        - File upload
   /pplx-settings      - Account audit
   /pplx-pro-optimizer - Mode optimization
   /pplx-persist       - Knowledge persistence
   /pplx-assets        - Asset management
   /pplx-cli-check     - Health diagnostics
   /pplx-bws-setup     - BWS configuration

6. Shell helpers:
   bash $INSTALL_DIR/pplx-plugin/scripts/pplx-health.sh --verbose --no-search
   bash $INSTALL_DIR/pplx-plugin/scripts/pplx-pro-check.sh --verbose
   bash $INSTALL_DIR/pplx-plugin/scripts/pplx-research-chain.sh "query" "follow-up"

For help: pplx --help
For plugin docs: cat $INSTALL_DIR/pplx-plugin/README.md

EOF
}

main() {
    echo "PPLX Installer for Linux"
    echo "========================"
    echo ""
    echo "Install directory: $INSTALL_DIR"
    echo "Plugin target: $PLUGIN_FOR"
    echo ""

    check_prereqs
    clone_repo
    setup_venv
    install_package
    verify_install
    install_plugin
    print_next_steps
}

main "$@"
