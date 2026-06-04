# Bitwarden Setup Guide

Complete walkthrough for storing Perplexity credentials and cookies in Bitwarden 
Secrets Manager (BWS) for secure, synchronized access across machines.

## Prerequisites

- Bitwarden account with organization admin access
- Bitwarden CLI installed: `brew install bitwarden-cli`
- Python 3.10+ with `bitwarden-sdk` installed
- Gmail account with IMAP enabled
- Gmail app password created (not your actual password)

## Step 1: Create Bitwarden Secrets Manager Access Token

### In Bitwarden Web Vault

1. Log in to https://vault.bitwarden.com
2. Go to **Settings → Organization → Service Accounts**
3. Click **Create Service Account**
4. Name: `perplexity-auth`
5. Click **Create**
6. In the service account details, click **Generate Access Token**
7. Choose **30 days** expiry (rotate periodically)
8. Copy the token (this is your **BWS_ACCESS_TOKEN**)
9. Click **Details** → Find **Project ID** (this is your **BWS_PROJECT_ID**)

### Save Token Securely

```bash
# Add to ~/.bashrc or ~/.zshrc
export BWS_ACCESS_TOKEN="<your-long-token-here>"
export BWS_PROJECT_ID="<project-id>"

# Or store in password manager
# Then: export BWS_ACCESS_TOKEN=$(pass show bws-token)
```

## Step 2: Create Bitwarden Items for Credentials

### Item 1: Credentials (`perplexity-login`)

```bash
# Use the setup script
python3 <skill>/scripts/session/bw_credentials.py setup \
  --email your.email@gmail.com \
  --gmail-app-password "abcd efgh ijkl mnop" \
  --forward-to your.actual.inbox@gmail.com
```

What this creates in Bitwarden:

**Item Name**: `perplexity-login`
**Type**: Login Item

| Field | Value |
|-------|-------|
| Username | your.email@gmail.com |
| Password | (empty) |
| custom: gmail | abcd efgh ijkl mnop |
| custom: forward_to | your.actual.inbox@gmail.com |
| custom: otp_email | (empty - optional) |
| custom: browser | cloak |
| custom: cdp_port | 9223 |
| custom: cookies_path | ~/.config/perplexity/cookies.json |

### Item 2: Cookies (`perplexity.ai`)

Created automatically after first login with `--bw-save`:

```bash
python3 <skill>/scripts/auth/login.py \
  --email your.email@gmail.com \
  --bw-save
```

**Item Name**: `perplexity.ai`
**Type**: Secure Note

Contains JSON array of all cookies (encrypted in Bitwarden vault).

## Step 3: Verify Bitwarden Connection

```bash
# Test access
python3 <skill>/scripts/session/bw_credentials.py show

# Output should show:
# Email: your.email@gmail.com
# Gmail app password: ••••••••••••••••••
# Forward to: your.actual.inbox@gmail.com
# Browser: cloak
# CDP port: 9223
# Cookies path: ~/.config/perplexity/cookies.json
```

If this fails:

```bash
# Check token is set
echo $BWS_ACCESS_TOKEN

# Check token is valid (try this)
python3 -c "from bitwarden_sdk import BitwardenClient; print('OK')"

# If ImportError: install SDK
pip install bitwarden-sdk
```

## Gmail App Password Setup

Gmail requires an app password for IMAP (not your actual Gmail password).

### Create App Password

1. Go to https://myaccount.google.com
2. Click **Security** (left sidebar)
3. Enable **2-Step Verification** if not already enabled
4. Scroll down to **App passwords**
5. Select **Mail** → **Other (custom name)**
6. Enter: `perplexity-auth`
7. Click **Generate**
8. Copy the 16-character password (4 spaces for readability): `abcd efgh ijkl mnop`

### Store in Bitwarden

```bash
python3 <skill>/scripts/session/bw_credentials.py setup \
  --email your.email@gmail.com \
  --gmail-app-password "abcd efgh ijkl mnop" \
  --forward-to your.actual.inbox@gmail.com
```

## Email Forwarding (If Applicable)

If your Perplexity email forwards to another inbox:

```bash
python3 <skill>/scripts/session/bw_credentials.py setup \
  --email perplexity-user@company.com \
  --forward-to actual.gmail@gmail.com \
  --gmail-app-password "xxxx xxxx xxxx xxxx"

# Then specify which inbox has the OTP
python3 <skill>/scripts/auth/login.py \
  --email perplexity-user@company.com \
  --bw-load
```

## Backup & Recovery

### Export Credentials (Manual Backup)

```bash
# Show all stored credentials (DON'T commit to git)
python3 <skill>/scripts/session/bw_credentials.py list

# Output:
# {
#   "email": "your.email@gmail.com",
#   "gmail": "abcd efgh ijkl mnop",
#   "forward_to": "your.actual.inbox@gmail.com",
#   ...
# }
```

### Rotate Access Token (Quarterly)

