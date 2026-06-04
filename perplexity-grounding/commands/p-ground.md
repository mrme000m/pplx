---
name: p-ground
aliases: [perplexity-ground, pplx-ground, ground-check, fact-check]
description: Quick fact-check a specific claim or assumption against live web search
allowed-tools: [mcp__perplexity__search, mcp__perplexity__follow_up]
---

# /p-ground — Quick Fact Check

Ground a specific claim, assumption, or code pattern against live web search. Returns a terse verdict.

## Instructions

Parse the user's arguments as the claim to verify. Execute a single targeted search:

### Step 1: Formulate Precise Query

Convert the claim into a verification query:
- Add library name and version if inferable
- Add specific API or pattern name
- Frame as a yes/no or factual question

### Step 2: Search

```
mcp__perplexity__search(
    query: "<precise verification query>",
    mode: "auto",
    answer_only: true
)
```

### Step 3: Render Verdict

Output exactly one of:

- **GROUNDED** — Claim is confirmed by current sources. Brief note.
- **OUTDATED** — Claim was true but has changed. Note the current state.
- **INCORRECT** — Claim is wrong. Note the correct information.
- **UNCERTAIN** — Could not verify definitively. Note what was found.

### Step 4: If Outdated/Incorrect

Provide the correct pattern or fact. If this affects code the agent has written or plans to write, note the correction.

## Examples

```
/p-ground React useEffect cleanup runs on unmount only
/p-ground Tailwind v4 uses tailwind.config.js
/p-ground Next.js 15 supports Node.js 18 minimum
/p-ground Python 3.13 removed the GIL
```
