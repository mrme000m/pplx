---
name: dependency-intelligence
version: 1.0.0
description: >
  Uses Perplexity Spaces to build and query persistent knowledge bases about
  project dependencies. Enables agents to maintain grounded, version-accurate
  understanding of libraries and frameworks across sessions.

  Triggers: agent needs persistent knowledge about project dependencies; user
  wants to build a reference library for a framework; project has many external
  dependencies that require version-accurate API knowledge.

keywords: [perplexity, spaces, dependencies, knowledge-base, rag, persistence, packages]
---

# Dependency Intelligence

Use Perplexity Spaces to maintain persistent, grounded knowledge about project dependencies.

## What This Solves

When working with external dependencies, agents often:
- Hallucinate API signatures from outdated training data
- Miss breaking changes between library versions
- Re-search the same information across sessions

Spaces solve this by creating persistent knowledge bases that agents can query instantly.

## Space-Based Workflow

### 1. Create a Project Space

```
mcp__perplexity__create_space(
    title: "project-name-deps",
    description: "Dependency reference for [project]",
    instructions: "Answer questions about library APIs, configurations, and version-specific behavior for this project's dependencies."
)
```

### 2. Upload Grounding Documents

Upload key reference files to ground the Space's knowledge:

- `package.json` / `requirements.txt` / `go.mod` / `Cargo.toml` — exact dependency versions
- `CHANGELOG.md` — recent changes context
- Architecture decision records
- Vendor API documentation excerpts

```
mcp__perplexity__upload_file_to_space(
    collection_uuid: "<space-uuid>",
    filename: "package.json",
    text_content: "<file-contents>"
)
```

### 3. Query for Grounded Answers

When working with a dependency, query the Space first before general web search:

```
mcp__perplexity__search_in_space(
    query: "How does react-hook-form v7 register() work with Zod schema validation?",
    collection_uuid: "<space-uuid>",
    mode: "auto"
)
```

### 4. Maintain Over Time

- Re-upload `package.json` / lock files when dependencies change
- Add new library docs when dependencies are added
- Query the Space when uncertain about an API

## When to Use Spaces vs. Direct Search

| Scenario | Use | Why |
|----------|-----|-----|
| Project-specific dependency question | Space search | Grounded in your exact versions |
| New library evaluation | Direct web search | No Space knowledge yet |
| Quick one-off fact check | Direct web search | Faster, no setup |
| Repeated queries about same library | Space search | Persistent, consistent answers |
| Version compatibility check | Space search + follow-up | Grounded context first |

## Space Discovery

List existing Spaces to find or reuse:
```
mcp__perplexity__list_spaces()
```

Check file status after upload:
```
mcp__perplexity__get_upload_status(collection_uuid: "<uuid>")
```

## Best Practices

1. **One Space per project** — keeps knowledge focused and relevant
2. **Upload version manifests first** — `package.json` grounds all subsequent answers
3. **Use `auto` mode for Space queries** — faster, free, usually sufficient
4. **Re-upload when dependencies change** — keeps knowledge current
5. **Don't upload source code** — only manifests, docs, and API references
