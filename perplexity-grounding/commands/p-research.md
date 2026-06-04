---
name: p-research
aliases: [perplexity-research, pplx-research]
description: Guided research with auto mode selection — search the web via Perplexity with intelligent defaults
allowed-tools: [mcp__perplexity__search, mcp__perplexity__follow_up, mcp__perplexity__list_spaces, mcp__perplexity__search_in_space]
---

# /p-research — Guided Perplexity Research

Execute a research query against Perplexity AI with automatic mode selection and token-efficient defaults.

## Instructions

Parse the user's arguments as the research query. Then execute this workflow:

### Step 1: Determine Mode

Evaluate the query complexity and select mode:

| Signal | Mode | Rationale |
|--------|------|-----------|
| Single fact, definition, quick check | `auto` | Free, fast, sufficient |
| User says "research", "deep", "thorough", "comprehensive" | `pro` | Deeper analysis needed |
| User says "reason", "think through", "step by step" | `reasoning` | Chain-of-thought required |
| User says "deep research", "exhaustive", "report" | `deep_research` | Comprehensive report needed |

**Default to `auto`** unless the user's language explicitly signals a deeper need.

### Step 2: Check for Space Context

If the query relates to a specific project's dependencies:
1. List spaces with `mcp__perplexity__list_spaces()`
2. Look for a Space matching the project name
3. If found, use `mcp__perplexity__search_in_space()` instead of general search
4. If not found, proceed with general search

### Step 3: Execute Search

```
mcp__perplexity__search(
    query: "<user's query with version/library specificity added if missing>",
    mode: "<selected mode>",
    answer_only: true,
    language: "en-US"
)
```

**Query enhancement**: If the user's query is vague (e.g. "how to use react hooks"), add specificity from the project context (e.g. "React 19 hooks API useActionState useEffect cleanup").

### Step 4: Present Results

Present the answer concisely:
- State the grounded answer
- If the answer changes the agent's prior assumption, note the correction
- Save `backend_uuid` for potential follow-up

### Step 5: Offer Follow-up

If the answer is incomplete or the user might want more detail, mention that follow-up is available with the saved `backend_uuid`.

## Examples

```
/p-research What is the latest Next.js App Router dynamic segment syntax?
/p-research How does Tailwind CSS v4 handle @apply in component styles?
/p-research deep research: compare React Server Components vs Next.js SSR tradeoffs
```
