---
name: space-management
description: This skill should be used when the user asks to "Perplexity Space", "knowledge base", "upload docs", "search in Space", "organize Space", or "project docs Space", or when creating, auditing, searching, or maintaining Perplexity Spaces, uploading project docs, building knowledge bases, or managing Space files, links, or custom skills.
version: 1.1.0
---

# Space Management

Use Perplexity Spaces as durable knowledge bases for projects, dependencies, and research corpora. Spaces provide persistent, project-scoped context that survives compaction and session boundaries.

## Space Design

- One Space per project/domain unless the corpus is very large.
- Use private access by default.
- Include instructions that say when to prefer uploaded files vs web search.
- Upload manifests first, then architecture docs, API specs, schemas, and migration notes.

## Safe Upload Policy

Never upload secrets, cookies, `.env`, vault exports, private keys, or customer data unless the user explicitly confirms and understands the risk.

## Operations

1. **List** Spaces before selecting a target.
2. **Create** Spaces with title, description, instructions, private access, and web default.
3. **Upload** via MCP when available; otherwise use `scripts/pplx-upload.sh`.
4. **Verify** files are READY before relying on them.
5. **Search** with `search_in_space` for project-specific questions.
6. **Audit** stale files, duplicates, failed uploads, and weak instructions.
7. **Delete** only after explicit confirmation.

## Instruction Template

```text
Answer using this Space's uploaded project files first. If uploaded files conflict with current web documentation, call out the conflict and prefer the current source for external dependency APIs. Keep answers concise and cite the file or source basis when possible.
```

## CLI Fallback

```bash
pplx spaces list
pplx spaces create --title "..." --description "..." --instructions "..."
pplx spaces files <uuid>
pplx spaces upload <uuid> <file>
pplx spaces search <uuid> "query"
```

See references/space-patterns.md for naming and audit patterns.
