# Development Tools & UI Debugging

Advanced tools for deep investigation, UI automation, and integration development.

## UI Investigation

Launch Chrome via CDP and extract React state, DOM, storage, and screenshots:

```bash
python3 <skill>/scripts/debug/ui_investigator.py \
  --url https://www.perplexity.ai \
  --extract-state \
  --extract-storage \
  --screenshot

# Output:
{
  "url": "https://www.perplexity.ai",
  "timestamp": "2026-05-28T12:00:00Z",
  "page": {
    "title": "Perplexity AI",
    "description": "...",
    "scripts_count": 15,
    "stylesheets_count": 8
  },
  "react_state": {
    "models": [...],
    "activeModel": "claude-3-opus",
    "user": {
      "id": "user-123",
      "email": "..."
    }
  },
  "storage": {
    "localStorage": {...},
    "sessionStorage": {...},
    "cookies": [...]
  },
  "screenshots": [
    "~/.perplexity-debug/sessions/2026-05-28-12-00-00/screenshot-1.png",
    "~/.perplexity-debug/sessions/2026-05-28-12-00-00/screenshot-2.png"
  ]
}
```

Options:
- `--url` - Target URL (default: perplexity.ai homepage)
- `--extract-state` - Extract React/Vue state
- `--extract-storage` - Extract localStorage, sessionStorage
- `--screenshot` - Capture screenshots
- `--output-dir` - Save directory
- `--phase` - Execution phase (navigate, interact, analyze)

## Interactive Element Crawler

Discover clickable elements and track page interactions:

```bash
python3 <skill>/scripts/debug/ui_crawler.py \
  --limit 20 \
  --save-har

# Output:
{
  "url": "https://www.perplexity.ai",
  "elements": [
    {
      "type": "button",
      "text": "Sign In",
      "selector": "button[data-testid='signin-button']",
      "interactive": true,
      "position": {"x": 1200, "y": 40}
    },
    {
      "type": "input",
      "placeholder": "Ask anything",
      "selector": "input#search-input",
      "interactive": true
    }
  ],
  "total_elements": 127,
  "interactive_elements": 34
}
```

Options:
- `--limit` - Max elements to discover
- `--save-har` - Capture network traffic
- `--deep-dive` - Extract JS/CSS info from each element

## Browser Profile Management

Save/restore authenticated browser state to skip re-login during development:

```bash
# Save current authenticated session
python3 <skill>/scripts/debug/browser_profiler.py \
  --action save \
  --profile perplexity-dev

# Load saved profile (skip login)
python3 <skill>/scripts/debug/browser_profiler.py \
  --action load \
  --profile perplexity-dev

# List saved profiles
python3 <skill>/scripts/debug/browser_profiler.py \
  --action list
```

Output locations:
```
~/.perplexity-auth/profiles/
├── perplexity-dev/
│   ├── cookies.json
│   ├── localStorage.json
│   ├── sessionStorage.json
│   └── metadata.json
├── perplexity-prod/
└── ...
```

## Scenario-Based Debugging

Run predefined debug scenarios to exercise specific flows:

```bash
# Search flow: auto search → pro search → follow-up
python3 <skill>/scripts/debug/ui_investigator.py \
  --scenario search-flow

# Space management: create → list → edit → delete
python3 <skill>/scripts/debug/ui_investigator.py \
  --scenario space-management

# Login flow: fresh login → session verify
python3 <skill>/scripts/debug/ui_investigator.py \
  --scenario login-flow

# Output:
{
  "scenario": "search-flow",
  "steps": [
    {
      "step": 1,
      "action": "navigate",
      "url": "https://www.perplexity.ai",
      "result": "ok"
    },
    {
      "step": 2,
      "action": "fill_search",
      "query": "what is machine learning",
      "result": "ok"
    },
    {
      "step": 3,
      "action": "submit_search",
      "mode": "auto",
      "result": "ok",
      "response_time_ms": 2450
    },
    ...
  ],
  "total_time_ms": 8923,
  "status": "success"
}
```

## Integration Development Workflow

### 1. Create Persistent Profile

```bash
# First-time: login and save profile
python3 login.py --email myemail@gmail.com --bw-save
python3 browser_profiler.py --action save --profile work-dev
```

### 2. Reuse Profile for Development

