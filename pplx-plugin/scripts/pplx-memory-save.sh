#!/bin/bash
# Save a research finding to Perplexity memory with project context
# Usage: bash pplx-memory-save.sh <key> <value> [--project <name>]
# Example: bash pplx-memory-save.sh "react.19.hooks" "useActionState replaces useFormState" --project myapp

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: bash pplx-memory-save.sh <key> <value> [--project <name>]"
    echo ""
    echo "Examples:"
    echo "  bash pplx-memory-save.sh \"lib.nextjs.middleware\" \"Edge runtime requires compat flag\""
    echo "  bash pplx-memory-save.sh \"decision.state-mgmt\" \"Chose Zustand over Redux\" --project myapp"
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

# Check pplx CLI
if ! command -v pplx &>/dev/null; then
    echo "Error: pplx CLI not found"
    exit 1
fi

# Save to memory
echo "Saving memory: ${full_key}"
pplx memories add "$full_key" "$value"
echo "Memory saved successfully."
