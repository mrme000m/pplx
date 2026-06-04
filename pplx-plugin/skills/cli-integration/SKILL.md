---
name: cli-integration
description: This skill should be used when the user asks to "use pplx CLI", "run Perplexity from shell", "MCP is down", "OpenCode Perplexity", "Codex Perplexity", "batch upload to Space", "check Perplexity auth", "BWS cookies", or when Perplexity access is needed through shell commands, non-Claude harnesses, or BWS cookie diagnostics.
version: 1.1.0
---

# PPLX CLI Integration

Use the `pplx` client as the universal fallback for Claude Code, OpenCode, Codex, and any harness that can run shell commands. The CLI provides search, follow-up, Spaces, threads, and model discovery when MCP tools are unavailable.

## Resolution Order

1. Use Perplexity MCP tools when available in the agent harness (Claude Code, OpenCode, Codex).
2. Use `pplx` executable if it is on `PATH`.
3. Use plugin helper scripts; they can run the local Python client by setting `PPLX_REPO_DIR`.
4. If none work, run `scripts/pplx-setup.sh --print-env` and follow remediation.

## Cookie/Auth Resolution

The client loads valid Perplexity cookies in this order:

1. `PERPLEXITY_COOKIES_PATH=/path/to/cookies.json` for explicit local override.
2. **Preferred:** Bitwarden Secrets Manager through `bitwarden-sdk` using `BWS_ACCESS_TOKEN`, project `pplx`, secret key `perplexity-cookies`.
3. Legacy Bitwarden vault fallback via `bw` CLI Secure Note named `perplexity.ai`.

For BWS setup from the pplx client checkout:

```bash
python scripts/setup_bws_secret.py create-token
python scripts/setup_bws_secret.py setup-cookies /path/to/cookies.json
python scripts/setup_bws_secret.py show
```

## Portable Helpers

The plugin scripts resolve paths relative to themselves. Avoid hardcoded marketplace or development paths.

```bash
bash <plugin>/scripts/pplx-health.sh --verbose --no-search
bash <plugin>/scripts/pplx-setup.sh --print-env
bash <plugin>/scripts/pplx-upload.sh <space-slug-or-uuid> <file> [--by-uuid]
bash <plugin>/scripts/pplx-summarize.sh <thread-slug> [--full]
```

## Core Commands

```bash
pplx search "query" --mode auto
pplx search "query" --mode pro --raw
pplx follow-up "question" <backend_uuid>
pplx models --raw
pplx spaces list
pplx spaces search <space-uuid> "query" --mode auto
pplx threads list --search "topic"
pplx status --raw
```

## Cost and Token Rules

- Default to `auto`.
- Use paid modes only when requested or clearly justified.
- Use `--raw` only when machine parsing is needed.
- Do not run live searches in startup checks.
- Store only `backend_uuid`, slugs, and concise summaries in the conversation.

## Authentication Guidance

Prefer BWS SDK because it avoids unlocked desktop vault state and provides service-account scoped secret access. Use legacy `bw` only as a fallback. Run `pplx-health.sh` to verify `bitwarden_sdk`, `BWS_ACCESS_TOKEN`, the `perplexity-cookies` secret, and actual cookie loading.
