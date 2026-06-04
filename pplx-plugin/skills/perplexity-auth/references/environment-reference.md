# Environment Variables Reference

Complete documentation of all configuration options for Perplexity Auth skill.

## Perplexity Account

### PERPLEXITY_EMAIL
- **Type**: String (email address)
- **Required**: Yes
- **Default**: None
- **Description**: Perplexity AI login email address
- **Example**: `export PERPLEXITY_EMAIL=user@gmail.com`

### PERPLEXITY_COOKIES_PATH
- **Type**: String (file path)
- **Required**: No
- **Default**: `~/.config/perplexity/cookies.json`
- **Description**: Where to store/load session cookies
- **Example**: `export PERPLEXITY_COOKIES_PATH=/secure/perplexity-cookies.json`

## Bitwarden Secrets Manager (BWS)

### BWS_ACCESS_TOKEN
- **Type**: String (token)
- **Required**: Yes (for Bitwarden sync)
- **Default**: None
- **Description**: Service account access token for Bitwarden
- **Valid for**: 30 days (configurable), then must rotate
- **Example**: `export BWS_ACCESS_TOKEN="8.abc123def456..."`
- **How to get**: 
  - Bitwarden web vault → Settings → Organization → Service Accounts
  - Create service account, generate token

### BWS_PROJECT_ID
- **Type**: String (UUID)
- **Required**: Yes (for Bitwarden sync)
- **Default**: None
- **Description**: Bitwarden project ID for credential storage
- **Example**: `export BWS_PROJECT_ID="12345678-1234-1234-1234-123456789012"`
- **How to get**:
  - Bitwarden web vault → Settings → Organization → Service Accounts
  - Click project, copy ID

## Gmail IMAP Configuration

### GMAIL_APP_PASSWORD
- **Type**: String (password)
- **Required**: Yes (for OTP extraction)
- **Default**: None (can load from Bitwarden instead)
- **Description**: Gmail app-specific password for IMAP access
- **Note**: NOT your regular Gmail password; must be app password
- **Example**: `export GMAIL_APP_PASSWORD="abcd efgh ijkl mnop"`
- **How to get**:
  - https://myaccount.google.com → Security → App passwords
  - Select Mail → Other (custom name)
  - Copy 16-character password

### GMAIL_FORWARD_TO
- **Type**: String (email address)
- **Required**: Yes (for OTP extraction)
- **Default**: `PERPLEXITY_EMAIL` (if same inbox receives OTPs)
- **Description**: Gmail inbox that receives Perplexity OTP emails
- **Example**: `export GMAIL_FORWARD_TO="actual.inbox@gmail.com"`
- **Use case**: If Perplexity email forwards to another account

### GMAIL_OTP_TIMEOUT
- **Type**: Integer (seconds)
- **Required**: No
- **Default**: 300 (5 minutes)
- **Description**: How long to wait for OTP email before timing out
- **Example**: `export GMAIL_OTP_TIMEOUT=600`
- **Range**: 10-1800 seconds (10 seconds to 30 minutes)

### GMAIL_IMAP_SERVER
- **Type**: String (hostname)
- **Required**: No
- **Default**: `imap.gmail.com`
- **Description**: Gmail IMAP server address
- **Example**: `export GMAIL_IMAP_SERVER="imap.gmail.com"`

### GMAIL_IMAP_PORT
- **Type**: Integer (port number)
- **Required**: No
- **Default**: 993 (SSL)
- **Description**: Gmail IMAP port
- **Valid**: 143 (TLS), 993 (SSL)
- **Example**: `export GMAIL_IMAP_PORT=993`

## CloakBrowser Configuration

### CLOAK_CDP_PORT
- **Type**: Integer (port)
- **Required**: No
- **Default**: 9223
- **Description**: Remote debugging port for Chrome DevTools Protocol
- **Example**: `export CLOAK_CDP_PORT=9224`
- **Note**: Change if 9223 is already in use

### CLOAK_BROWSER_PATH
- **Type**: String (file path)
- **Required**: No
- **Default**: Auto-detect from PATH
- **Description**: Explicit path to cloakbrowser executable
- **Example**: `export CLOAK_BROWSER_PATH=/usr/local/bin/cloakbrowser`

### CLOAK_TIMEOUT
- **Type**: Integer (seconds)
- **Required**: No
- **Default**: 30
- **Description**: CDP connection timeout
- **Example**: `export CLOAK_TIMEOUT=60`

### CLOAK_HEADLESS
- **Type**: Boolean (true/false)
- **Required**: No
- **Default**: false (show UI)
- **Description**: Run browser in headless mode (no visible window)
- **Example**: `export CLOAK_HEADLESS=true`
- **Use case**: CI/CD environments

## Session Management

### SESSION_REFRESH_DAYS
- **Type**: Integer (days)
- **Required**: No
- **Default**: 20
- **Description**: Session age threshold to trigger re-login
- **Example**: `export SESSION_REFRESH_DAYS=25`
- **Range**: 1-29 (session expires at 30 days)
- **Note**: Lower = more frequent logins, higher = risk of unexpected expiry

### SESSION_EXPIRY_DAYS
- **Type**: Integer (days)
- **Required**: No
- **Default**: 30
- **Description**: Maximum session lifetime (matches Perplexity API)
- **Example**: `export SESSION_EXPIRY_DAYS=30`
- **Note**: Usually fixed by Perplexity; only change if documented

## Logging Configuration

