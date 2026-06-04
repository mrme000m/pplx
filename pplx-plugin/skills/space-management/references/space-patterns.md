# Space Management Patterns

## Naming Conventions

- Use project-scoped names: `my-project-docs`, `api-reference-v2`
- Include version in name if managing multiple versions
- Avoid generic names like `docs` or `my-stuff`

## Instruction Templates

### Project Documentation Space
```
This Space contains documentation for {project_name}.
When answering questions, ground responses in uploaded files.
Prioritize information from files over web search.
If a file seems stale, flag it for review.
```

### API Reference Space
```
This Space contains API documentation for {service_name}.
When answering API usage questions, reference the uploaded specs.
If an API endpoint is not found in the files, search the web.
Always note which version of the API the documentation covers.
```

### Research Corpus Space
```
This Space contains research notes and findings about {topic}.
Use this knowledge base as the primary source for queries about {topic}.
When new information is discovered, suggest uploading it here.
```

## Access Control

- Private (access: 1) — default for project documentation
- Public (access: 2) — only for shared team knowledge bases
- Never expose sensitive information (credentials, internal data)

## File Organization

- Upload one logical document per file
- Use descriptive filenames: `api-auth-endpoints.md`, not `doc1.md`
- Group related files with prefixes: `schema-users.json`, `schema-orders.json`
- Maximum file size: check Perplexity docs for current limits

## Context-Mode Integration

When working with large file lists or search results, use `mcp__plugin_context-mode_context-mode__ctx_execute` to process data without loading raw JSON into conversation:

```javascript
// Example: Summarize Space files without printing full list
const files = JSON.parse(FS.readFileSync('space-files.json', 'utf8'));
const ready = files.filter(f => f.status === 'READY');
const stale = files.filter(f => f.name.includes('v1') || f.name.includes('old'));
console.log(`${ready.length} files ready, ${stale.length} potentially stale`);
stale.forEach(f => console.log(`- ${f.name} (uploaded: ${f.updated})`));
```

This pattern keeps the raw file list out of conversation memory — only the summary enters context.
