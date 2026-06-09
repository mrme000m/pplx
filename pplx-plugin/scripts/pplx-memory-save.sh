#!/bin/bash
# Save a research finding for later retrieval
# Usage: bash pplx-memory-save.sh <key> <value> [--project <name>]
# Example: bash pplx-memory-save.sh "react.19.hooks" "useActionState replaces useFormState" --project myapp
#
# Note: Perplexity memories can only be created through the web UI during conversations.
# This script saves to a local memory file that can be uploaded to a Perplexity Space
# or referenced in your project documentation.

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: bash pplx-memory-save.sh <key> <value> [--project <name>]"
    echo ""
    echo "Examples:"
    echo '  bash pplx-memory-save.sh "lib.nextjs.middleware" "Edge runtime requires compat flag"'
    echo '  bash pplx-memory-save.sh "decision.state-mgmt" "Chose Zustand over Redux" --project myapp'
    echo ""
    echo "Note: Perplexity memories are created via web UI. This script saves to a local"
    echo "      memory file that can be uploaded to a Perplexity Space."
    exit 1
fi

key="$1"
value="$2"
shift 2

project=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)
            project="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build namespaced key if project is provided
if [[ -n "$project" ]]; then
    full_key="${project}.${key}"
else
    full_key="$key"
fi

# Determine memory file location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
MEMORY_DIR="${PPLX_MEMORY_DIR:-$REPO_DIR/.pplx-memories}"
MEMORY_FILE="$MEMORY_DIR/memories.md"

mkdir -p "$MEMORY_DIR"

# Check if memory file exists, create header if not
if [[ ! -f "$MEMORY_FILE" ]]; then
    cat > "$MEMORY_FILE" <<EOF
# PPLX Memory Log

Auto-generated memory log for research findings and decisions.
Upload this file to your Perplexity Space for AI-accessible knowledge.

---

EOF
fi

# Append the memory entry
cat >> "$MEMORY_FILE" <<EOF
## $(date -Iseconds) — $full_key

$value

---

EOF

echo "Memory saved: $full_key"
echo "File: $MEMORY_FILE"
echo ""
echo "To make this available in Perplexity:"
echo "  1. Open https://www.perplexity.ai/settings/memory"
echo "  2. Add: '$full_key = $value'"
echo "  3. Or upload $MEMORY_FILE to your project Space:"
echo "     pplx spaces upload <space-uuid> $MEMORY_FILE"
