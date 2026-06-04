---
name: pplx-space
aliases: [perplexity-space, pplx-spaces]
description: Manage Perplexity Spaces for project knowledge bases, dependency grounding, files, links, skills, and scoped research
allowed-tools: [perplexity_list_spaces, perplexity_get_space, perplexity_create_space, perplexity_edit_space, perplexity_delete_space, perplexity_upload_file_to_space, perplexity_list_space_files, perplexity_delete_space_files, perplexity_get_upload_status, perplexity_list_space_threads, perplexity_search_in_space, Bash, Read]
argument-hint: "list|create|upload|files|search|links|skills|audit"
---

# /pplx-space

Operate Perplexity Spaces as persistent, project-scoped knowledge bases.

## Operations

- **list**: show available Spaces with title, slug, UUID, owner/shared status, and last activity.
- **create**: ask for title, description, instructions, access level, and web-search default. Default to private.
- **upload**: upload local files or selected context. Prefer MCP upload; fall back to `scripts/pplx-upload.sh`.
- **files**: list Space files, status, failed uploads, and stale candidates.
- **search**: run scoped search against a Space before broad web search.
- **links**: manage focused web links/domains through the CLI when MCP lacks coverage.
- **skills**: upload or audit Space custom skills through the CLI when needed.
- **audit**: inspect instructions, files, duplicate docs, failed uploads, and whether manifests are current.

## Best Practices

1. One primary Space per project or domain.
2. Upload dependency manifests before API docs so answers are version-grounded.
3. Use clear instructions: tell Perplexity when to prefer uploaded files and when to use web.
4. Verify upload status before relying on new files.
5. Do not upload secrets, `.env`, private keys, or credential exports.

## CLI Fallback

```bash
pplx spaces list
pplx spaces get <slug>
pplx spaces create --title "Project Docs" --description "..." --instructions "..."
pplx spaces upload <space-uuid> <file>
pplx spaces search <space-uuid> "query" --mode auto
bash <plugin>/scripts/pplx-upload.sh <space-slug-or-uuid> <file> [--by-uuid]
```

Always confirm before deleting Spaces or files.
