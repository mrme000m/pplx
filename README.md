# PPLX

Perplexity AI command-line interface with **Bitwarden vault authentication** and **dynamic model discovery**.

No cookie files on disk — credentials are pulled directly from your Bitwarden vault at runtime. Models are fetched dynamically from Perplexity's API, so you always see the latest available options.

## Quick Install

### macOS / Linux (one-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/mrme000m/pplx/main/install.sh | bash
```

With options:

```bash
# Custom install directory
curl -fsSL https://raw.githubusercontent.com/mrme000m/pplx/main/install.sh | bash -s -- --dev-dir ~/projects

# Skip plugin installation (CLI only)
curl -fsSL https://raw.githubusercontent.com/mrme000m/pplx/main/install.sh | bash -s -- --skip-plugin

# Install plugin for specific agent only
curl -fsSL https://raw.githubusercontent.com/mrme000m/pplx/main/install.sh | bash -s -- --plugin-for claude
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -Command "Invoke-Expression (Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/mrme000m/pplx/main/install/windows.ps1').Content"
```

With options:

```powershell
# Custom install directory
powershell -ExecutionPolicy Bypass -File install\windows.ps1 -DevDir "C:\projects"

# Skip plugin installation
powershell -ExecutionPolicy Bypass -File install\windows.ps1 -SkipPlugin

# Install plugin for specific agent only
powershell -ExecutionPolicy Bypass -File install\windows.ps1 -PluginFor "claude"
```

### Manual Install

```bash
git clone https://github.com/mrme000m/pplx.git
cd pplx
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -e .
pip install curl-cffi bitwarden-sdk python-dotenv
```

## Prerequisites

- [Bitwarden CLI](https://bitwarden.com/help/article/cli/) (`bw`)
- A secure note in Bitwarden named exactly `perplexity.ai` containing your Perplexity cookies as JSON

## Bitwarden Setup

1. Export your Perplexity cookies to JSON (from browser dev tools)
2. Create a **Secure Note** in Bitwarden named exactly `perplexity.ai`
3. Paste the JSON into the note body:
   ```json
   {
     "__Secure-next-auth.session-token": "...",
     "pplx.session-id": "...",
     "cf_clearance": "..."
   }
   ```

## Usage

```bash
# Basic search (auto mode, free)
pplx search "What is quantum computing?"

# Pro mode with specific model
pplx search "Explain Rust ownership" --mode pro --model "GPT-5.4"

# Pro mode WITH thinking (reasoning variant)
pplx search "Prove sqrt(2) irrational" --mode pro --model "Claude Sonnet 4.6" --thinking

# Reasoning mode (automatically enables thinking)
pplx search "Multi-step logic puzzle" --mode reasoning --model "GPT-5.5"

# Deep research
pplx search "Comprehensive CRISPR analysis" --mode deep_research

# List dynamically discovered models
pplx models

# List models with full details
pplx models -v

# Continue a thread
pplx follow-up "Tell me more" <backend_uuid> --mode pro

# Management
pplx threads list
pplx spaces list
pplx profile
```

## Modes

| Mode | Description | Paid |
|------|------------|------|
| `auto` | Fast, free default | No |
| `pro` | Higher quality with citations | Yes |
| `reasoning` | Step-by-step thinking models | Yes |
| `deep_research` | Multi-page reports | Yes |

## Thinking Mode

Thinking mode is a **toggle**, not just a mode! Any model that supports reasoning can be used in thinking mode:

```bash
# Non-thinking (fast response)
pplx search "Quick fact check" --mode pro --model "GPT-5.4"

# Thinking (step-by-step reasoning)
pplx search "Complex proof" --mode pro --model "GPT-5.4" --thinking
```

Models that support thinking show both standard and thinking variants in `pplx models`.

## Dynamically Discovered Models

PPLX fetches the available model list directly from Perplexity's API on startup (`GET /rest/models/config`). This means:

- You always see the **latest models** — no hardcoded lists
- New models appear automatically
- Model capabilities are fetched from the source of truth

```bash
$ pplx models
Available Models

==================================================

AUTO:
------------------------------
  Default (auto-selected)

PRO:
------------------------------
  • Sonar 2
  • Claude Sonnet 4.6
  • Claude Opus 4.7
  • GPT-5.4
  • GPT-5.5
  • Claude Opus 4.8
  • Kimi K2.6

REASONING:
------------------------------
  • GPT-5.4
  • GPT-5.5
  • Gemini 3.1 Pro
  • Claude Sonnet 4.6
  • Claude Opus 4.8
  • Kimi K2.6
  • Nemotron 3 Super

DEEP RESEARCH:
------------------------------
  Default (auto-selected)
```

## Python API

```python
from pplx import PerplexityClient

client = PerplexityClient()  # Auto-loads cookies from Bitwarden

# List available models
print(client.list_models())

