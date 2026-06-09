#!/bin/bash
# Run a multi-step Perplexity research chain with follow-ups
# Usage: bash pplx-research-chain.sh "initial query" ["follow-up 1"] ["follow-up 2"] ...
# Example: bash pplx-research-chain.sh "React 19 overview" "breaking changes" "migration guide"

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: bash pplx-research-chain.sh \"initial query\" [\"follow-up 1\"] [\"follow-up 2\"] ..."
    echo ""
    echo "Example:"
    echo '  bash pplx-research-chain.sh "React 19 new features" "server components changes" "use hook API"'
    exit 1
fi

# Check dependencies
if ! command -v pplx &>/dev/null; then
    echo "Error: pplx CLI not found"
    exit 1
fi

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required for JSON parsing"
    echo "Install: brew install jq  (macOS)  or  apt-get install jq  (Linux)"
    exit 1
fi

initial_query="$1"
shift

echo "=== Research Chain ==="
echo ""
echo "Step 1: Initial search"
echo "Query: ${initial_query}"
echo ""

# Run initial search and capture backend_uuid
result=$(pplx search "$initial_query" --mode auto --raw)
uuid=$(echo "$result" | jq -r '.backend_uuid // empty')

if [[ -z "$uuid" ]]; then
    echo "Error: Could not get backend_uuid from initial search"
    exit 1
fi

echo "backend_uuid: ${uuid}"
echo ""

# Print answer
echo "$result" | jq -r '.text // .answer // "(no answer)"' 2>/dev/null || echo "$result"
echo ""

# Process follow-ups
step=2
for follow_up in "$@"; do
    echo "Step ${step}: Follow-up"
    echo "Query: ${follow_up}"
    echo ""

    result=$(pplx follow-up "$follow_up" "$uuid" --raw)
    new_uuid=$(echo "$result" | jq -r '.backend_uuid // empty')

    if [[ -n "$new_uuid" ]]; then
        uuid="$new_uuid"
        echo "backend_uuid: ${uuid}"
    fi

    echo "$result" | jq -r '.text // .answer // "(no answer)"' 2>/dev/null || echo "$result"
    echo ""

    ((step++)) || true
done

echo "=== Research Chain Complete ==="
echo "Final backend_uuid: ${uuid}"
echo ""
echo "Save to memory: pplx memories add \"research.topic\" \"Findings summary\""
