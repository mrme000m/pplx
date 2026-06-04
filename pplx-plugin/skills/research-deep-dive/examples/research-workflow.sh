#!/bin/bash
# Example: Multi-thread research workflow
# Usage: bash research-workflow.sh "research topic"

set -euo pipefail

TOPIC="${1:-research topic}"
RESULTS_DIR="./research-results-$(date +%Y%m%d)"
mkdir -p "$RESULTS_DIR"

echo "Starting research: $TOPIC"
echo "Results directory: $RESULTS_DIR"

# Initial broad search
echo ""
echo "=== Phase 1: Initial Search ==="
pplx search "$TOPIC" --mode auto --verbose > "$RESULTS_DIR/initial.json" 2>/dev/null
cat "$RESULTS_DIR/initial.json" | jq '.answer'

# Extract backend UUID for follow-ups
UUID=$(cat "$RESULTS_DIR/initial.json" | jq -r '.backend_uuid' 2>/dev/null)

# Follow-up queries
FOLLOWUPS=(
    "What are the main tradeoffs?"
    "What are recent changes or updates?"
    "What are best practices?"
)

echo ""
echo "=== Phase 2: Follow-up Investigation ==="
for i in "${!FOLLOWUPS[@]}"; do
    echo ""
    echo "--- Follow-up $((i+1)): ${FOLLOWUPS[$i]} ---"
    pplx follow-up "${FOLLOWUPS[$i]}" "$UUID" > "$RESULTS_DIR/followup-$((i+1)).json" 2>/dev/null
    cat "$RESULTS_DIR/followup-$((i+1)).json" | jq '.answer'
done

# Synthesis
echo ""
echo "=== Phase 3: Synthesis ==="
echo "Research complete. Results saved to $RESULTS_DIR/"
echo "Files:"
ls -1 "$RESULTS_DIR/"

echo ""
echo "To upload findings to a Space:"
echo "  bash pplx-upload.sh <space-slug> <file-in-results-dir>"
