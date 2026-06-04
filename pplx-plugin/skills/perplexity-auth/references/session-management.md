# Session Management

Guide to cookie persistence, session validation, and token refresh lifecycle.

## Cookie Storage Hierarchy

Cookies are loaded in this priority order:

1. **Filesystem** (~/.config/perplexity/cookies.json)
   - Fastest load time
   - Unencrypted (protect with file permissions)
   - Manual backup only

2. **Bitwarden Secrets Manager** (BWS)
   - Encrypted at rest
   - Synchronized across machines
   - Requires BWS_ACCESS_TOKEN
   - Project: `pplx`, Item: `perplexity.ai` (type: Secure Note)

3. **Legacy Bitwarden CLI** (deprecated)
   - Item: `perplexity.ai` (type: Secure Note)
   - Less secure than BWS
   - Use only if BWS unavailable

## Session Lifecycle

### Initial Login (30-90 seconds)

```
1. CloakBrowser launched
2. Navigate to perplexity.ai
3. Fill email → Perplexity sends magic-link
4. extract_otp.py polls Gmail IMAP
5. Fill OTP → Confirm
6. Cookies extracted via CDP
7. Saved to ~/.config/perplexity/cookies.json
8. Optional: saved to Bitwarden vault
9. Verify with API call
10. Session valid for ~30 days
```

**Cookies contain**:
- `pplx_auth` - Main session token (JWT)
- `pplx_refresh` - Refresh token (if present)
- Session metadata (domain, expiry, secure flags)

### Periodic Refresh (5 seconds if valid, 30-90 seconds if expired)

Run nightly via cron:

```bash
python3 session_refresh.py --email myemail@gmail.com

# Logic:
# 1. Load current session from disk/Bitwarden
# 2. Make lightweight API call (pplx status)
# 3. If 200 OK: session valid
#    - If < 20 days old: skip login, exit success
#    - If 20-25 days old: trigger re-login as precaution
# 4. If 401/403: session expired
#    - Load backup cookies from Bitwarden
#    - If available: verify backup cookies work
#    - If not valid: trigger full login (CDP + OTP)
# 5. Save new cookies, log result
```

**Recommended cron**:
```cron
# Refresh every night at 2 AM
0 2 * * * python3 /path/to/session_refresh.py --email myemail@gmail.com \
  >> ~/.perplexity-auth/logs/refresh.log 2>&1
```

### Session Expiry (30 days)

**Expiry signals**:
- API returns `401 Unauthorized`
- Token decode shows `exp` timestamp in past
- Manual check: `session_status.py --verbose`

**Recovery**:
```bash
# If session expired, re-login
python3 login.py --email myemail@gmail.com --bw-load

# If --bw-load fails (no cached cookies):
python3 login.py --email myemail@gmail.com
# Full CDP login with OTP extraction
```

## Command Reference

### Check Session Status

```bash
# Quick check (returns JSON)
python3 session_status.py --email myemail@gmail.com

# Output:
{
  "status": "valid",
  "authenticated": true,
  "age_days": 15,
  "expires_in_days": 15,
  "source": "filesystem",
  "token_expires_at": "2026-07-03T21:14:00Z"
}

# Verbose (includes token details)
python3 session_status.py --email myemail@gmail.com --verbose

# Output includes:
{
  "status": "valid",
  "authenticated": true,
  "age_days": 15,
  "expires_in_days": 15,
  "source": "filesystem",
  "token_expires_at": "2026-07-03T21:14:00Z",
  "token_claims": {
    "sub": "user-id-123",
    "email": "myemail@gmail.com",
    "iat": 1717446840,
    "exp": 1720038840
  },
  "cookies": {
    "pplx_auth": "eyJ...",
    "secure": true,
    "httpOnly": true
  }
}
```

### Save Cookies to Bitwarden

```bash
# After login, optionally backup cookies
python3 bw_cookies.py save

# Copies ~/.config/perplexity/cookies.json to Bitwarden
# Item: perplexity.ai (type: Secure Note)
# Field: cookies (JSON string)
```

### Load Cookies from Bitwarden

```bash
# Restore cookies from Bitwarden to filesystem
python3 bw_cookies.py load

# Verifies Bitwarden item exists
# Validates JSON format
# Sets file permissions to 600
```

### Check Cookie Status

```bash
# Show which cookies exist and their validity
python3 bw_cookies.py status

# Output:
{
  "filesystem": {
    "exists": true,
    "path": "~/.config/perplexity/cookies.json",
    "valid": true,
    "age_days": 15
  },
  "bitwarden": {
    "exists": true,
    "item": "perplexity.ai",
    "valid": true,
    "age_days": 15,
    "synced_with_filesystem": true
  }
}
```

