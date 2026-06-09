---
name: advanced-research-orchestration
description: |
  This skill should be used when the user needs complex multi-step research, cross-referencing multiple sources, synthesizing findings across searches, building research chains with follow-ups, or conducting due diligence that requires structured investigation. Also trigger when users ask for "comprehensive research", "investigate thoroughly", "compare multiple", "deep dive across", or when a single Perplexity search is insufficient.
version: 1.0.0
---

# Advanced Research Orchestration

Conduct multi-step, cross-referenced research using Perplexity's full feature set — follow-up chains, Space-scoped search, mode escalation, and synthesis.

## When to Orchestrate

Use orchestrated research when:
- A single search can't cover the topic breadth
- Multiple sources need cross-validation
- Findings from one query inform the next query
- The topic spans domains (e.g., "security implications of new React features")
- Decision-quality output is required (technology selection, migration planning)

## The ORCHESTRATE Pattern

```
O - Orient: Define the research question and success criteria
R - Research: Run initial broad search to map the landscape
C - Cross-reference: Validate findings with targeted follow-ups
H - Hypothesize: Form tentative conclusions
E - Escalate: Use deeper modes (pro, reasoning, deep_research) for critical gaps
S - Synthesize: Compile findings with confidence levels
T - Transfer: Save to memory, upload to Space, or document decisions
E - Evaluate: Check if the original question was answered
```

## Phase 1: Orientation

Define before searching:

1. **The question** — What exactly needs to be known?
2. **Success criteria** — What would count as an answer?
3. **Scope boundaries** — What's in scope vs. out of scope?
4. **Decision dependency** — Is this blocking a code change or architectural decision?
5. **Time budget** — How deep should this go?

## Phase 2: Landscape Mapping

Start broad with auto mode:

```bash
pplx search "Overview of state management options for React 19 in 2025" --mode auto
```

Extract from the response:
- Key players/frameworks mentioned
- Version numbers and recency
- Areas of consensus vs. debate
- Gaps that need deeper investigation

## Phase 3: Targeted Follow-ups

Use backend_uuid to chain context:

```bash
# Initial search
RESULT=$(pplx search "React 19 state management comparison" --mode auto --raw)
UUID=$(echo "$RESULT" | jq -r '.backend_uuid')

# Follow-up 1: Deep dive on specific option
pplx follow-up "How does Zustand 5 compare to Jotai 2 for server components?" "$UUID"

# Follow-up 2: Breaking changes
pplx follow-up "What breaking changes should I expect migrating from Redux Toolkit?" "$UUID"

# Follow-up 3: Performance
pplx follow-up "Benchmark data for bundle size and runtime performance?" "$UUID"
```

## Phase 4: Cross-Validation

Validate critical claims with independent searches:

```bash
# Validate claim from follow-up chain
pplx search "Zustand 5 server components compatibility official docs" --mode pro

# Check for conflicting information
pplx search "Jotai 2 server components limitations issues 2025" --mode pro
```

## Phase 5: Deep Research for Critical Gaps

For the most important unanswered questions, use deep_research:

```bash
pplx search "Comprehensive migration guide from Redux to Zustand for React 19 with server components" --mode deep_research
```

## Phase 6: Synthesis

Compile findings with confidence annotation:

```markdown
## Research Synthesis: [Topic]

### Key Findings
| Finding | Confidence | Source Basis |
|---------|-----------|--------------|
| Zustand 5 supports RSC | High | Official docs, multiple sources |
| Jotai 2 has edge cases with RSC | Medium | GitHub issues, one source |
| Migration from RTK is straightforward | Medium | Community posts, no official guide |

### Consensus Areas
- [List areas where sources agree]

### Controversial/Uncertain Areas
- [List areas with conflicting info]

### Recommendations
1. [Actionable recommendation with rationale]
2. [Alternative with trade-offs]

### Unanswered Questions
- [What still needs investigation]

### backend_uuid Chain
- Initial: `uuid-1`
- Follow-ups: `uuid-2`, `uuid-3`, `uuid-4`
```

## Phase 7: Transfer

Preserve findings for future use:

```bash
# Save key decisions to memory
pplx memories add "decision.2025-06.state-management" "Chose Zustand 5 over Jotai 2 for RSC compatibility. See research chain uuid-1."

# Upload synthesis to project Space
pplx spaces upload <space-uuid> research-synthesis-state-management.md

# Pin generated report asset
pplx assets pin <report-asset-id>
```

## Space-Scoped Orchestration

When project context exists in a Space:

1. Start with Space search for project-specific grounding
2. Use general web search for broader context
3. Cross-reference findings

```bash
# Step 1: Project-specific context
pplx spaces search <space-uuid> "our current auth pattern" --mode auto

# Step 2: Broader comparison
pplx search "OAuth2 vs OIDC 2025 best practices" --mode pro

# Step 3: Cross-reference with project constraints
pplx follow-up "Given our existing JWT setup, should we migrate to OIDC?" <uuid>
```

## Cost Budgeting

| Research Depth | Typical Cost | Use For |
|----------------|-------------|---------|
| Auto + 1 follow-up | Free | Quick decisions |
| Pro + 2-3 follow-ups | Low | Standard due diligence |
| Reasoning + cross-validation | Medium | Architecture decisions |
| Deep research + full chain | High | Major technology choices |

## Anti-Patterns

- **Don't** chain more than 5 follow-ups — diminishing returns
- **Don't** use deep_research for every sub-question — save it for synthesis
- **Don't** forget to validate claims from follow-ups with independent searches
- **Don't** skip synthesis — raw search outputs are not decisions
- **Don't** lose backend_uuid values — they are the research trail
