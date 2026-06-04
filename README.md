# PPLX

Perplexity AI command-line interface with **Bitwarden vault authentication** and **dynamic model discovery**.

No cookie files on disk — credentials are pulled directly from your Bitwarden vault at runtime. Models are fetched dynamically from Perplexity's API, so you always see the latest available options.

## Prerequisites

- [Bitwarden CLI](https://bitwarden.com/help/article/cli/) (`bw`)
- A secure note in Bitwarden named exactly `perplexity.ai` containing your Perplexity cookies as JSON

## Installation

```bash
cd /Volumes/ExMac/code/MCP/pplx
pip install -e .
```

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
