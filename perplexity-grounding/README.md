# perplexity-grounding

Grounds agent responses with live Perplexity search — prevents hallucination on version-sensitive APIs, detects stale documentation, and provides token-efficient research workflows.

## What It Does

This plugin extends the pplx system (`/Volumes/ExMac/code/MCP/pplx/`) and works with an existing Perplexity MCP server (e.g. [perplexity-web-wrapper](https://github.com/mrme000m/perplexity-web-wrapper)) to provide intelligent guidance so agents like Claude Code and OpenCode:

- Know **when** to search (version-sensitive APIs, unfamiliar libraries)
- Know **when not** to search (stable patterns, project code)
- Use the right **mode** by default (free `auto` for 90% of queries)
- Use **token-efficient** defaults (`answer_only: true`)
- Get **proactive nudges** when editing dependency files

## Prerequisites

- An active Perplexity MCP server providing `mcp__perplexity__*` tools
- Perplexity account (free tier works for `auto` mode)

## Installation

```bash
# Option 1: Run directly
claude --plugin-dir /path/to/perplexity-grounding

# Option 2: Symlink into plugins
ln -s /path/to/perplexity-grounding ~/.claude/plugins/perplexity-grounding
```

## Components

### Skills (auto-activating)

| Skill | Triggers When |
|-------|---------------|
| `web-grounded-research` | Agent works with external deps/APIs that may be version-sensitive |
| `dependency-intelligence` | Agent needs persistent knowledge about project dependencies |
| `pplx-cli` | MCP server unavailable, batch ops, CI/CD, terminal-based agent |

### Commands (user-invoked)

| Command | Purpose |
|---------|---------|
| `/p-research <query>` | Guided research with auto mode selection |
| `/p-verify-docs <library>` | Verify a dependency's API is current |
| `/p-ground <claim>` | Quick fact-check a specific claim |

### Agents (proactive)

| Agent | Triggers When |
|-------|---------------|
| `stale-doc-detector` | Files with external dependency imports are read/edited |

### Hooks (automatic)

| Hook | Event | Action |
|------|-------|--------|
| `mode-guard` | Before Perplexity search | Ensures mode and token efficiency |
| `freshness-nudge` | After editing files | Suggests verification for dep APIs |
| `dependency-change-alert` | After editing manifests | Suggests checking breaking changes |

## Architecture

```
┌──────────────────────────────────────────────┐
│  Agent (Claude / OpenCode / etc.)            │
│           ↓                                  │
│  ┌─────────────────────────────────┐         │
│  │  perplexity-grounding           │         │
│  │  (skills + hooks + agents)      │         │
│  └──────┬──────────────┬───────────┘         │
│         ↓ guidance       ↓ fallback           │
│  ┌──────────────┐  ┌──────────────┐          │
│  │  MCP Server   │  │  pplx CLI   │          │
│  │  (pww)       │  │  (BWS auth)  │          │
│  └──────┬───────┘  └──────┬───────┘          │
│         ↓                  ↓                  │
│         └────── Perplexity AI ──────────┘     │
└──────────────────────────────────────────────┘
```

This plugin does NOT provide an MCP server. It provides the **intelligence layer** that makes agents use an existing Perplexity MCP server and the `pplx` CLI correctly and efficiently.

## Token Efficiency

The plugin is designed to minimize context window consumption:

- Skills teach `answer_only: true` by default (200-500 token responses)
- Hooks prevent wasteful Pro query usage
- Commands auto-select the cheapest sufficient mode
- Agent uses `haiku` model for scanning + `auto` mode for verification

## License

MIT
