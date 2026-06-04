# CLI Integration Patterns

## Error Handling

```bash
#!/bin/bash
# Retry with exponential backoff
MAX_RETRIES=3
DELAY=2

for i in $(seq 1 $MAX_RETRIES); do
    RESULT=$(pplx search "$QUERY" --raw 2>&1)
    if echo "$RESULT" | jq -e '.answer' > /dev/null 2>&1; then
        echo "$RESULT" | jq '.answer'
        exit 0
    fi
    sleep $((DELAY * i))
done
echo "Search failed after $MAX_RETRIES attempts" >&2
exit 1
```

## Batch Search

```bash
# Search multiple queries in parallel
queries=("query1" "query2" "query3")
for q in "${queries[@]}"; do
    pplx search "$q" &
done
wait
```

## Bitwarden Authentication Check

```bash
# Verify Bitwarden connectivity and Perplexity session
bw status 2>/dev/null | jq -e '.status == "unlocked"' > /dev/null
if [ $? -ne 0 ]; then
    echo "Bitwarden not unlocked. Run: bw unlock" >&2
    exit 1
fi

# Verify Perplexity cookies exist
bw get item "perplexity.ai" 2>/dev/null | jq -e '.notes' > /dev/null
if [ $? -ne 0 ]; then
    echo "No 'perplexity.ai' note in Bitwarden. See README for setup." >&2
    exit 1
fi
```

## Context-Mode Integration

When processing CLI search results in agents that support tool-augmented execution, pipe results through a lightweight processor to keep raw output out of conversation:

```javascript
// Example: Process batch search results
const fs = require('fs');
const results = ['query1', 'query2', 'query3'].map(q => {
  try { return JSON.parse(fs.readFileSync(`results/${q}.json`, 'utf8')); }
  catch { return null; }
}).filter(Boolean);

const answers = results.map(r => r.answer?.substring(0, 150) || '(no answer)');
console.log(`Processed ${answers.length} searches:`);
answers.forEach((a, i) => console.log(`${i+1}. ${a}...`));
```

This is especially useful for batch searches where the combined output would be large.
