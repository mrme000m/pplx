# Architecture

Complete system architecture for the Perplexity Auth skill suite.

## Overview

The `perplexity-auth` skill consolidates login automation, session management, diagnostics, and network traffic analysis into a unified skill for the `pplx-plugin`.

## Directory Structure

```
perplexity-auth/
├── SKILL.md                     # Entry point
├── scripts/
│   ├── auth/
│   │   ├── login.py             # CloakBrowser CDP + OTP orchestrator
│   │   ├── extract_otp.py        # Gmail IMAP OTP fetcher
│   │   └── session_refresh.py   # Session validation and refresh
│   ├── session/
│   │   ├── bw_credentials.py     # Bitwarden credential manager
│   │   ├── bw_cookies.py        # Bitwarden cookie vault
│   │   └── session_status.py    # Session state checker
│   ├── diagnostics/
│   │   ├── health_check.py       # Quick and full diagnostic
│   │   └── verify_cli.py         # CLI command verifier with retries
│   ├── traffic/
│   │   ├── debug_client.py       # HAR capture via curl_cffi hooks
│   │   ├── analyze_traffic.py    # Endpoint discovery from HAR
│   │   └── capture_api_calls.py  # CDP network event capture
│   ├── ui/
│   │   ├── ui_investigator.py    # Deep UI state extraction
│   │   └── ui_crawler.py         # Interactive element discovery
│   └── utils/
│       ├── cloak_setup.sh         # Dependency installer
│       └── browser_debug.py       # Low-level CDP debugging
├── references/
│   ├── architecture.md           # This file
│   ├── authentication-flow.md     # Login flow deep-dive
│   ├── session-management.md     # Session lifecycle
│   ├── diagnostics.md            # Diagnostic workflows
│   ├── bitwarden-setup.md        # Bitwarden configuration
│   ├── environment-reference.md   # Environment variables
│   └── troubleshooting.md         # Common issues
└── examples/
    ├── session-refresh-loop.sh   # Nightly cron refresh
    ├── ci-integration.sh         # CI/CD auth
    └── debug-scenario.sh          # Scenario debugging
```

## Core Components

### Authentication Core (auth/)

**login.py** - Main orchestrator using CloakBrowser via CDP:

Login flow (12 steps):
1. Launch CloakBrowser with CDP remote debugging
2. Navigate to perplexity.ai
3. Click Sign In button
4. Fill email field and submit
5. Perplexity sends magic-link email
6. Poll Gmail IMAP for the email
7. Extract 6-digit token via regex
8. Fill OTP on verification page
9. Wait for redirect to logged-in homepage
10. Extract cookies via Network.getAllCookies CDP command
11. Save cookies to ~/.config/perplexity/cookies.json
12. Optionally sync to Bitwarden

**extract_otp.py** - Gmail IMAP OTP extractor:
- Searches INBOX for FROM "team@mail.perplexity.ai" SUBJECT "Sign in to Perplexity"
- Fallback: broader FROM "perplexity.ai" search
- Extracts token via regex
- Configurable timeout (default 120s) and poll interval (default 5s)

### Session Management (session/)

Three-layer storage model:

| Layer | Storage | Purpose |
|-------|---------|---------|
| Disk | ~/.config/perplexity/cookies.json | Fast SDK access |
| Bitwarden | Secure Note perplexity.ai | Backup/cross-machine sync |
| Browser Profile | CloakBrowser SQLite + localStorage | Full state reuse |

### Diagnostics (diagnostics/)

**health_check.py** - Two modes:
- --quick: Import verification only
- --full: Full diagnostic including API session validation

**verify_cli.py** - Command verification with retries

### Traffic Analysis (traffic/)

**debug_client.py** - HTTP capture via curl_cffi monkey-patch
**analyze_traffic.py** - Endpoint discovery from HAR files
**capture_api_calls.py** - CDP network event capture

## Key Design Decisions

1. **CloakBrowser over stock Chrome**: Bypasses Cloudflare/Turnstile challenges
2. **Magic-link over password**: No Perplexity password stored
3. **Dual cookie storage**: Disk for speed, Bitwarden for reliability
4. **CDP over Selenium/Playwright**: Direct WebSocket API
5. **No modifications to pplx-sdk**: Debug via pre-import monkey-patch
