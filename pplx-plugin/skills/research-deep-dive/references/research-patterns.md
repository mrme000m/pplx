# Research Patterns

## Query Formulation Techniques

### Tier 1: Quick Fact (most queries)
```
pplx search "React useState return type" --mode auto
```
- Specific, narrow query
- Single concept or API detail
- Mode: auto (free)

### Tier 2: Focused Follow-up
```bash
RESULT=$(pplx search "React 19 useState changes" --mode auto --verbose)
UUID=$(echo "$RESULT" | jq -r '.backend_uuid')
pplx follow-up "What about useEffect?" "$UUID"
```
- Build on previous answer
- Same context, different angle
- Mode: auto unless user requests deeper

### Tier 3: Deep Research (rare)
```
pplx search "Comprehensive comparison of React vs Solid.js performance" --mode deep_research
```
- Multiple sub-topics
- Requires synthesis across sources
- Only when explicitly requested

## Mode Escalation Decision Tree

```
Is this a simple factual question?
├── YES → auto (free)
└── NO → Does it need step-by-step reasoning?
    ├── YES → reasoning
    └── NO → Does it need cited sources and deep analysis?
        ├── YES → pro
        └── NO → Does it need comprehensive multi-topic report?
            ├── YES → deep_research
            └── NO → auto (default)
```

## Cost Optimization

- Always use `answer_only: true` via MCP when sources aren't needed
- Chain follow-ups instead of starting new searches
- Use Space-scoped search when context is known
- Set `incognito: false` to leverage conversation history
- Avoid running the same search multiple times — cache results

## Context-Mode Integration

When processing research results, use `mcp__plugin_context-mode_context-mode__ctx_execute` to extract insights without loading raw search results:

```javascript
// Example: Extract answer and sources from search result
const result = JSON.parse(FS.readFileSync('search-result.json', 'utf8'));
console.log('Answer:', result.answer.substring(0, 300) + '...');
if (result.sources) {
  console.log('Key sources:');
  result.sources.slice(0, 3).forEach(s => console.log(`- ${s.title}: ${s.url}`));
}
```

This pattern is especially valuable for `deep_research` mode, which returns extensive results that would consume significant conversation memory if printed in full.
