---
name: perplexity-auth
version: 1.1.0
description: |
  This skill should be used when the user needs Perplexity AI authentication, session management, or diagnostic verification. Trigger phrases include perplexity login, perplexity auth, refresh perplexity cookies, perplexity session expired, perplexity health check, verify perplexity, perplexity debug, analyze perplexity traffic, or perplexity endpoint discovery. Provides automated login via CloakBrowser CDP, Gmail OTP extraction, Bitwarden credential storage, and network traffic analysis.

---

# Perplexity Authentication & Diagnostics

Consolidated auth suite combining login automation, session management, diagnostics, and traffic analysis. All scripts live under `scripts/` with detailed reference docs in `references/`.

## Architecture Overview

The auth skill manages Perplexity session lifecycle through three subsystems: authentication (login automation via CloakBrowser CDP), session management (cookie storage via disk and Bitwarden), and diagnostics (health checks, traffic analysis, CLI verification).

### Login Flow

Authentication uses a 12-step magic-link flow:
1. Launch CloakBrowser with CDP remote debugging port
2. Navigate to perplexity.ai
3. Click Sign In button
4. Fill email field and submit
5. Perplexity sends magic-link email
6. Poll Gmail IMAP for the email
7. Extract 6-digit token via regex from `extract_otp.py`
8. Fill OTP on Perplexity verification page
9. Wait for redirect to logged-in homepage
10. Extract cookies via CDP `Network.getAllCookies`
11. Save cookies to `~/.config/perplexity/cookies.json`
12. Optionally sync to Bitwarden Secure Note

### Three-Layer Storage Model

| Layer | Storage | Purpose |
|-------|---------|---------|
| Disk | `~/.config/perplexity/cookies.json` | Fast SDK access, primary source |
| Bitwarden | Secure Note `perplexity.ai` | Backup and cross-machine sync |
| Browser Profile | CloakBrowser SQLite + localStorage | Full state reuse between sessions |

### Key Design Decisions

- **CloakBrowser over stock Chrome**: Bypasses Cloudflare/Turnstile challenges that block automated login
- **Magic-link over password**: No Perplexity password stored; authentication flows through Gmail OTP
- **Dual cookie storage**: Disk for speed, Bitwarden for reliability and cross-machine availability
- **CDP over Selenium/Playwright**: Direct WebSocket API for fine-grained browser control
- **No modifications to pplx-sdk**: Traffic debug via pre-import monkey-patch, not SDK changes

**See**: `references/architecture.md` for complete directory structure and component details

## Quick Start

### 1. Install dependencies

```bash
bash <skill>/scripts/utils/cloak_setup.sh --force
```

### 2. Store credentials in Bitwarden

```bash
python3 <skill>/scripts/session/bw_credentials.py setup \
  --email your.email@gmail.com \
  --gmail-app-password "your-gmail-app-password" \
  --forward-to your.actual.inbox@gmail.com
```

### 3. Automated login

```bash
# Full login: CloakBrowser + Gmail OTP + cookie save
python3 <skill>/scripts/auth/login.py --email your.email@gmail.com --bw-save

# Fast login: load from Bitwarden (no browser)
python3 <skill>/scripts/auth/login.py --email your.email@gmail.com --bw-load
```

### 4. Health check

```bash
# Quick: verify dependencies and cookies
python3 <skill>/scripts/diagnostics/health_check.py --quick

# Full: + session validation via API
python3 <skill>/scripts/diagnostics/health_check.py --full
```

## When to Use Each Script

| Scenario | Script | Reason |
|----------|--------|--------|
| First-time setup | `bw_credentials.py setup` | Store email and Gmail app password |
| Daily login (session valid) | `login.py --bw-load` | Fast, loads cookies from Bitwarden |
| Session expired | `login.py --bw-save` | Full browser login, saves new cookies |
| CI/CD pipeline | `examples/ci-integration.sh` | Automated, non-interactive flow |
| Nightly refresh | `examples/session-refresh-loop.sh` | Cron-based session refresh |
| Debug API calls | `debug_client.py` | HAR capture for endpoint analysis |
| Verify CLI state | `verify_cli.py` | Command-level health check |
| Check session validity | `session_status.py` | API-based session validation |
| Health diagnostics | `health_check.py` | Full dependency and cookie check |

