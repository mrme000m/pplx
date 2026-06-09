#!/bin/bash
# PPLX Pro Feature Check — verify Pro features are accessible
# Usage: bash pplx-pro-check.sh [--verbose]

set -euo pipefail

verbose=false
if [[ "${1:-}" == "--verbose" ]]; then
    verbose=true
fi

# Resolve plugin directory (portable)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

info() {
    if $verbose; then
        echo "  $1"
    fi
}

echo "=== PPLX Pro Feature Check ==="
echo ""

# Check pplx CLI
if command -v pplx &>/dev/null; then
    pass "pplx CLI found"
    info "$(pplx --version 2>/dev/null || echo 'version unknown')"
else
    fail "pplx CLI not found"
    echo "  Run: python3 -m pip install -e ."
    exit 1
fi

# Check auth
if $verbose; then
    echo ""
    echo "--- Auth Check ---"
fi

if pplx status --raw &>/dev/null; then
    pass "Authentication working"
    if $verbose; then
        pplx status --sections user,rate 2>/dev/null || warn "Could not fetch status details"
    fi
else
    fail "Authentication failed"
    echo "  Check: BWS_ACCESS_TOKEN or PERPLEXITY_COOKIES_PATH"
    exit 1
fi

# Check models (Pro feature indicator)
if $verbose; then
    echo ""
    echo "--- Model Discovery ---"
fi

if pplx models --raw &>/dev/null; then
    pass "Model discovery working"
    if $verbose; then
        echo "  Available modes:"
        pplx models --raw 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for mode, models in data.items():
    if models:
        print(f'    {mode}: {len(models)} models')
" 2>/dev/null || true
    fi
else
    warn "Model discovery failed (may indicate connectivity issue)"
fi

# Check memories (Pro feature)
if $verbose; then
    echo ""
    echo "--- Memories ---"
fi

if pplx memories list --limit 1 &>/dev/null; then
    pass "Memories accessible"
else
    warn "Memories not accessible (may require Pro subscription)"
fi

# Check tasks (Pro feature)
if $verbose; then
    echo ""
    echo "--- Scheduled Tasks ---"
fi

if pplx tasks list &>/dev/null; then
    pass "Scheduled tasks accessible"
else
    warn "Scheduled tasks not accessible (may require Pro subscription)"
fi

# Check workflows (Pro feature)
if $verbose; then
    echo ""
    echo "--- Workflows ---"
fi

if pplx workflows &>/dev/null; then
    pass "Workflows accessible"
else
    warn "Workflows not accessible (may require Pro subscription)"
fi

# Check assets (Pro feature)
if $verbose; then
    echo ""
    echo "--- Assets ---"
fi

if pplx assets list --limit 1 &>/dev/null; then
    pass "Assets accessible"
else
    warn "Assets not accessible (may require Pro subscription)"
fi

# Rate limits
if $verbose; then
    echo ""
    echo "--- Rate Limits ---"
fi

if pplx rate-limits --raw &>/dev/null; then
    pass "Rate limits accessible"
    if $verbose; then
        pplx rate-limits 2>/dev/null || true
    fi
else
    warn "Rate limits not accessible"
fi

# Credits
if $verbose; then
    echo ""
    echo "--- Credits ---"
fi

if pplx credits &>/dev/null; then
    pass "Credits accessible"
    if $verbose; then
        pplx credits 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if isinstance(data, dict):
    balance = data.get('balance', data.get('credits', 'unknown'))
    print(f'  Balance: {balance}')
" 2>/dev/null || true
    fi
else
    warn "Credits not accessible"
fi

echo ""
echo "=== Pro Feature Check Complete ==="
