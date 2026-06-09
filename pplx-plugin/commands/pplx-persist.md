---
name: pplx-persist
aliases: [perplexity-persist, pplx-memory, pplx-tasks, pplx-save]
description: Save research findings to Perplexity memories, create scheduled tasks for recurring checks, and manage persistent knowledge across sessions
allowed-tools: [Bash, Read, perplexity_list_memories, perplexity_get_memory, perplexity_delete_memory, perplexity_list_computer_tasks, perplexity_list_workflows]
argument-hint: "memory|task|workflow|list-memories|list-tasks"
---

# /pplx-persist

Create durable knowledge that survives session boundaries using Perplexity memories, scheduled tasks, and workflows.

## Sub-commands

### memory <key> <value>
Save a key-value memory to Perplexity.

```bash
pplx memories add "project.auth.decision" "Using OAuth2 + PKCE for mobile app"
```

### task <name> <prompt> --schedule <rrule>
Create a scheduled recurring research task.

```bash
pplx tasks create "weekly-security" \
  "Check for critical security advisories in React ecosystem" \
  --start-at "2025-06-16T09:00:00Z" \
  --rrule "FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0" \
  --tzid "America/New_York"
```

### workflow
List available Perplexity workflow templates.

```bash
pplx workflows
```

### list-memories
List saved memories with optional search.

```bash
pplx memories list --limit 50
pplx memories list --search "react"
```

### list-tasks
List scheduled tasks.

```bash
pplx tasks list
pplx tasks recurring
```

## Memory Key Conventions

Use dot-notation for organization:

```
project.{name}.{topic}       → project.api.rate-limiting
lib.{name}.{version}.{topic} → lib.nextjs.14.middleware
decision.{date}.{topic}      → decision.2025-06.vite-migration
workaround.{issue}           → workaround.webpack-cjs-interop
session.{date}.topic         → session.2025-06-09.react-rsc
```

## When to Persist

**Save to memory:**
- Non-obvious workarounds or gotchas
- Version-specific behavior
- Decision rationale
- Project configuration requirements

**Create scheduled tasks:**
- Weekly dependency security checks
- Monthly framework version monitoring
- Quarterly API deprecation audits

## Safety

- Ask before deleting memories or tasks
- Never save secrets in Perplexity memories
- Review scheduled tasks quarterly
