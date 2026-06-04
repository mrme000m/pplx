#!/bin/bash
# Scenario-based debug - run predefined debug scenarios
# Usage: debug-scenario.sh [search-flow|space-management|login-flow]

SKILL_DIR="${PERPLEXITY_AUTH_SKILL_DIR:-$HOME/code/MCP/pplx/pplx-plugin/skills/perplexity-auth}"
SCENARIO="${1:-search-flow}"
OUTPUT_DIR="${HOME}/.perplexity-debug/sessions/$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUTPUT_DIR"

echo "=== Debug Scenario: $SCENARIO ==="
echo "Output: $OUTPUT_DIR"

cd "$SKILL_DIR"

case "$SCENARIO" in
    search-flow)
        echo "Running search flow scenario..."
        python3 scripts/diagnostics/health_check.py --full --json > "$OUTPUT_DIR/health.json"
        python3 scripts/traffic/capture_api_calls.py --url "https://www.perplexity.ai" --duration 20 --output "$OUTPUT_DIR/search.har"
        python3 scripts/traffic/analyze_traffic.py "$OUTPUT_DIR/search.har" --json > "$OUTPUT_DIR/endpoints.json"
        ;;

    space-management)
        echo "Running space management scenario..."
        python3 scripts/diagnostics/health_check.py --full --json > "$OUTPUT_DIR/health.json"
        python3 scripts/traffic/capture_api_calls.py --url "https://www.perplexity.ai/spaces" --duration 20 --output "$OUTPUT_DIR/spaces.har"
        python3 scripts/traffic/analyze_traffic.py "$OUTPUT_DIR/spaces.har" --json > "$OUTPUT_DIR/endpoints.json"
        ;;

    login-flow)
        echo "Running login flow scenario..."
        python3 scripts/diagnostics/health_check.py --full --json > "$OUTPUT_DIR/health.json"
        python3 scripts/session/session_status.py --verbose > "$OUTPUT_DIR/session_status.json"
        ;;

    *)
        echo "Unknown scenario: $SCENARIO"
        echo "Available: search-flow, space-management, login-flow"
        exit 1
        ;;
esac

echo ""
echo "=== Scenario complete ==="
echo "Results saved to: $OUTPUT_DIR"