```bash
# 1. Generate new token in Bitwarden web vault
# 2. Update environment variable
export BWS_ACCESS_TOKEN="<new-token>"

# 3. Verify new token works
python3 <skill>/scripts/session/bw_credentials.py show

# 4. Delete old token from web vault (Settings → Service Accounts)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Perplexity Health Check

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Set BWS token
        run: export BWS_ACCESS_TOKEN=${{ secrets.BWS_ACCESS_TOKEN }}
      
      - name: Install dependencies
        run: |
          pip install bitwarden-sdk websocket-client
          bash pplx-plugin/skills/perplexity-auth/scripts/utils/cloak_setup.sh
      
      - name: Load cookies from Bitwarden
        run: |
          python3 pplx-plugin/skills/perplexity-auth/scripts/session/bw_cookies.py load
      
      - name: Run health check
        run: |
          python3 pplx-plugin/skills/perplexity-auth/scripts/diagnostics/health_check.py --quick
      
      - name: Notify on failure
        if: failure()
        run: |
          echo "Perplexity session health check failed"
          exit 1
```

### GitLab CI Example

```yaml
health_check:
  stage: monitor
  script:
    - export BWS_ACCESS_TOKEN=$BWS_ACCESS_TOKEN
    - pip install bitwarden-sdk websocket-client
    - bash pplx-plugin/skills/perplexity-auth/scripts/utils/cloak_setup.sh
    - python3 pplx-plugin/skills/perplexity-auth/scripts/session/bw_cookies.py load
    - python3 pplx-plugin/skills/perplexity-auth/scripts/diagnostics/health_check.py --quick
  only:
    - schedules
```

**In CI settings**, add `BWS_ACCESS_TOKEN` as a protected secret.

## Team Setup (Multiple Users)

### Share Access Without Exposing Credentials

If team members need Perplexity access:

1. **Admin creates shared vault**:
   - Bitwarden Organization
   - Collections: `perplexity-prod`, `perplexity-staging`

2. **Admin grants access**:
   - Users added to organization
   - Collections shared with team

3. **Each user's local setup**:
   ```bash
   export BWS_ACCESS_TOKEN=<their-own-token>
   python3 bw_credentials.py show  # Load shared item
   ```

4. **Credentials never leave Bitwarden**:
   - Users only see BWS token in CI/local
   - Actual passwords only in encrypted vault

## Troubleshooting

### "BWS_ACCESS_TOKEN not set"

```bash
# Check if exported
echo $BWS_ACCESS_TOKEN

# If empty, export in shell
export BWS_ACCESS_TOKEN="your-token"

# Or add to ~/.bashrc/.zshrc permanently
echo 'export BWS_ACCESS_TOKEN="your-token"' >> ~/.bashrc
source ~/.bashrc
```

### "Failed to connect to Bitwarden"

```bash
# Verify SDK installed
python3 -c "from bitwarden_sdk import BitwardenClient; print('OK')"

# If error, install:
pip install bitwarden-sdk

# Verify token is valid (try creating a client)
python3 -c "
from bitwarden_sdk import BitwardenClient
client = BitwardenClient()
client.auth.login_access_token()
print('Connected OK')
"
```

### "Item 'perplexity-login' not found"

```bash
# Check if exists
python3 <skill>/scripts/session/bw_credentials.py list

# If missing, create it
python3 <skill>/scripts/session/bw_credentials.py setup \
  --email your.email@gmail.com \
  --gmail-app-password "xxxx xxxx xxxx xxxx" \
  --forward-to your.inbox@gmail.com
```

### "Gmail app password rejected"

```bash
# 1. Check password is correct (re-create in Gmail)
# 2. Remove spaces: "abcd efgh ijkl mnop" → "abcdefghijklmnop"
# 3. Update in Bitwarden:
python3 <skill>/scripts/session/bw_credentials.py setup \
  --email your.email@gmail.com \
  --gmail-app-password "abcdefghijklmnop" \
  --forward-to your.inbox@gmail.com
```

### "Token expired"

Access tokens expire after 30 days (configurable).

```bash
# Rotate token in Bitwarden web vault:
# 1. Settings → Organization → Service Accounts
# 2. Select account
# 3. Delete old token
# 4. Generate new token (30 days)
# 5. Update locally:

export BWS_ACCESS_TOKEN="<new-token>"
python3 <skill>/scripts/session/bw_credentials.py show  # Verify
```

## Security Best Practices

1. **Never commit tokens to git**
   ```bash
   echo "BWS_ACCESS_TOKEN=*" >> .gitignore
   ```

2. **Use environment variables in CI**
   - Don't hardcode tokens
   - Mark as "protected" secrets in CI platform

3. **Rotate tokens quarterly**
   - Set calendar reminder
   - Update all CI/local machines
   - Delete old tokens from Bitwarden

4. **Limit scope**
   - Service account should only access `perplexity-*` items
   - Don't reuse for other projects

5. **Monitor access**
   - Enable Bitwarden audit logs
   - Review access history
   - Alert on unusual access patterns

6. **Encrypt filesystem cookies**
   ```bash
   chmod 600 ~/.config/perplexity/cookies.json
   ```

7. **Use HTTPS only**
   - All Bitwarden communication encrypted
   - Ensure firewall allows HTTPS outbound
