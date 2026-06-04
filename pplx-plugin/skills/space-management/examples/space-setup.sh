#!/bin/bash
# Example: Automated Space creation and initial file upload
# Usage: bash space-setup.sh "Project Name" "path/to/docs/dir"

set -euo pipefail

PROJECT_NAME="${1:-My Project}"
DOCS_DIR="${2:-.}"

echo "Creating Space for: $PROJECT_NAME"

# Create Space
SPACE_JSON=$(pplx spaces create --title "$PROJECT_NAME Docs" --description "Documentation for $PROJECT_NAME" 2>/dev/null || echo "failed")
if [ "$SPACE_JSON" = "failed" ]; then
    echo "[FAIL] Could not create Space"
    exit 1
fi

SPACE_UUID=$(echo "$SPACE_JSON" | jq -r '.uuid' 2>/dev/null)
SPACE_SLUG=$(echo "$SPACE_JSON" | jq -r '.slug' 2>/dev/null)

echo "[OK] Space created: $SPACE_SLUG ($SPACE_UUID)"

# Upload markdown files
for f in "$DOCS_DIR"/*.md; do
    [ -f "$f" ] || continue
    FILENAME=$(basename "$f")
    echo "Uploading $FILENAME..."
    bash "${PPLX_PLUGIN_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." >/dev/null 2>&1 && pwd)}/scripts/pplx-upload.sh" "$SPACE_SLUG" "$f"
done

echo ""
echo "Space setup complete: $SPACE_SLUG"
echo "List files: pplx spaces files $SPACE_UUID"
