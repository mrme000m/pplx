---
name: pplx-threads
aliases: [perplexity-threads, pplx-thread]
description: Search, retrieve, summarize, share, rename, and analyze Perplexity conversation threads
allowed-tools: [perplexity_list_threads, perplexity_get_thread, perplexity_share_thread, Bash]
argument-hint: "list|get|summarize|share|rename|delete|analyze"
---

# /pplx-threads

Work with Perplexity thread history without flooding the context window.

## Workflow

1. Use `list_threads` with a `search_term` before fetching full thread details.
2. Fetch only the relevant thread(s) with `get_thread`.
3. Extract user questions, final answers, sources, mode, and durable IDs.
4. Summarize in a compact format instead of pasting raw payloads.
5. Preserve `backend_uuid`, thread slug, and context UUID for follow-ups.

## Operations

- `list`: recent threads, optionally filtered.
- `get`: exact thread detail by slug.
- `summarize`: concise summary with decisions, code patterns, and sources.
- `share`: create/share a thread link when supported.
- `rename` / `delete`: use CLI fallback and confirm destructive actions first.
- `analyze`: cross-thread pattern extraction; use the `thread-analyzer` agent when many threads are involved.

## CLI Fallback

```bash
pplx threads list --search "oauth" --limit 20
pplx threads get <slug>
pplx threads share <slug>
pplx threads rename <context_uuid> "New title"
pplx threads delete <context_uuid> --force
bash <plugin>/scripts/pplx-summarize.sh <slug> [--full]
```

For long histories, process in batches and present only the synthesis.
