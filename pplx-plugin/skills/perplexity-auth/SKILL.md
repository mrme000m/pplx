---
name: perplexity-auth
version: 1.1.0
description: |
  Perplexity AI authentication, session management, and diagnostic verification.
  Handles automated login via CloakBrowser CDP, Gmail OTP extraction, Bitwarden
  credential storage, session health checks, CLI command verification, and
  network traffic analysis.

  Triggers: "perplexity login", "refresh perplexity cookies", "perplexity auth",
  "re-login perplexity", "perplexity session expired", "perplexity health check",
  "verify perplexity", "perplexity debug", "analyze perplexity traffic",
  "perplexity endpoint discovery".

---

# Perplexity Authentication & Diagnostics

Consolidated auth suite combining login automation, session management, diagnostics, and traffic analysis. All scripts live under `scripts/` with detailed reference docs in `references/`.

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

## Next Steps

- **First time?** → Read `references/architecture.md`
- **Setting up Bitwarden?** → Follow `references/bitwarden-setup.md`
- **Need to debug?** → Use `examples/debug-scenario.sh`
- **CI integration?** → Copy `examples/ci-integration.sh`
- **Stuck?** → Check `references/troubleshooting.md`