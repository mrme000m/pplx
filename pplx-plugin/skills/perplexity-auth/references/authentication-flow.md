---
# Authentication Flow Guide

Step-by-step walkthrough of the Perplexity login automation using CloakBrowser CDP 
and Gmail OTP extraction.

## Prerequisites

- Python 3.10+
- `websocket-client` library
- CloakBrowser (stealth Chromium)
- Bitwarden CLI & access token
- Gmail account with IMAP enabled + app password
- Perplexity AI account

## Setup Checklist

Before running login automation:

```bash
# 1. Install CloakBrowser
bash <skill>/scripts/utils/cloak_setup.sh

# 2. Verify Bitwarden access
bitwarden login
export BWS_ACCESS_TOKEN=<your-access-token>

# 3. Store Gmail credentials in Bitwarden
python3 <skill>/scripts/session/bw_credentials.py setup \
  --email your.email@gmail.com \
  --gmail-app-password "your-app-password" \
  --forward-to your.actual.inbox@gmail.com

# 4. Verify setup
python3 <skill>/scripts/session/bw_credentials.py show
```

## Login Flow in Detail

### Phase 1: Launch CloakBrowser

**Time**: ~3-5 seconds

CloakBrowser is a stealth version of Chromium that evades Cloudflare detection. 
Standard Chrome/Firefox trigger Cloudflare's bot detection.

### Phase 2: CDP Connection & Navigation

**Time**: ~5-8 seconds

Connect to Chrome DevTools Protocol via WebSocket, initialize network monitoring, 
navigate to Perplexity.

### Phase 3: Click "Sign In" Button

**Time**: ~2-3 seconds

Find and click the "Sign In" button on the Perplexity homepage.

### Phase 4: Fill Email & Submit

**Time**: ~3-5 seconds

Fill email input, submit form, Perplexity sends magic-link email.

### Phase 5: Extract OTP from Gmail

**Time**: ~10-60 seconds (configurable, default 5 min)

Poll Gmail IMAP for magic-link email, extract 6-digit OTP token.

### Phase 6: Fill OTP & Verify

**Time**: ~2-3 seconds

Fill 6-digit OTP in verification form, Perplexity confirms login.

### Phase 7: Extract & Save Cookies

**Time**: ~2-3 seconds

Extract session cookies from CDP Network, save to filesystem and optionally Bitwarden.

### Phase 8: Verify Session

**Time**: ~2-3 seconds

Make test API call to confirm authentication succeeded.

## End-to-End Example

Complete walkthrough of a successful login:

```bash
# Start
$ python3 login.py --email myemail@gmail.com --bw-save

# Internal execution takes approximately 30-90 seconds
# Total: ~30-90 seconds for first login

# Output:
{
  "status": "authenticated",
  "email": "myemail@gmail.com",
  "cookies_saved_to": "~/.config/perplexity/cookies.json",
  "bitwarden_item": "perplexity.ai",
  "expires_at": "2026-07-03T21:14:00Z"
}
```

## Loading Cached Cookies

On subsequent runs, skip the full login:

```bash
$ python3 login.py --email myemail@gmail.com --bw-load

# Internal execution:
# 1. Load cookies from Bitwarden (bw_cookies.py load)
# 2. Verify session with API call
# 3. If valid, exit (total: ~5 seconds)
# 4. If expired: prompt to re-login with --email only (no --bw-load)

# Output:
{
  "status": "authenticated",
  "source": "bitwarden_cache",
  "age_days": 14,
  "expires_in_days": 16
}
```

## Session Refresh

Automate periodic refresh to keep session alive:

```bash
$ python3 session_refresh.py --email myemail@gmail.com

# Internal execution:
# 1. Check current session (quick API call)
# 2. If valid and recent (< 20 days old): exit, no action
# 3. If expired or > 20 days old: run full login.py
# 4. Save new cookies to Bitwarden
# 5. Log result (success/failure)

# Example cron job (run nightly):
# 0 2 * * * /path/to/session_refresh.py --email myemail@gmail.com
```

## Troubleshooting by Phase

| Phase | Error | Fix |
|-------|-------|-----|
| 1 | Port 9223 in use | `lsof -ti tcp:9223 \| xargs kill` |
| 1 | cloakbrowser not found | `bash <skill>/scripts/utils/cloak_setup.sh` |
| 2 | Cloudflare error | CloakBrowser evasion failed, retry |
| 3 | Button not found | Perplexity UI changed, check screenshot |
| 4 | Email input not found | Perplexity UI changed, check screenshot |
| 5 | Email never arrives | Check `GMAIL_FORWARD_TO`, increase timeout |
| 5 | App password error | Re-create app password in Gmail settings |
| 6 | OTP input not found | Perplexity UI changed or custom 2FA enabled |
| 7 | Cookies empty | Browser still in login form, extend Phase 6 timeout |
| 8 | 401 Unauthorized | Cookies weren't persisted, check Phase 7 |
---