## Configuration Files

### Bitwarden Item: `perplexity-login` (Credentials)

Type: **Login Item**

| Field | Value | Purpose |
|-------|-------|---------|
| name | `perplexity-login` | Credential storage |
| username | your.email@gmail.com | Perplexity login email |
| password | (empty) | Not used |
| custom: gmail | app-password-here | Gmail IMAP password |
| custom: forward_to | actual.inbox@gmail.com | Where OTP emails arrive |
| custom: otp_email | (optional) | Override forward_to |
| custom: browser | `cloak` or `chrome` | Browser type |
| custom: cdp_port | `9223` | CDP debugging port |
| custom: cookies_path | `~/.config/perplexity/cookies.json` | Cookie storage location |

### Bitwarden Item: `perplexity.ai` (Cookies)

Type: **Secure Note**

| Field | Value | Purpose |
|-------|-------|---------|
| name | `perplexity.ai` | Cookie storage |
| notes | `[{...cookie objects...}]` | JSON array of cookies |

Example:
```json
[
  {
    "name": "pplx_auth",
    "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "domain": ".perplexity.ai",
    "path": "/",
    "expires": 1720038840,
    "httpOnly": true,
    "secure": true
  },
  {
    "name": "pplx_refresh",
    "value": "...",
    "domain": ".perplexity.ai",
    "path": "/",
    "expires": 1751574840,
    "httpOnly": true,
    "secure": true
  }
]
```

## Environment Variables

```bash
# Perplexity account
export PERPLEXITY_EMAIL=your.email@gmail.com

# Cookie storage location
export PERPLEXITY_COOKIES_PATH=~/.config/perplexity/cookies.json

# Bitwarden access
export BWS_ACCESS_TOKEN=<your-bws-token>
export BWS_PROJECT_ID=pplx

# Gmail credentials (stored in Bitwarden, but can override)
export GMAIL_APP_PASSWORD=<override>
export GMAIL_FORWARD_TO=<override>

# Session refresh threshold (days before expiry to trigger re-login)
export SESSION_REFRESH_DAYS=20

# Logging
export LOG_LEVEL=INFO
export LOG_FILE=~/.perplexity-auth/logs/session.log
```

## Error Handling

### Session Not Found

```bash
$ python3 session_status.py

# Error: Session file not found
# Status: 2 (config error)

# Fix:
# 1. Check PERPLEXITY_COOKIES_PATH
# 2. Run login.py to create session
# 3. Or load from Bitwarden: bw_cookies.py load
```

### Session Expired

```bash
$ python3 session_status.py

# Status: expired
# Expires in: -5 days

# Fix:
# Run session_refresh.py (checks Bitwarden cache first)
# Or: python3 login.py --email X --bw-load
```

### Bitwarden Not Configured

```bash
$ python3 bw_cookies.py save

# Error: BWS_ACCESS_TOKEN not set

# Fix:
# 1. Create BWS token in Bitwarden org
# 2. export BWS_ACCESS_TOKEN=<token>
# 3. Retry
```

### Cookies Corrupted

```bash
# Delete and re-login
rm ~/.config/perplexity/cookies.json
python3 login.py --email myemail@gmail.com --bw-save

# Or restore from Bitwarden backup
python3 bw_cookies.py load
python3 session_status.py  # Verify
```

## Best Practices

1. **Always enable Bitwarden backup**
   ```bash
   python3 login.py --email X --bw-save
   ```

2. **Run session_refresh.py nightly**
   ```cron
   0 2 * * * python3 session_refresh.py --email X
   ```

3. **Monitor refresh logs**
   ```bash
   tail -f ~/.perplexity-auth/logs/refresh.log
   ```

4. **Encrypt filesystem cookies**
   ```bash
   chmod 600 ~/.config/perplexity/cookies.json
   ```

5. **Test cookie restoration quarterly**
   ```bash
   # Delete current cookies
   rm ~/.config/perplexity/cookies.json
   # Load from Bitwarden
   python3 bw_cookies.py load
   # Verify
   python3 session_status.py
   ```

## Multi-Device Setup

To use same session across machines:

1. Login on Machine A (with `--bw-save`)
2. On Machine B:
   ```bash
   export BWS_ACCESS_TOKEN=<same-token>
   python3 bw_cookies.py load
   python3 session_status.py  # Verify
   ```
3. Optional: Use `session_refresh.py` on Machine B to rotate cookies

## Session Rotation

To manually rotate credentials:

```bash
# 1. Save current session
python3 bw_cookies.py save

# 2. Run full re-login (forces new token)
python3 login.py --email myemail@gmail.com --bw-save

# 3. Bitwarden item updated with new cookies
# 4. Confirm rotation
python3 session_status.py
```
