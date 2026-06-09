---
name: pplx-pro-optimizer
aliases: [perplexity-pro, pplx-modes, pplx-cost]
description: Guide optimal Perplexity mode selection (auto/pro/reasoning/deep_research) for coding tasks with cost-aware escalation rules
allowed-tools: [Bash, Read]
argument-hint: "mode-guide|cost-matrix|escalation-rules|validate <query>"
---

# /pplx-pro-optimizer

Get guidance on optimal Perplexity mode selection for coding tasks. This command helps balance cost, speed, and answer quality.

## Sub-commands

### mode-guide
Show the complete mode selection matrix with examples for each mode.

### cost-matrix
Display cost/speed/quality trade-offs for each mode.

### escalation-rules
Show auto-escalation heuristics for coding contexts — when to use pro, reasoning, or deep_research.

### validate <query>
Analyze a specific query and recommend the optimal mode with rationale.

## Mode Selection Quick Reference

| Mode | Cost | Speed | Best For |
|------|------|-------|----------|
| `auto` | Free | Fast | Quick facts, version checks, syntax |
| `pro` | Paid | Medium | Cited analysis, breaking changes, comparisons |
| `reasoning` | Paid | Medium | Step-by-step debugging, architecture decisions |
| `deep_research` | Paid | Slow | Comprehensive reports, multi-topic analysis |

## Auto-Escalation Heuristics

### Escalate to `pro` when:
- Breaking changes verification for dependency upgrades
- API documentation that changes frequently
- Technology comparison with cited sources needed
- Security vulnerability assessment

### Escalate to `reasoning` when:
- Complex multi-step debugging
- System architecture or migration planning
- Root cause analysis
- Design pattern trade-off analysis

### Escalate to `deep_research` when:
- New framework evaluation for adoption
- Major version migration (e.g., React 18→19)
- Multi-technology stack comparison
- Comprehensive security audit

## CLI Examples

```bash
# Quick check — start with auto
pplx search "Python dataclass frozen parameter" --mode auto

# Breaking changes — escalate to pro
pplx search "React 19 breaking changes migration" --mode pro

# Architecture decision — use reasoning
pplx search "Microservices vs monolith for small team trade-offs" --mode reasoning

# Major evaluation — deep research
pplx search "Full comparison Svelte 5 vs React 19 2025" --mode deep_research
```
