---
name: pplx-orchestrate
aliases: [perplexity-orchestrate, pplx-research-chain, pplx-deep-dive]
description: Run multi-step Perplexity research with follow-up chains, cross-validation, and structured synthesis
allowed-tools: [perplexity_search, perplexity_follow_up, perplexity_list_spaces, perplexity_search_in_space, Bash, Read]
argument-hint: "<topic> [--depth quick|standard|deep] [--space <name>]"
---

# /pplx-orchestrate

Conduct structured multi-step research using the ORCHESTRATE pattern: Orient, Research, Cross-reference, Hypothesize, Escalate, Synthesize, Transfer, Evaluate.

## Parameters

- `<topic>`: The research topic or question
- `--depth`: Research depth
  - `quick`: Auto mode + 1 follow-up (free)
  - `standard`: Pro mode + 2-3 follow-ups + cross-validation (low cost)
  - `deep`: Reasoning/deep_research + full chain + synthesis (higher cost)
- `--space`: Project Space to scope initial search

## The ORCHESTRATE Pattern

1. **Orient**: Define the question and success criteria
2. **Research**: Run initial broad search (auto or pro)
3. **Cross-reference**: Validate with targeted follow-ups
4. **Hypothesize**: Form tentative conclusions
5. **Escalate**: Use deeper modes for critical gaps
6. **Synthesize**: Compile findings with confidence levels
7. **Transfer**: Save to memory or upload to Space
8. **Evaluate**: Check if the question was answered

## Example: Technology Evaluation

```bash
# Step 1: Initial landscape mapping
pplx search "State management React 19 2025 overview" --mode auto
# → Note backend_uuid: uuid-1

# Step 2: Follow-up on specific options
pplx follow-up "Zustand 5 vs Jotai 2 for server components" uuid-1
# → Note backend_uuid: uuid-2

# Step 3: Cross-validation
pplx search "Zustand 5 RSC compatibility official docs" --mode pro

# Step 4: Deep research for migration path
pplx search "Migration Redux Toolkit to Zustand 5 comprehensive guide" --mode deep_research

# Step 5: Synthesize and save
pplx memories add "decision.2025-06.state-mgmt" "Chose Zustand 5. See research chain uuid-1, uuid-2."
```

## Example: Space-Scoped Investigation

```bash
# Step 1: Project context from Space
pplx spaces search <space-uuid> "our auth implementation" --mode auto

# Step 2: Broader best practices
pplx search "OAuth2 PKCE mobile app security 2025" --mode pro

# Step 3: Cross-reference with project constraints
pplx follow-up "Given our JWT + refresh token setup, should we add PKCE?" <uuid>
```

## Synthesis Template

```markdown
## Research Synthesis: [Topic]

### Key Findings
| Finding | Confidence | Source Basis |
|---------|-----------|--------------|
| ... | High/Medium/Low | ... |

### Consensus Areas
- ...

### Controversial/Uncertain Areas
- ...

### Recommendations
1. ...

### Unanswered Questions
- ...

### backend_uuid Chain
- Initial: ...
- Follow-ups: ...
```

## Cost Budgeting

| Depth | Typical Mode Chain | Cost |
|-------|-------------------|------|
| quick | auto + 1 follow-up | Free |
| standard | pro + 2-3 follow-ups + validation | Low |
| deep | reasoning/deep_research + full chain | Medium-High |

## Rules

- Never chain more than 5 follow-ups
- Use deep_research only for final synthesis, not every sub-question
- Always validate critical claims with independent searches
- Save backend_uuid values for continuity
- Synthesize before transferring — raw outputs are not decisions
