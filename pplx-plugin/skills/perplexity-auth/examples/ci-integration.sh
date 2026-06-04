#!/bin/bash
# CI/CD integration - authenticate in headless/CI environments
# Usage: ci-integration.sh <email> <gmail-app-password>

set -e

EMAIL="${1:-${PERPLEXITY_EMAIL:-}}"
GMAIL_APP_PASSWORD="${2:-${GMAIL_APP_PASSWORD:-}}"
SKILL_DIR="${PERPLEXITY_AUTH_SKILL_DIR:-$HOME/code/MCP/pplx/pplx-plugin/skills/perplexity-auth}"

if [[ -z "$EMAIL" || -z "$GMAIL_APP_PASSWORD" ]]; then
    echo "Usage: ci-integration.sh <email> <gmail-app-password>"
    exit 1
fi

echo "=== CI Authentication ==="

export PERPLEXITY_EMAIL="$EMAIL"
export GMAIL_APP_PASSWORD="$GMAIL_APP_PASSWORD"

cd "$SKILL_DIR"

echo "Installing dependencies..."
bash scripts/utils/cloak_setup.sh --force

echo "Running health check..."
python3 scripts/diagnostics/health_check.py --quick

echo "Running full login..."
python3 scripts/auth/login.py --email "$EMAIL" --bw-save

echo "Validating session..."
python3 scripts/auth/session_refresh.py --validate

echo "=== CI Authentication Complete ==="