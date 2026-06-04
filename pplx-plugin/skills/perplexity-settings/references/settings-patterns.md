# Settings Management Patterns

## Shortcut Naming Conventions

- Use kebab-case: `verify-api-docs`, `check-latest-version`
- Prefix with purpose: `dev-`, `research-`, `review-`
- Include the action: `verify-`, `find-`, `compare-`

## Recommended Shortcuts

| Name | Prompt | Mode |
|------|--------|------|
| `verify-api-doc` | "Verify that {library} API patterns are current and not deprecated. Check the latest official documentation." | auto |
| `find-breaking-changes` | "Find any breaking changes in {library} between {old_version} and {new_version}." | pro |
| `research-best-practice` | "Research current best practices for {topic}. Include source citations." | pro |

## Memory Management

- Delete memories that are project-specific and no longer active
- Keep memories concise — each one costs tokens on every conversation
- Use specific memory_key names: `tools.perplexity_auth`, not `note1`
- Periodically audit with `list_memories` and remove duplicates

## Personalization Settings

- `enable_web_by_default: true` — if most queries need current information
- `default_mode: auto` — to avoid accidental paid query usage
- Review periodically — Perplexity adds new settings over time

## Context-Mode Integration

When auditing large shortcut or memory lists, use `mcp__plugin_context-mode_context-mode__ctx_execute` to produce summary tables without loading raw JSON:

```javascript
// Example: Audit shortcuts and memories in one pass
const shortcuts = JSON.parse(FS.readFileSync('shortcuts.json', 'utf8'));
const memories = JSON.parse(FS.readFileSync('memories.json', 'utf8'));

console.log(`Shortcuts: ${shortcuts.length}`);
console.log('  auto:', shortcuts.filter(s => s.mode === 'auto').length);
console.log('  pro:', shortcuts.filter(s => s.mode === 'pro').length);
console.log('  deep_research:', shortcuts.filter(s => s.mode === 'deep_research').length);
console.log(`\nMemories: ${memories.length}`);
const stale = memories.filter(m => m.key.includes('old') || m.key.includes('deprecated'));
if (stale.length > 0) {
  console.log(`  Potentially stale: ${stale.length}`);
  stale.forEach(m => console.log(`    - ${m.key}`));
}
```

This keeps the full shortcut/memory lists out of conversation memory.
