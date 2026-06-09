---
name: pplx-assets
aliases: [perplexity-assets, pplx-reports, pplx-download]
description: Manage Perplexity-generated assets, reports, code artifacts, and downloads
allowed-tools: [Bash, perplexity_list_assets, perplexity_pin_asset, perplexity_unpin_asset, perplexity_delete_asset, perplexity_download_asset]
argument-hint: "list|pins|pin|unpin|delete|download"
---

# /pplx-assets

Track, organize, and download Perplexity-generated assets from searches, especially pro and deep_research modes.

## Sub-commands

### list
List all generated assets.

```bash
pplx assets list --limit 20
pplx assets list --versions  # Show all versions
```

### pins
List pinned assets.

```bash
pplx assets pins
```

### pin <asset_id>
Pin an asset to prevent expiration.

```bash
pplx assets pin <asset_id>
```

### unpin <asset_id>
Unpin an asset.

```bash
pplx assets unpin <asset_id>
```

### delete <asset_id>
Delete an asset permanently.

```bash
pplx assets delete <asset_id> --force
```

### download <url> <filename>
Download an asset for local use.

```bash
pplx assets download <url> <filename>
```

## Workflow

1. After a `deep_research` or `pro` search, list assets:
   ```bash
   pplx assets list --limit 10
   ```

2. Pin important assets:
   ```bash
   pplx assets pin <report-id>
   ```

3. Download code examples or reports:
   ```bash
   pplx assets download <url> migration-guide.md
   ```

4. Upload relevant content to project Space:
   ```bash
   pplx spaces upload <space-uuid> migration-guide.md
   ```

## Asset Types

| Type | Description | Action |
|------|-------------|--------|
| Reports | Research summaries, comparisons | Pin + download |
| Code blocks | Generated examples | Download + integrate |
| Images | Diagrams, charts | Download if needed |
| Data exports | Tables, structured data | Download for analysis |

## Best Practices

- Check for assets after every `deep_research` search
- Pin migration guides and architecture comparisons
- Don't pin one-off code snippets — copy to codebase directly
- Review and clean pinned assets monthly
- Use descriptive filenames when downloading
