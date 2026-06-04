# Thread Analysis Patterns

## Conversation Summarization Template

```markdown
## Thread: {title}
**Date:** {created_at}
**Mode:** {auto|pro|reasoning|deep_research}

### Summary
{2-3 sentence overview}

### Key Decisions
- {decision 1}
- {decision 2}

### Code Patterns
```
{relevant code snippet}
```

### Action Items
- [ ] {item}
```

## Cross-Thread Correlation

1. Search threads with topic-specific keywords
2. For each matching thread, extract:
   - User questions (intent)
   - Assistant answers (solution)
   - Code patterns used
3. Build a matrix: topic → solutions → frequency
4. Identify the most common solution per topic

## Thread Cleanup

- Delete threads with `mcp__perplexity__list_computer_tasks` that are stale
- Rename threads with descriptive titles using `mcp__perplexity__share_thread`
- Pin important threads for quick access
- Export valuable threads to Spaces before deletion

## Context-Mode Integration

When analyzing multiple threads, use `mcp__plugin_context-mode_context-mode__ctx_execute` to process thread content efficiently:

```javascript
// Example: Extract key decisions from a thread without printing full conversation
const thread = JSON.parse(FS.readFileSync('thread.json', 'utf8'));
const decisions = thread.messages
  .filter(m => m.role === 'assistant' && m.content.includes('recommend'))
  .map(m => m.content.substring(0, 200));
console.log(`Found ${decisions.length} recommendations:`);
decisions.forEach((d, i) => console.log(`${i+1}. ${d}...`));
```

This keeps the full thread content out of conversation memory — only extracted insights enter context.
