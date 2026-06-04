---
name: pplx-threads
aliases: [perplexity-threads, pplx-thread]
description: Search, retrieve, summarize, share, rename, batch delete, and analyze Perplexity conversation threads
allowed-tools: [perplexity_list_threads, perplexity_get_thread, perplexity_share_thread, Bash, Read]
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
- `delete`: delete one or more threads by context UUID. Accepts comma-separated UUIDs for batch deletion. Confirm each batch before executing. Use `--force` in CLI to skip confirmation.
- `analyze`: cross-thread pattern extraction; use the `thread-analyzer` agent when many threads are involved.

## CLI Fallback

```bash
pplx threads list --search "oauth" --limit 20
pplx threads get <slug>
pplx threads share <slug>
pplx threads rename <context_uuid> "New title"
pplx threads delete <context_uuid_1>,<context_uuid_2> --force
bash <plugin>/scripts/pplx-summarize.sh <slug> [--full]
```

## Delete Workflow

- Single delete: `pplx threads delete <context_uuid>`
- Batch delete: `pplx threads delete <uuid1>,<uuid2>,<uuid3>` (comma-separated, no spaces)
- MCP fallback: the client calls `DELETE /rest/thread` with `{"entry_uuids":[],"context_uuids":[...],"read_write_token":""}` and returns 200 on success
- Always confirm the UUIDs with the user before deletion
- Use `--force` flag to skip interactive confirmation in scripts
