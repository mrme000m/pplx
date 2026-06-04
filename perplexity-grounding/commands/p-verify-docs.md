---
name: p-verify-docs
aliases: [perplexity-verify-docs, pplx-verify, verify-dependency]
description: Verify that documentation or API patterns for a dependency are current and not deprecated
allowed-tools: [mcp__perplexity__search, mcp__perplexity__follow_up, mcp__perplexity__search_in_space, mcp__perplexity__list_spaces, Read, Grep, Glob]
---

# /p-verify-docs — Verify Dependency Documentation

Check whether the agent's knowledge about a specific library, API, or framework is current. This prevents writing code based on outdated patterns.

## Instructions

Parse the user's arguments as the dependency or API to verify. Then execute this workflow:

### Step 1: Identify What to Verify

The argument can be:
- A library name (e.g. "react-hook-form", "drizzle-orm")
- A specific API (e.g. "next.js generateStaticParams")
- A code pattern (e.g. "tailwind dark mode config")

If the argument is vague, scan the project for relevant imports:
```
Grep for import statements matching the argument
```

### Step 2: Determine Current Version

Find the version used in this project:
1. Check `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, or similar
2. Note the exact version number

### Step 3: Search for Current Documentation

```
mcp__perplexity__search(
    query: "[library] [version] [specific API] current API signature and deprecation status 2025",
    mode: "auto",
    answer_only: true
)
```

### Step 4: Compare and Report

Compare the search result against the agent's prior knowledge:

1. **Confirmed current** — API/pattern is valid for the project's version
2. **Deprecated** — API has been deprecated; note the replacement
3. **Changed** — API signature has changed; note the differences
4. **New** — API was added after training data cutoff; note the details

### Step 5: Apply Corrections

If the verification reveals differences:
- Note exactly what changed
- Update any code the agent was about to write
- Suggest the correct pattern for the project's version

## Examples

```
/p-verify-docs next.js App Router
/p-verify-docs drizzle-orm relational queries
/p-verify-docs @tanstack/react-query useQuery signature
```

## Output Format

```
## Verification: [library] [version]

Status: [CONFIRMED | DEPRECATED | CHANGED | NEW]

[Summary of findings]

[If changed/deprecated]:
- Old pattern: [what the agent previously knew]
- Current pattern: [what is actually correct]
- Migration: [how to update]
```