```bash
# Load profile (instant, no login needed)
python3 browser_profiler.py --action load --profile work-dev

# Now browser is authenticated, test your changes
python3 ui_investigator.py --url https://www.perplexity.ai/api/test
```

### 3. Capture UI Changes

```bash
# Extract DOM before changes
python3 ui_investigator.py --extract-state --screenshot

# Run your changes/tests

# Extract DOM after changes
python3 ui_investigator.py --extract-state --screenshot --output-dir ./after

# Compare
diff before/state.json after/state.json
```

### 4. Debug API Interactions

```bash
# Crawl with HAR capture
python3 ui_crawler.py --save-har --limit 50

# Analyze captured traffic
python3 analyze_traffic.py --har-file ~/.perplexity-debug/sessions/*/session.har

# Find new endpoints
grep "api/" ~/.perplexity-debug/sessions/*/session.har | jq '.log.entries[] | select(.request.url | contains("/api"))'
```

## Common Development Tasks

### Find Selector for UI Element

```bash
# Crawl and get selectors
python3 ui_crawler.py --limit 100

# Parse output for specific element
python3 ui_crawler.py --limit 100 | jq '.elements[] | select(.text | contains("Sign In"))'

# Result:
{
  "type": "button",
  "text": "Sign In",
  "selector": "button[data-testid='signin-button']"
}
```

### Verify Element Clickability

```bash
# Load profile
python3 browser_profiler.py --action load --profile work-dev

# Test click on element
python3 ui_investigator.py \
  --action click \
  --selector "button[data-testid='signin-button']" \
  --screenshot
```

### Extract Hardcoded Strings

```bash
# Get all text from page
python3 ui_investigator.py --extract-state

# Search for specific strings
jq '.page_text[] | select(. | contains("credit"))'

# Find all model names
jq '.react_state.models[] | .name'
```

### Monitor Network Activity

```bash
# Crawl with network capture
python3 ui_crawler.py --save-har

# Analyze by endpoint
python3 analyze_traffic.py --har-file session.har --group-by-path

# Find slow requests
jq '.log.entries[] | select(.timings.wait > 1000)' session.har
```

## Troubleshooting Development Issues

### "Element not found" error

```bash
# Re-extract selectors
python3 ui_crawler.py --limit 100 --output-dir ./updated

# Check if element changed
diff old-elements.json updated-elements.json

# If element moved/changed:
# 1. Update your selector
# 2. Check Perplexity UI changelog
# 3. File issue if breaking change
```

### "React state extraction failed"

```bash
# Retry with different phase
python3 ui_investigator.py \
  --extract-state \
  --phase analyze  # Wait longer for JS to load

# Or increase timeout
python3 ui_investigator.py \
  --extract-state \
  --timeout 60  # 60 second timeout
```

### "Browser profile corruption"

```bash
# Delete corrupted profile
rm -rf ~/.perplexity-auth/profiles/work-dev

# Re-create
python3 login.py --email myemail@gmail.com --bw-save
python3 browser_profiler.py --action save --profile work-dev
```

## Performance Tips

1. **Reuse profiles** instead of re-logging in each time
   - Save: 30-90 seconds per run
   
2. **Use `--quick` mode** for diagnostics
   - 30 seconds vs 5 minutes for full check

3. **Batch API calls** in verify_cli.py
   - Single HAR capture for multiple commands

4. **Disable screenshots** if not needed
   - Reduces disk I/O and output size

5. **Filter elements** by type when crawling
   - `--element-types button,input` instead of all

## Integration with CI/CD

### GitHub Actions: Daily UI Check

```yaml
name: Daily UI Regression Check

on:
  schedule:
    - cron: '0 8 * * *'

jobs:
  ui-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup
        run: |
          pip install websocket-client
          bash pplx-plugin/skills/perplexity-auth/scripts/utils/cloak_setup.sh
      
      - name: Load profile
        run: |
          python3 pplx-plugin/skills/perplexity-auth/scripts/debug/browser_profiler.py \
            --action load \
            --profile ci-worker
      
      - name: Crawl UI
        run: |
          python3 pplx-plugin/skills/perplexity-auth/scripts/debug/ui_crawler.py \
            --limit 100 \
            --output-dir ./current-ui
      
      - name: Compare to baseline
        run: |
          diff baseline-ui.json current-ui/elements.json || true
      
      - name: Report changes
        if: failure()
        run: echo "UI has changed - review manually"
```
