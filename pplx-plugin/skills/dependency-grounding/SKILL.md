---
name: dependency-grounding
description: This skill should be used when implementing or reviewing code with external dependencies whose syntax may have changed, when the user asks to "verify docs", "latest API", "breaking changes", "is this pattern current", or when dependency manifests are edited, package upgrades occur, or unfamiliar imports are detected.
version: 1.1.0
---

# Dependency Grounding

Prevent stale API usage by verifying external dependency facts with Perplexity when local code and training data are insufficient.

## When to Ground

Search when any of these are true:
- User asks for latest/current/up-to-date behavior.
- A dependency version changed.
- A new external package is introduced.
- An API signature, config option, or migration path is version-sensitive.
- An error message references package internals.

Do not search for local project behavior; read the codebase.

## Workflow

1. Identify package/API and exact project version from manifests.
2. Formulate query: `[package] [version] [API/config] current docs deprecation breaking changes`.
3. Use Perplexity `auto` mode and answer-only style for quick checks.
4. Apply the verified pattern to code or recommendations.
5. If this will recur, upload manifest/docs to a project Space.

## Output

```markdown
Status: CONFIRMED | CHANGED | DEPRECATED | UNCERTAIN
Package/API: <name> <version>
Finding: <concise grounded answer>
Action: <what to change or verify next>
```

## CLI Fallback

```bash
pplx search "<package> <version> <api> current docs deprecation" --mode auto
```
