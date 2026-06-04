#!/usr/bin/env bash
#
# cloak_setup.sh — Install CloakBrowser and verify CDP dependencies
#
# CloakBrowser is a stealth Chromium with 32 C++ source-level patches that
# evades bot detection (Cloudflare, PerimeterX, DataDome, etc). Required for
# automated Perplexity login because stock Chrome/CDP triggers Cloudflare
# "Just a moment…" interstitial.
#
# Usage:
#   ./cloak_setup.sh          # Check status or install
#   ./cloak_setup.sh --force  # Force reinstall
#
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; }
info() { echo -e "${CYAN}[i]${NC} $*"; }

FORCE="${1:-}"

# ─── Check Python ────────────────────────────────────────────────────────────

check_python() {
    if command -v python3 &>/dev/null; then
        local ver
        ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log "Python $ver found"
        return 0
    fi
    err "Python 3.10+ required — install from https://python.org"
    return 1
}

# ─── Check/Install CloakBrowser ──────────────────────────────────────────────
check_cloakbrowser() {
    local installed=""

    # Try to import and get binary_info (the correct lowercase module name)
    installed=$(python3 -c "
from cloakbrowser import binary_info
try:
    bi = binary_info()
    print(f\"installed={bi.get('installed', False)};version={bi.get('version', '?')};path={bi.get('binary_path', '?')}\")
except Exception as e:
    print(f'installed=False;error={e}')
" 2>/dev/null) || true

    if echo "$installed" | grep -q "installed=True"; then
        local info=""
        info=$(python3 -c "
from cloakbrowser import binary_info
bi = binary_info()
print(f\"v{bi.get('version', '?')} at {bi.get('binary_path', 'unknown')}\")
" 2>/dev/null) || info="(details unavailable)"
        log "CloakBrowser $info"
        return 0
    fi

    if [ "$FORCE" != "--force" ]; then
        warn "CloakBrowser not installed"
        info "Install with: pip3 install cloakbrowser"
        info "Or run: $0 --force to install automatically"
        return 1
    fi

    install_cloakbrowser
}

install_cloakbrowser() {
    info "Installing CloakBrowser..."
    # Try standard install first, fall back to --break-system-packages
    if pip3 install cloakbrowser 2>/dev/null; then
        log "CloakBrowser installed via pip3"
    else
        pip3 install --break-system-packages cloakbrowser
        log "CloakBrowser installed with --break-system-packages"
    fi

    # Verify
    python3 -c "from cloakbrowser import binary_info; assert binary_info()['installed']"
    log "CloakBrowser verified"
}

# ─── Check websocket-client ──────────────────────────────────────────────────

check_websocket() {
    if python3 -c "import websocket" 2>/dev/null; then
        log "websocket-client available"
        return 0
    fi
    warn "Installing websocket-client..."
    pip3 install websocket-client 2>/dev/null || pip3 install --break-system-packages websocket-client
    log "websocket-client installed"
}

# ─── Check Bitwarden CLI ─────────────────────────────────────────────────────

check_bw() {
    if command -v bw &>/dev/null; then
        log "Bitwarden CLI available"
        return 0
    fi
    warn "Bitwarden CLI (bw) not found — cookie sync won't work"
    info "Install with: brew install bitwarden-cli"
    return 1
}

# ─── Check curl_cffi ─────────────────────────────────────────────────────────

check_curl_cffi() {
    if python3 -c "import curl_cffi" 2>/dev/null; then
        log "curl_cffi available"
        return 0
    fi
    warn "Installing curl_cffi..."
    pip3 install curl_cffi 2>/dev/null || pip3 install --break-system-packages curl_cffi
    log "curl_cffi installed"
}

# ─── Main ────────────────────────────────────────────────────────────────────

main() {
    echo ""
    info "CloakBrowser Setup for Perplexity Login"
    echo "  ========================================"
    echo ""

    local ok=true

    check_python       || ok=false
    check_websocket    || ok=false
    check_curl_cffi    || ok=false

    if [ "$FORCE" = "--force" ]; then
        install_cloakbrowser
    elif ! check_cloakbrowser; then
        ok=false
    fi

    check_bw || warn "bw CLI not found (cookie sync won't work)"

    echo ""
    if $ok; then
        log "All dependencies ready"
        echo ""
        info "Next: run login.py to perform automated Perplexity login"
    else
        err "Some dependencies missing — fix above before running login.py"
    fi
}

main "$@"
