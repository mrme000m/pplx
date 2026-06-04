---
name: pplx-settings
aliases: [perplexity-settings, pplx-config, pplx-account]
description: Audit Perplexity account status, credits, rate limits, memories, tasks, workflows, model availability, and plugin configuration
allowed-tools: [Bash]
argument-hint: "status|models|credits|memories|tasks|workflows|rate-limits|ai-profile|health"
---

# /pplx-settings

Audit Perplexity account and client settings using the available `pplx` client surface.

## Preferred CLI Commands

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
bash <plugin>/scripts/pplx-health.sh --verbose --no-search
```

## Workflow

1. Determine the requested settings area.
2. Use the narrowest command; avoid dumping all account data by default.
3. Summarize as a concise table with remediation actions.
4. For destructive actions like memory deletion or task deletion, ask for confirmation.
5. If MCP settings tools are available in the harness, they may be used, but do not assume they exist.

## Audit Output

Include:
- Auth/session health
- Subscription/credits/rate-limit signals if available
- Model discovery status
- Memories/tasks/workflows counts
- Plugin/client path configuration
- Recommended fixes
