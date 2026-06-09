---
name: perplexity-settings
description: |
  This skill should be used when the user asks to "Perplexity settings", "pplx status", "credits", "rate limits", "memories", "workflows", "models", "auth check", "BWS_ACCESS_TOKEN", "perplexity-cookies", or when auditing Perplexity account/client state, BWS cookie loading, dynamic models, or plugin setup.
  Also trigger when the user asks about their Perplexity account, subscription status, available AI models, or needs to verify their authentication and cookie configuration.
version: 1.1.0
---

# Perplexity Settings

Audit account and client state through the actual `pplx` client commands available in this repository.

## Auth/Cookie Model

Cookie loading order:

1. `PERPLEXITY_COOKIES_PATH` JSON file override.
2. **Preferred:** Bitwarden Secrets Manager using `bitwarden-sdk`, `BWS_ACCESS_TOKEN`, project `pplx`, secret `perplexity-cookies`.
3. Legacy `bw` CLI Secure Note named `perplexity.ai`.

For BWS setup:

```bash
python scripts/setup_bws_secret.py create-token
python scripts/setup_bws_secret.py setup-cookies /path/to/cookies.json
python scripts/setup_bws_secret.py show
```

## Narrow Commands

Use the narrowest command for the requested area:

```bash
pplx status --raw
pplx models --raw
pplx credits
pplx rate-limits --raw
pplx settings
pplx memories list --limit 50
pplx tasks list
pplx workflows
pplx ai-profile --raw
```

## Health Diagnostics

```bash
bash <plugin>/scripts/pplx-health.sh --verbose --no-search
```

Run live search diagnostics only when the user asks or auth/connectivity must be verified.

## Reporting

Summarize, do not dump raw JSON. Include:
- auth/client status
- BWS token/secret presence, without exposing secret values
- dynamic model discovery state
- rate/credit signals
- memory/task/workflow counts
- recommended cleanup or setup actions

Ask before deleting memories, tasks, Spaces, or files.

## Example Audit Workflow

**Quick health check (no live search):**
```bash
bash <plugin>/scripts/pplx-health.sh --verbose --no-search
```

**Check all account state:**
```bash
pplx status --raw
pplx models --raw
pplx rate-limits --raw
pplx credits
```

**Review and clean up memories:**
```bash
pplx memories list --limit 50
# Ask before deleting: pplx memories delete <key>
```

## Space Audit Notes

When auditing Spaces, check `user_permission`:

| Permission | Meaning | Action |
|-----------|---------|--------|
| `4` | User-owned Space | Safe to delete via API |
| `6` | System-managed Space (e.g. Bookmarks) | Cannot delete via API — skip during cleanup |

System Spaces include the built-in **Bookmarks** space (`bookmarks-*` slug), which
aggregates all saved/bookmarked threads and files from across Perplexity. It has
`user_permission: 6` and the API returns 400 on DELETE attempts. The Space itself
is Perplexity-managed, but users can freely add/remove individual threads inside it
to manage what's bookmarked. Delete the Space container via the web UI only.
