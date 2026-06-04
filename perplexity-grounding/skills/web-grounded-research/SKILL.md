---
name: web-grounded-research
version: 1.0.0
description: >
  Teaches agents when and how to use Perplexity MCP tools to ground responses
  in current, verified information. Prevents hallucination on version-sensitive
  APIs, recent library changes, and unfamiliar frameworks.

  Triggers: agent is working with external dependencies, APIs, or libraries it
  may have stale knowledge about; user asks about recent changes, current versions,
  or latest documentation; agent needs to verify a code pattern against real docs.

keywords: [perplexity, grounding, hallucination, verification, search, research, docs, api, version]
---

# Web-Grounded Research

Ground agent responses with live web search to prevent hallucination and stale-knowledge errors.

## When to Search

Search Perplexity when the task involves ANY of:

1. **Version-sensitive APIs** — method signatures, parameters, or return types that change across library versions (e.g. React 19 vs 18 hooks, Next.js App Router vs Pages, Tailwind v4 vs v3)
2. **Recent changes** — deprecations, breaking changes, new features released after training cutoff
3. **Unfamiliar libraries** — any package the agent has not seen in the current project's codebase before
4. **Error diagnosis** — error messages or stack traces referencing external package internals
5. **Configuration syntax** — framework config files (next.config, tailwind.config, tsconfig) where options change between versions
6. **User explicitly asks** for current/latest/up-to-date information

## When NOT to Search

Skip Perplexity for:
- Standard language features (Python `for` loops, JS `Array.map`, Go `goroutines`)
- Project-specific code already in the codebase (read it directly instead)
- Well-known stable patterns that haven't changed in years
- Subjective or opinion-based questions

## Token-Efficient Search Patterns

### Tier 1: Quick Fact (most searches)

Use `mcp__perplexity__search` with these defaults:

```
mode: "auto"
answer_only: true
```

Returns `{answer, backend_uuid}` — typically 200-500 tokens. Use this for 90% of searches.

### Tier 2: Focused Follow-up

When the first answer is incomplete, use `mcp__perplexity__follow_up` with `backend_uuid` from the previous response. This keeps the conversation context and avoids re-stating the full question.

### Tier 3: Deep Research (rare)

Only use `mode: "pro"` or `mode: "deep_research"` when:
- User explicitly requests thorough research
- Migration between major library versions
- Comparing multiple competing approaches
- Building a comprehensive technical document

## Search Query Formulation

Write queries that return precise answers:

| Bad | Good | Why |
|-----|------|-----|
| "how to use react" | "React 19 useActionState API signature and return type" | Specific version + specific API |
| "next.js routing" | "Next.js 15 App Router dynamic route params type signature" | Version + feature + detail |
| "tailwind error" | "Tailwind CSS v4 @apply directive not working in CSS modules" | Version + symptom + context |

**Pattern**: `[library] [version] [specific feature/API] [question focus]`

## Grounding Workflow

When an agent identifies a grounding need:

1. **Identify the gap** — what specific fact/version/pattern is uncertain
2. **Formulate a precise query** — include library name, version if known, specific API
3. **Search with `auto` mode, `answer_only: true`** — minimize token cost
4. **Validate the answer** — does it directly address the gap? If not, follow up
5. **Apply the grounded knowledge** — write code using the verified information
6. **Cite the source** — include a brief comment noting the verified fact (optional)

## Anti-Patterns to Avoid

- **Do not** search for every import or function call — only when uncertainty exists
- **Do not** use `pro` mode for simple factual lookups — wastes Pro queries
- **Do not** return raw search results to the user — synthesize the answer
- **Do not** search when the answer is in the project's own codebase — read the file instead
- **Do not** use `deep_research` unless the user explicitly asks — it is slow and expensive

## Cost Awareness

| Mode | Cost | Typical Response |
|------|------|-----------------|
| `auto` | Free | 200-500 tokens |
| `pro` | 1 Pro query | 500-1500 tokens |
| `reasoning` | 1 Pro query | 500-2000 tokens |
| `deep_research` | Multiple Pro queries | 2000+ tokens |

Default to `auto`. Escalate only on explicit user request.
