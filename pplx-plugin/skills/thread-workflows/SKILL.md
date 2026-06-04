---
name: thread-workflows
description: This skill should be used when the user asks to "show my Perplexity threads", "find previous research", "summarize thread", "analyze my threads", or "export Perplexity conversation", or when listing, searching, summarizing, sharing, renaming, deleting, exporting, or analyzing Perplexity threads, finding previous research, preserving backend_uuid values, or extracting decisions and patterns from conversation history.
version: 1.1.0
---

# Thread Workflows

Work with Perplexity thread history in a token-efficient way.

## Retrieval Strategy

1. Start with `list_threads` with a `search_term` to filter by topic.
2. Fetch only likely matches with `get_thread`; do not retrieve all threads at once.
3. Extract durable identifiers from each thread: `slug`, `context UUID`, `backend UUID`, `title`.
4. Summarize findings rather than pasting raw thread JSON into the conversation.
5. Preserve `backend_uuid` values and thread slugs before compaction for follow-up continuity.

## Common Operations

### List Threads
- Use `list_threads` with `limit` (default 10) and optional `search_term`.
- Report total count, thread titles, slugs, and recency.
- For large histories, paginate and present only the most relevant matches.

### Get Thread Details
- Fetch a single thread by its slug with `get_thread`.
- Extract user questions, final answers, sources cited, mode used, and `backend_uuid`.
- Focus on the signal: decisions made, code patterns shared, conclusions reached.

### Summarize Thread
- Present a compact summary: topic, key answers, decisions, sources, and follow-up IDs.
- Do not paste raw conversation text.
- Use the summary template below for consistency.

### Share Thread
- Use `share_thread` to generate a shareable link by slug.
- Return the share URL to the user; do not open it externally.

### Rename / Delete
- Confirm destructive actions (delete, rename) before executing.
- Batch delete supports multiple context UUIDs in a single request.
- The API endpoint is `DELETE /rest/thread` with body `{"entry_uuids":[],"context_uuids":[...],"read_write_token":""}`.
- For single delete: pass one context UUID.
- For batch delete: pass comma-separated UUIDs via CLI (`pplx threads delete <uuid1>,<uuid2> --force`).
- Use CLI fallback for rename/delete when MCP lacks coverage.

## Summary Template

```markdown
## Thread Summary: <title>
- Slug/context: <ids>
- Topic: <topic>
- Key answers: <bullets>
- Decisions/code patterns: <bullets>
- Sources: <short list>
- Follow-up opportunities: <bullets>
```

## Cross-Thread Analysis

For many threads, launch the `thread-analyzer` agent. Compare repeated answers, conflicts, cited sources, and decisions across threads. Present synthesis, not raw data.

## Mode and Token Discipline

- Default to `auto` mode for thread operations (free, fast).
- Use `answer_only: true` for quick verification of thread content.
- Use `answer_only: false` only when sources/citations are explicitly needed.
- Store only `backend_uuid`, slugs, and concise summaries in the conversation — not full thread payloads.

## Compaction Preservation

Before compaction, capture and output:
- Active `backend_uuid` values from recent searches
- Thread slugs that may be referenced in follow-ups
- Chosen model/mode if non-default
- Any research topics or follow-up chains in progress

## CLI Fallback

```bash
pplx threads list --search "topic" --limit 20
pplx threads get <slug>
pplx threads share <slug>
pplx threads delete <uuid1>,<uuid2> --force
bash <plugin>/scripts/pplx-summarize.sh <slug>
```

Ask before destructive operations such as delete or rename. For long histories, process in batches and present only the synthesis.

## Additional Resources

- **`references/thread-patterns.md`** - Detailed thread analysis patterns and edge cases
- **`examples/thread-export.json`** - Example thread export format
