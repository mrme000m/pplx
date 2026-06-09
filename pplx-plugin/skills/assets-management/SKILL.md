---
name: assets-management
description: |
  This skill should be used when Perplexity generates reports, images, code artifacts, diagrams, or data exports that need to be tracked, pinned, downloaded, or organized. Also trigger when users mention "save this report", "download the code", "Perplexity generated", or when working with generated assets from deep_research or pro mode searches.
version: 1.0.0
---

# Assets Management

Track, organize, and download Perplexity-generated assets (reports, code, images, data) for integration into coding workflows.

## What Are Assets?

Perplexity generates assets during searches, especially in `pro` and `deep_research` modes:

| Asset Type | Description | Typical Mode |
|------------|-------------|--------------|
| **Reports** | Formatted research summaries, comparisons | deep_research |
| **Code blocks** | Generated code examples, configurations | pro, reasoning |
| **Images** | Diagrams, charts, visualizations | pro |
| **Data exports** | Structured data, tables, JSON | deep_research |

## Asset Lifecycle

### 1. Discovery

After a Perplexity search, check for generated assets:

```bash
pplx assets list --limit 20
```

### 2. Pin Important Assets

Pin assets you want to keep beyond the default retention:

```bash
pplx assets pin <asset_id>
```

### 3. Download for Local Use

```bash
# Get download URL first
pplx assets list --limit 20  # note the URL from output

# Download
pplx assets download <url> <filename>
```

### 4. Cleanup

Delete unneeded assets to keep the workspace organized:

```bash
pplx assets delete <asset_id> --force
```

## Integration with Coding Workflows

### Post-Deep-Research Asset Handling

After a `deep_research` query:

1. List assets to see what was generated
2. Pin the main report asset
3. Download code examples if applicable
4. Save key findings to Perplexity memory
5. Upload relevant excerpts to project Space

```bash
# Example workflow
pplx search "Comprehensive Rust async runtime comparison 2025" --mode deep_research
pplx assets list --limit 10
pplx assets pin <report-asset-id>
pplx assets download <code-examples-url> rust-async-examples.md
```

### Asset-to-Space Pipeline

For project-relevant generated content:

1. Generate via Perplexity search
2. Download asset locally
3. Upload to project Space for persistent access
4. Pin in Space if frequently referenced

```bash
pplx search "Next.js 14 App Router middleware patterns" --mode pro
pplx assets download <asset-url> nextjs-middleware-patterns.md
pplx spaces upload <space-uuid> nextjs-middleware-patterns.md
```

## Organization Tips

- **Prefix filenames** with topic: `react-19-hooks.md`, not `report-1.md`
- **Pin only what you'll reference again** — unpinned assets expire
- **Download code examples** for local editing and version control
- **Cross-reference assets with memories** for discoverability:
  ```bash
  pplx memories add "assets.nextjs-middleware" "Pinned report: nextjs-middleware-patterns.md (asset_id: xyz)"
  ```

## CLI Reference

```bash
# List all assets
pplx assets list
pplx assets list --limit 50
pplx assets list --versions  # Show all versions

# Pinned assets
pplx assets pins

# Shared assets
pplx assets shared

# Pin/unpin
pplx assets pin <asset_id>
pplx assets unpin <asset_id>

# Delete
pplx assets delete <asset_id> --force

# Download
pplx assets download <url> <filename>
```

## Best Practices

- Check for assets after every `deep_research` and most `pro` searches
- Pin migration guides, architecture comparisons, and API references
- Don't pin one-off code snippets — copy those directly into your codebase
- Review and clean pinned assets monthly
- Share important assets with team via `pplx assets shared`
