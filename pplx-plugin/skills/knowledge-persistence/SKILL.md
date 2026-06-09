---
name: knowledge-persistence
description: |
  This skill should be used when the user wants to save research findings for future sessions, set up recurring research tasks, manage Perplexity memories, workflows, or scheduled tasks, or when durable knowledge that survives session boundaries is needed. Also trigger when users mention "remember this", "save for later", "recurring check", "monitor", or "keep track of" in the context of Perplexity research.
version: 1.0.0
---

# Knowledge Persistence

Use Perplexity's persistent features — memories, scheduled tasks, and workflows — to create durable knowledge that survives session boundaries, compaction, and agent restarts.

## Feature Overview

| Feature | Purpose | Persistence | Best For |
|---------|---------|-------------|----------|
| **Memories** | Key-value facts | Cross-session | Technical decisions, version notes, workarounds |
| **Scheduled Tasks** | Recurring searches | Until deleted | Dependency monitoring, security alerts, trend tracking |
| **Workflows** | Pre-built templates | Account-level | Common research patterns, report generation |
| **Spaces** | Project knowledge bases | Until deleted | Documentation, API specs, architecture |

## Memories

### When to Save

Save a memory when you discover:
- Non-obvious workaround or gotcha
- Version-specific behavior that will recur
- Decision rationale (why X over Y)
- Project-specific configuration requirements
- Breaking change patterns for tracked dependencies

### Memory Key Naming

Use dot-notation namespaces for organization:

```
project.{name}.{topic}       → project.api.auth-flow
lib.{name}.{version}.{topic} → lib.react.19.hooks
decision.{date}.{topic}      → decision.2025-06.migration-to-vite
workaround.{issue}           → workaround.webpack-esm-hybrid
```

### Commands

```bash
# Save a finding
pplx memories add "lib.nextjs.14.middleware" "Edge middleware requires Node.js compat flag for certain packages"

# List memories
pplx memories list --limit 50
pplx memories list --search "nextjs"

# Retrieve
pplx memories get "lib.nextjs.14.middleware"

# Delete (ask first)
pplx memories delete "lib.nextjs.14.middleware"
```

## Scheduled Tasks

### When to Create

Create a scheduled task for:
- Weekly dependency security checks
- Monthly framework version monitoring
- Quarterly API deprecation audits
- Daily market/metric monitoring (finance alerts)

### Task Design

Keep prompts specific and scoped:

```bash
# Good: Specific, actionable, scoped
pplx tasks create "weekly-security-check" \
  "Check npm audit for critical vulnerabilities in React ecosystem" \
  --start-at "2025-06-15T09:00:00Z" \
  --rrule "FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0" \
  --tzid "America/New_York"

# Bad: Vague, unbounded
pplx tasks create "check-stuff" "Check things" --start-at "now" --rrule "FREQ=DAILY"
```

### Finance Alerts

For price/metric monitoring:

```bash
pplx finance alert "crypto-monitor" BTC --threshold 70000 \
  --prompt "Alert when Bitcoin crosses $70k"
```

### Managing Tasks

```bash
pplx tasks list
pplx tasks recurring
pplx tasks delete "task-id"
```

## Workflows

### Discovery

```bash
pplx workflows
```

Use workflows as starting templates for common research patterns. They provide structured prompts that can be customized.

## Integration with Coding Workflows

### Dependency Monitoring Pipeline

1. Save initial dependency versions to memory:
   ```bash
   pplx memories add "project.deps.versions" "React 18.3, Next.js 14.2, Node 20.12"
   ```

2. Create weekly task to check for major version announcements:
   ```bash
   pplx tasks create "deps-major-check" \
     "Any major version releases for React, Next.js, or Node.js in the past week?" \
     --start-at "2025-06-16T10:00:00Z" \
     --rrule "FREQ=WEEKLY;BYDAY=MO;BYHOUR=10" \
     --tzid "UTC"
   ```

3. When major versions are detected, trigger deep_research for migration impact.

### Session Continuity Pattern

Before compaction or session end:
1. Save active research topics to memory
2. Note backend_uuid values for follow-up chains
3. Record Space slugs/UUIDs for project context
4. Document any pending decisions

```bash
# Example pre-compact preservation
pplx memories add "session.2025-06-09.topic" "Investigating React Server Components hydration issues"
pplx memories add "session.2025-06-09.uuid" "backend_uuid: abc-123-def-456"
pplx memories add "session.2025-06-09.space" "project-docs-space-uuid: xyz-789"
```

## Safety

- **Ask before deleting** memories, tasks, or workflows
- **Don't save secrets** in Perplexity memories
- **Review scheduled tasks quarterly** to avoid stale monitoring
- **Use descriptive keys** so future-you can find them