### LOG_LEVEL
- **Type**: String (enum)
- **Required**: No
- **Default**: INFO
- **Valid values**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Example**: `export LOG_LEVEL=DEBUG`
- **Use cases**:
  - DEBUG: Detailed troubleshooting
  - INFO: Standard operation
  - WARNING: Issues but can continue
  - ERROR: Failures requiring action

### LOG_FILE
- **Type**: String (file path)
- **Required**: No
- **Default**: `~/.perplexity-auth/logs/auth.log`
- **Description**: Where to write log output
- **Example**: `export LOG_FILE=/var/log/perplexity-auth.log`
- **Rotation**: Handled by script (daily, keep 7 days)

### LOG_TO_STDOUT
- **Type**: Boolean (true/false)
- **Required**: No
- **Default**: false
- **Description**: Also print logs to console
- **Example**: `export LOG_TO_STDOUT=true`

## Testing & Development

### DRY_RUN
- **Type**: Boolean (true/false)
- **Required**: No
- **Default**: false
- **Description**: Simulate operations without making changes
- **Example**: `export DRY_RUN=true`
- **Use case**: Test configuration without logging in

### DEBUG_CDP
- **Type**: Boolean (true/false)
- **Required**: No
- **Default**: false
- **Description**: Enable CDP WebSocket message logging
- **Example**: `export DEBUG_CDP=true`
- **Output**: All CDP messages to stderr

### SKIP_AUTH_VERIFY
- **Type**: Boolean (true/false)
- **Required**: No
- **Default**: false
- **Description**: Skip final authentication verification (speed up)
- **Example**: `export SKIP_AUTH_VERIFY=true`
- **Warning**: May miss authentication failures

## Configuration File

Instead of individual env vars, load from file:

```bash
# Create config file
cat > ~/.perplexity-auth.conf << EOF
PERPLEXITY_EMAIL=user@gmail.com
PERPLEXITY_COOKIES_PATH=~/.config/perplexity/cookies.json

BWS_ACCESS_TOKEN=8.abc123...
BWS_PROJECT_ID=12345678-...

GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
GMAIL_FORWARD_TO=actual.inbox@gmail.com

CLOAK_CDP_PORT=9223
LOG_LEVEL=INFO
EOF

# Load config
export $(cat ~/.perplexity-auth.conf | grep -v '^#' | xargs)

# Verify
echo $PERPLEXITY_EMAIL
```

## Loading Priority

Environment variables are loaded in this order (first found wins):

1. **Command-line arguments** (highest priority)
   ```bash
   python3 login.py --email user@gmail.com --config /custom/path
   ```

2. **Environment variables**
   ```bash
   export PERPLEXITY_EMAIL=user@gmail.com
   python3 login.py
   ```

3. **Config file** (if `--config` specified)
   ```bash
   python3 login.py --config ~/.perplexity-auth.conf
   ```

4. **Default values** (lowest priority)
   ```bash
   python3 login.py
   # Uses defaults: ~/.config/perplexity/cookies.json, etc.
   ```

## Example Configurations

### Minimal Setup

```bash
export PERPLEXITY_EMAIL=user@gmail.com
export GMAIL_APP_PASSWORD="abcd efgh ijkl mnop"
export GMAIL_FORWARD_TO=user@gmail.com

# Now these work:
python3 login.py
python3 health_check.py --quick
```

### Bitwarden Setup

```bash
export PERPLEXITY_EMAIL=user@gmail.com
export BWS_ACCESS_TOKEN="8.abc123..."
export BWS_PROJECT_ID="12345678-..."

# Credentials loaded from Bitwarden automatically
python3 login.py --bw-save
python3 bw_cookies.py load
```

### CI/CD Setup

```bash
# In GitHub Actions / GitLab CI as secrets:
export PERPLEXITY_EMAIL=${{ secrets.PERPLEXITY_EMAIL }}
export BWS_ACCESS_TOKEN=${{ secrets.BWS_ACCESS_TOKEN }}
export BWS_PROJECT_ID=${{ secrets.BWS_PROJECT_ID }}
export CLOAK_HEADLESS=true
export LOG_LEVEL=WARNING

# Load cookies and run
python3 bw_cookies.py load
python3 health_check.py --quick
```

### Development Setup

```bash
export PERPLEXITY_EMAIL=dev@gmail.com
export CLOAK_CDP_PORT=9224
export LOG_LEVEL=DEBUG
export DEBUG_CDP=true

# Test with verbose output
python3 login.py
```

### Multi-Account Setup

```bash
# Account 1
PERPLEXITY_EMAIL=user1@gmail.com \
PERPLEXITY_COOKIES_PATH=~/.config/perplexity/user1-cookies.json \
python3 login.py

# Account 2
PERPLEXITY_EMAIL=user2@gmail.com \
PERPLEXITY_COOKIES_PATH=~/.config/perplexity/user2-cookies.json \
python3 login.py
```

## Validation

All environment variables are validated on startup:

```bash
# Check configuration
python3 config_loader.py

# Output:
{
  "status": "valid",
  "perplexity_email": "user@gmail.com",
  "cookies_path": "~/.config/perplexity/cookies.json",
  "bws_configured": true,
  "gmail_configured": true,
  "cloak_browser_found": true
}
```

If validation fails:

```bash
# Check for errors
python3 config_loader.py --validate

# Output detailed error
{
  "status": "error",
  "errors": [
    "PERPLEXITY_EMAIL not set",
    "GMAIL_APP_PASSWORD not set"
  ],
  "warnings": [
    "LOG_FILE directory does not exist; will be created"
  ]
}
```
