#!/bin/bash
# Quick Perplexity Authentication Flow

set -e

SKILL_DIR="$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")"
SCRIPTS_DIR="$SKILL_DIR/scripts"

echo "=== Perplexity Quick Auth Flow ==="
echo "Email: $PERPLEXITY_EMAIL"
echo ""

# Prerequisites
if [ -z "$PERPLEXITY_EMAIL" ] || [ -z "$GMAIL_APP_PASSWORD" ]; then
  echo "Error: PERPLEXITY_EMAIL and GMAIL_APP_PASSWORD required"
  exit 1
fi

# Install CloakBrowser
echo "1/4: Checking dependencies..."
bash "$SCRIPTS_DIR/utils/cloak_setup.sh" || true

# Run login
echo "2/4: Running login (30-90 seconds)..."
python3 "$SCRIPTS_DIR/auth/login.py" --email "$PERPLEXITY_EMAIL" --bw-save

# Verify
echo "3/4: Verifying session..."
python3 "$SCRIPTS_DIR/session/session_status.py" --email "$PERPLEXITY_EMAIL"

# Health check
echo "4/4: Health check..."
python3 "$SCRIPTS_DIR/diagnostics/health_check.py" --quick

echo "=== Success! ==="