# Search with thinking toggle
result = client.search("Hello world", mode="pro", model="GPT-5.4", thinking=True)
print(result["text"]["answer"])
```

## Agent & IDE Integration

The installer auto-detects and configures the plugin for supported agent harnesses. To install manually:

```bash
# Install plugin for all detected agents
bash install/install-plugin.sh /path/to/pplx/pplx-plugin all

# Or for a specific agent
bash install/install-plugin.sh /path/to/pplx/pplx-plugin claude
bash install/install-plugin.sh /path/to/pplx/pplx-plugin opencode
bash install/install-plugin.sh /path/to/pplx/pplx-plugin codex
```

### Claude Code

**Auto-install:** The installer detects `claude`/`cc` in PATH and symlinks the plugin to the Claude plugins directory.

**Manual:**
```bash
# Load the plugin (commands + skills + agents + hooks)
claude --plugin-dir /path/to/pplx/pplx-plugin

# Or symlink for persistent access
ln -s /path/to/pplx/pplx-plugin ~/.claude/plugins/pplx-plugin
```

**Available commands:**
- `/pplx-research` — Grounded web/Space research with mode guardrails
- `/pplx-orchestrate` — Multi-step research chains with synthesis
- `/pplx-space` — Create, audit, upload to, and search Spaces
- `/pplx-threads` — Search, summarize, share, batch delete threads
- `/pplx-upload` — Safely upload docs/manifests to Spaces
- `/pplx-settings` — Audit account/client/BWS state
- `/pplx-pro-optimizer` — Guide optimal mode selection (auto/pro/reasoning/deep_research)
- `/pplx-persist` — Save findings to memories, create scheduled tasks
- `/pplx-assets` — Track, pin, and download generated assets
- `/pplx-cli-check` — Diagnose local CLI/auth/model discovery
- `/pplx-bws-setup` — Configure/verify BWS SDK cookie auth

**Auto-activating skills:**
- `cli-integration` — MCP unavailable fallback
- `dependency-grounding` — Stale API detection
- `research-deep-dive` — Thorough research workflows
- `space-management` — Knowledge base operations
- `thread-workflows` — Thread history management
- `perplexity-settings` — Account/client audit
- `pro-mode-optimizer` — Cost-aware mode escalation
- `knowledge-persistence` — Durable cross-session knowledge
- `assets-management` — Generated artifact tracking
- `advanced-research-orchestration` — Multi-step research chains

**Hooks (auto-run):**
- `SessionStart` — Readiness check + project Space detection
- `PreToolUse` — Cost guard + Pro mode auto-escalation
- `PostToolUse` — Dependency nudge + memory preservation + asset tracking
- `UserPromptSubmit` — Research intent + Pro feature suggestion
- `Stop` — Research quality gate
- `PreCompact` — Context preservation
- `SessionEnd` — Usage summary

### OpenCode

**Auto-install:** The installer detects `opencode` in PATH and adds the plugin to `skills.paths`.

**Manual:**
Add to your `~/.config/opencode/opencode.json` or project `.opencode/opencode.json`:

```json
{
  "skills": {
    "paths": [
      "/path/to/pplx/pplx-plugin"
    ]
  }
}
```

Commands from `pplx-plugin/commands/` are auto-loaded as slash commands.

### Codex (GitHub)

**Auto-install:** The installer detects `codex` in PATH and links plugin scripts.

**Manual:**
```bash
# In your Codex environment or .codex/config
export PATH="/path/to/pplx/pplx-plugin/scripts:$PATH"
export PPLX_REPO_DIR="/path/to/pplx"
export PPLX_PLUGIN_DIR="/path/to/pplx/pplx-plugin"
```

### Generic Shell-Capable Agent

Any agent that can run shell commands can use:

```bash
# Direct CLI
pplx search "query" --mode auto
pplx spaces list
pplx threads list --search "topic"
pplx memories list --limit 50
pplx tasks list
pplx assets list --limit 20

# Plugin helper scripts
bash /path/to/pplx/pplx-plugin/scripts/pplx-health.sh --verbose --no-search
bash /path/to/pplx/pplx-plugin/scripts/pplx-pro-check.sh --verbose
bash /path/to/pplx/pplx-plugin/scripts/pplx-upload.sh <space> <file>
bash /path/to/pplx/pplx-plugin/scripts/pplx-summarize.sh <thread-slug>
bash /path/to/pplx/pplx-plugin/scripts/pplx-research-chain.sh "query" "follow-up"
bash /path/to/pplx/pplx-plugin/scripts/pplx-memory-save.sh "key" "value" --project myapp
```

## Architecture

```
Bitwarden Vault
    │ secure note: "perplexity.ai"
    │
    ▼
PPLX Client
    │ 1. Loads cookies from Bitwarden
    │ 2. Fetches /rest/models/config dynamically
    │
    ▼
Perplexity API
    │ GET /rest/models/config  →  Available models
    │ GET /api/auth/session    →  Auth verification
    │ POST /rest/sse/perplexity_ask  →  Search queries
```