## Subsystem Reference

### Authentication (`scripts/auth/`)

| Script | Purpose |
|--------|---------|
| `login.py` | Main orchestrator — CloakBrowser CDP + OTP extraction |
| `extract_otp.py` | Gmail IMAP poller for 6-digit magic-link token |
| `session_refresh.py` | Validate and refresh session |

**See**: `references/authentication-flow.md`

### Session Management (`scripts/session/`)

| Script | Purpose |
|--------|---------|
| `bw_credentials.py` | Manage `perplexity-login` Bitwarden Login item |
| `bw_cookies.py` | Manage `perplexity.ai` Bitwarden Secure Note (cookie vault) |
| `session_status.py` | Check disk/Bitwarden cookie state, validate via API |

**See**: `references/session-management.md`, `references/bitwarden-setup.md`

### Diagnostics (`scripts/diagnostics/`)

| Script | Purpose |
|--------|---------|
| `health_check.py` | Quick/full diagnostic of deps, cookies, SDK, session |
| `verify_cli.py` | Verify pplx CLI commands with retries |

**See**: `references/diagnostics.md`

### Traffic Analysis (`scripts/traffic/`)

| Script | Purpose |
|--------|---------|
| `debug_client.py` | HAR capture via curl_cffi monkey-patch |
| `analyze_traffic.py` | Endpoint discovery from HAR files |
| `capture_api_calls.py` | CDP network event capture (browser) |

**See**: `references/development-tools.md`

### UI Investigation (`scripts/ui/`)

| Script | Purpose |
|--------|---------|
| `ui_investigator.py` | Deep UI state extraction via CDP |
| `ui_crawler.py` | Interactive element discovery |

**See**: `references/development-tools.md`

## Common Workflows

### Nightly session refresh (cron)

```bash
bash <skill>/examples/session-refresh-loop.sh
```

### CI/CD authentication

```bash
bash <skill>/examples/ci-integration.sh your.email@gmail.com "gmail-app-password"
```

### Debug a scenario

```bash
# search-flow | space-management | login-flow
bash <skill>/examples/debug-scenario.sh search-flow
```

## Environment Configuration

```bash
PERPLEXITY_EMAIL=your.email@gmail.com
PERPLEXITY_COOKIES_PATH=~/.config/perplexity/cookies.json
BWS_ACCESS_TOKEN=<your-bws-token>
GMAIL_APP_PASSWORD=<your-app-password>
GMAIL_FORWARD_TO=your.actual.inbox@gmail.com
CLOAK_CDP_PORT=9223
```

**See**: `references/environment-reference.md`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Just a moment..." (Cloudflare) | Run `cloak_setup.sh --force` |
| IMAP auth failure | Check `bw_credentials.py show` — app password may be expired |
| CDP connection refused | Kill port: `lsof -ti tcp:9223 \| xargs kill` |
| No cookies found | Run full login: `login.py --email $EMAIL --bw-save` |

**See**: `references/troubleshooting.md`

## Additional Resources

### Reference Files
- **`references/architecture.md`** — Complete directory structure and design decisions
- **`references/authentication-flow.md`** — 12-step login flow deep-dive
- **`references/session-management.md`** — Session lifecycle and storage details
- **`references/bitwarden-setup.md`** — Bitwarden CLI and BWS configuration
- **`references/diagnostics.md`** — Diagnostic workflow details
- **`references/development-tools.md`** — Traffic analysis and UI investigation
- **`references/environment-reference.md`** — Environment variable reference
- **`references/troubleshooting.md`** — Common issues and resolutions

### Examples
- **`examples/session-refresh-loop.sh`** — Nightly cron-based session refresh
- **`examples/ci-integration.sh`** — CI/CD non-interactive authentication
- **`examples/debug-scenario.sh`** — Scenario-specific debugging
- **`examples/quick-auth-flow.sh`** — Quick auth test flow
- **`examples/config-example.env`** — Environment configuration template
