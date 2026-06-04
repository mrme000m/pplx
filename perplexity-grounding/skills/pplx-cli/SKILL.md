---
name: pplx-cli
version: 1.0.0
description: >
  Direct access to the pplx CLI for Perplexity AI operations outside of MCP.
  Use when the MCP server is unavailable or when running operations that benefit
  from CLI control (batch file uploads, scripted searches, CI integration).

  Triggers: MCP server is down or unavailable; user asks for CLI-based search;
  batch operations on Spaces; CI/CD integration for dependency verification.

keywords: [pplx, cli, terminal, batch, scripting, fallback, perplexity]
---

# PPLX CLI Access

The `pplx` CLI provides direct Perplexity access when MCP tools are unavailable or for scripted workflows.

## Setup

The pplx CLI is installed from `/Volumes/ExMac/code/MCP/pplx/` with Bitwarden-backed authentication:

```bash
cd /Volumes/ExMac/code/MCP/pplx
pip install -e .
```

Authentication uses Bitwarden Secrets Manager — no manual cookie management needed.

## Core Commands

### Search
```bash
pplx search "query text"                    # Auto mode (free)
pplx search "query" --mode pro              # Pro mode
pplx search "query" --mode deep_research    # Deep research
pplx search "query" --raw                   # Full JSON output
pplx search "query" --model "Claude Sonnet 4.6"  # Specific model
```

### Follow-up
```bash
pplx follow-up "follow-up query" <backend_uuid>
```

### Models
```bash
pplx models              # List available models
pplx models --raw        # Raw JSON
pplx models -v           # Full details
```

### Spaces
```bash
pplx spaces list
pplx spaces get <slug>
pplx spaces create --title "Name" --description "Desc"
pplx spaces edit <uuid> --title "New Name"
pplx spaces delete <uuid> --force
pplx spaces threads <slug>
pplx spaces files <uuid>
pplx spaces upload <uuid> <file>
```

### Threads
```bash
pplx threads list
pplx threads list --search "keyword"
pplx threads get <slug>
pplx threads recent
pplx threads pinned
```

### Other
```bash
pplx discover                     # Trending articles
pplx profile                      # User profile
```

## When to Use CLI vs MCP

| Scenario | Use CLI | Use MCP |
|----------|---------|---------|
| Agent is in Claude Code | | MCP tools |
| Agent is in terminal/OpenCode | CLI | |
| Batch file uploads | CLI | |
| CI/CD integration | CLI | |
| MCP server is down | CLI (fallback) | |
| Interactive agent session | | MCP tools |
| Scripted dependency scanning | CLI | |

## Output Parsing

The CLI outputs either human-readable text (default) or JSON (`--raw` flag).

For agent consumption, always use `--raw` to get parseable JSON:
```bash
pplx search "query" --raw | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['text'])"
```
