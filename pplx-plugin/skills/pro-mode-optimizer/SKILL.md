---
name: pro-mode-optimizer
description: |
  This skill should be used when the user needs guidance on Perplexity Pro mode selection, wants to optimize research costs, needs to decide between auto/pro/reasoning/deep_research, or when auto-escalation decisions need validation. Also trigger when users ask about Perplexity paid features, research depth, citation quality, or when to upgrade from auto to a paid mode.
version: 1.0.0
---

# Pro Mode Optimizer

Make optimal mode decisions for Perplexity searches to balance cost, speed, and answer quality for coding tasks.

## Mode Selection Matrix

| Mode | Cost | Speed | Best For | Avoid When |
|------|------|-------|----------|------------|
| `auto` | Free | Fast | Quick facts, version checks, syntax verification | Deep analysis, cited sources needed |
| `pro` | Paid | Medium | Cited analysis, current docs verification, breaking changes | Simple facts that auto handles |
| `reasoning` | Paid | Medium | Step-by-step debugging, architecture decisions, migration planning | Factual lookups, stable APIs |
| `deep_research` | Paid | Slow | Comprehensive reports, multi-topic comparisons, due diligence | Quick checks, single-answer questions |

## Auto-Escalation Rules for Coding Agents

### Escalate to `pro` when:
- Verifying breaking changes for dependency upgrades
- Checking current documentation for APIs that changed recently
- Needing cited sources for a technical decision
- Comparing 2-3 specific tools/libraries with feature matrices
- Security vulnerability assessment or patch verification

### Escalate to `reasoning` when:
- Debugging complex multi-step issues
- Planning system architecture or migration paths
- Analyzing error traces across multiple dependencies
- Deciding between design patterns with trade-offs
- Root cause analysis for production issues

### Escalate to `deep_research` when:
- Evaluating a new framework for project adoption
- Comprehensive migration guide needed (major version bumps)
- Multi-technology stack comparison for greenfield projects
- Security audit or compliance review across multiple dimensions
- Researching emerging technology viability

### Stay in `auto` when:
- Checking a specific function signature
- Verifying a version number
- Quick syntax check
- Stable language feature confirmation
- Already-known API verification

## Cost Optimization Strategies

1. **Start with auto, escalate only when needed** — Most coding queries are answered well by auto.
2. **Use answer_only=true** via MCP for 90% of queries — only disable when citations are explicitly needed.
3. **Chain follow-ups** with backend_uuid instead of starting new searches.
4. **Use Space search** for project-specific questions before general web search.
5. **Batch related queries** in a single deep_research rather than multiple pro searches.
6. **Cache findings in Perplexity memory** for recurring questions.

## Decision Flow

```
Is the answer time-sensitive or version-dependent?
├── NO → Can training data answer this confidently?
│   ├── YES → Answer directly (no search)
│   └── NO → auto mode
└── YES → Is this a simple factual lookup?
    ├── YES → auto mode
    └── NO → Need step-by-step reasoning?
        ├── YES → reasoning mode
        └── NO → Need cited sources?
            ├── YES → pro mode
            └── NO → Multi-topic comprehensive analysis?
                ├── YES → deep_research
                └── NO → pro mode (default paid)
```

## CLI Usage

```bash
# Quick fact — always start here
pplx search "Python 3.14 match statement syntax" --mode auto

# Cited verification — escalate when needed
pplx search "React 19 use hook breaking changes" --mode pro

# Step-by-step reasoning — debugging, architecture
pplx search "Why does this Next.js 14 middleware fail with edge runtime?" --mode reasoning

# Comprehensive report — major decisions only
pplx search "Full comparison Next.js 14 vs Remix 2025 ecosystem performance" --mode deep_research
```

## Memory Integration

Save mode-selection rationale to Perplexity memory for recurring patterns:

```bash
pplx memories add "project.modes.react" "Always use pro for React version >18 queries due to frequent breaking changes"
pplx memories add "project.modes.python" "Auto mode sufficient for Python stdlib; pro for third-party packages"
```

## Anti-Patterns

- **Don't** use deep_research for single API lookups
- **Don't** use pro for stable language syntax (Python for-loops, JavaScript const)
- **Don't** use reasoning when the answer is a known fact
- **Don't** escalate silently — always note the mode change and why
- **Don't** forget to set answer_only=true in MCP calls when sources aren't needed
