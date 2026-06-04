#!/bin/bash
# Nightly session refresh cron script
# Add to crontab: 0 3 * * * /path/to/session-refresh-loop.sh

SKILL_DIR="${PERPLEXITY_AUTH_SKILL_DIR:-$HOME/code/MCP/pplx/pplx-plugin/skills/perplexity-auth}"
EMAIL="${PERPLEXITY_EMAIL:-}"

if [[ -z "$EMAIL" ]]; then
    echo "ERROR: PERPLEXITY_EMAIL not set"
    exit 1
fi

LOGFILE="${HOME}/.perplexity-debug/sessions/$(date +%Y%m%d)/refresh.log"
mkdir -p "$(dirname "$LOGFILE")"

echo "[$(date)] Starting session refresh for $EMAIL" >> "$LOGFILE"

cd "$SKILL_DIR"

python3 scripts/auth/session_refresh.py --refresh >> "$LOGFILE" 2>&1
RESULT=$?

echo "[$(date)] Refresh complete, exit code: $RESULT" >> "$LOGFILE"
exit $RESULT