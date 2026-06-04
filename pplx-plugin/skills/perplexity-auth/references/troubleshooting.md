# Troubleshooting Guide

Solutions to common issues organized by symptom and component.

## Authentication Issues

### "Cloudflare Just a moment..." message

**Symptom**: Browser stuck on Cloudflare challenge during login

**Causes**:
- CloakBrowser not installed or not detected
- Cloudflare bot detection triggered
- Network proxy interfering

**Solutions**:
```bash
# 1. Verify CloakBrowser installed
which cloakbrowser

# 2. If not found, install
bash <skill>/scripts/utils/cloak_setup.sh

# 3. Verify stealth mode enabled
cloakbrowser --headless --remote-debugging-port=9223 &
curl http://localhost:9223/json/version

# 4. If Cloudflare still blocks: increase timeout
python3 login.py \
  --email myemail@gmail.com \
  --timeout 60  # 60 second page load timeout
```

### "IMAP authentication failed"

**Symptom**: `extract_otp.py` fails to connect to Gmail

**Causes**:
- Gmail app password incorrect or expired
- 2-Step Verification not enabled
- Account locked by Google

**Solutions**:
```bash
# 1. Verify credentials in Bitwarden
python3 bw_credentials.py show

# 2. Re-create Gmail app password
# Go to: https://myaccount.google.com → Security → App passwords
# Select Mail → Other (perplexity-auth)
# Copy new password: "abcd efgh ijkl mnop"

# 3. Update in Bitwarden
python3 bw_credentials.py setup \
  --email myemail@gmail.com \
  --gmail-app-password "abcd efgh ijkl mnop" \
  --forward-to your.inbox@gmail.com

# 4. Verify
python3 bw_credentials.py show

# 5. Retry login
python3 login.py --email myemail@gmail.com --bw-save
```

### "OTP not found / Email never arrives"

**Symptom**: `extract_otp.py` times out waiting for email

**Causes**:
- Email forwarding rules consuming email
- Timeout too short
- Perplexity email server delay
- Account flagged by Gmail

**Solutions**:
```bash
# 1. Check Gmail forwarding rules
# Go to: https://mail.google.com → Settings → Forwarding and POP/IMAP
# Disable auto-forward if active

# 2. Increase OTP timeout
python3 login.py \
  --email myemail@gmail.com \
  --otp-timeout 600  # 10 minutes instead of default 5

# 3. Verify forward-to address is correct
python3 bw_credentials.py show | grep forward_to

# 4. Check Gmail IMAP is enabled
# Settings → Forwarding and POP/IMAP → Enable IMAP

# 5. If still failing, check if email arrived at all
# Go to Gmail, search for: from:team@mail.perplexity.ai
# If missing: Perplexity service down or account issue
```

### "CDP connection refused"

**Symptom**: `Port 9223 connection refused`

**Causes**:
- Port already in use
- CloakBrowser crashed
- Firewall blocking

**Solutions**:
```bash
# 1. Kill existing process
lsof -ti tcp:9223 | xargs kill

# 2. Verify port is free
netstat -an | grep 9223  # Should be empty

# 3. Try different port
python3 login.py \
  --email myemail@gmail.com \
  --cdp-port 9224  # Use alternate port

# 4. Check firewall
# macOS: System Preferences → Security & Privacy → Firewall
# Linux: sudo ufw allow 9223/tcp
# Windows: Allow in Windows Defender Firewall
```

## Session Issues

### "Session expired" / 401 Unauthorized

**Symptom**: API returns 401, login required

**Causes**:
- Cookies older than 30 days
- Cookies corrupted or deleted
- Perplexity revoked token

**Solutions**:
```bash
# 1. Check session age
python3 session_status.py

# 2. If expired, refresh
python3 session_refresh.py --email myemail@gmail.com --force

# 3. If refresh fails, full re-login
python3 login.py --email myemail@gmail.com --bw-save

# 4. If Bitwarden has backup, try that first
python3 bw_cookies.py load
python3 session_status.py  # Verify

# 5. If all fails, delete and re-create
rm ~/.config/perplexity/cookies.json
python3 login.py --email myemail@gmail.com --bw-save
```

### "Cookies file not found"

**Symptom**: `FileNotFoundError: ~/.config/perplexity/cookies.json`

**Causes**:
- First login hasn't been run
- File was deleted
- Wrong path configured

**Solutions**:
```bash
# 1. Check path
echo $PERPLEXITY_COOKIES_PATH

# 2. Ensure directory exists
mkdir -p ~/.config/perplexity

# 3. Run login
python3 login.py --email myemail@gmail.com --bw-save

# 4. Verify file created
ls -la ~/.config/perplexity/cookies.json
```

### "BWS token expired"

**Symptom**: `Bitwarden access denied` or `Invalid token`

**Causes**:
- Token expired (30 day default)
- Token revoked
- Wrong token

**Solutions**:
```bash
# 1. Check token
echo $BWS_ACCESS_TOKEN

# 2. Verify it's still valid
python3 -c "
from bitwarden_sdk import BitwardenClient
client = BitwardenClient()
client.auth.login_access_token()
print('Token valid')
"

# 3. If expired, generate new token in Bitwarden web vault
# Settings → Organization → Service Accounts → Select account → Generate Token

# 4. Update locally
export BWS_ACCESS_TOKEN="<new-token>"
echo "export BWS_ACCESS_TOKEN='<new-token>'" >> ~/.bashrc

# 5. Verify
python3 bw_credentials.py show
```

## Diagnostic Issues

### "Health check says session expired"

**Symptom**: `python3 health_check.py --quick` returns expired status

**Solutions**:
```bash
# 1. Check actual age
python3 session_status.py --verbose

# 2. If not actually expired, update threshold
# Default is 25 days; if closer to 30, refresh manually
python3 session_refresh.py --email myemail@gmail.com

# 3. If actually expired, login again
python3 login.py --email myemail@gmail.com --bw-load
```

### "CLI command verification fails"

**Symptom**: `verify_cli.py` shows commands failing

**Solutions**:
```bash
# 1. Test command manually
pplx models

# 2. Check if pplx CLI works
which pplx
pplx --version

# 3. Verify session is valid
python3 session_status.py

# 4. Run with increased retry
python3 verify_cli.py \
  --commands models \
  --retry 5 \
  --timeout 30

# 5. Check Perplexity service status
# Go to: https://status.perplexity.ai
```

## Network & Infrastructure Issues

### "Network timeout"

**Symptom**: `Connection timed out` during API calls

**Causes**:
- Network connectivity issue
- Perplexity service down
- DNS not resolving
- Firewall blocking

**Solutions**:
```bash
# 1. Test basic connectivity
ping -c 3 1.1.1.1  # Test DNS
ping -c 3 perplexity.ai

# 2. Check DNS resolution
nslookup perplexity.ai
# Should return IP address

# 3. Test HTTPS connection
curl -I https://www.perplexity.ai

# 4. Check firewall
# Ensure HTTPS (port 443) is open outbound

# 5. Increase timeout
python3 login.py \
  --email myemail@gmail.com \
  --timeout 60  # Longer timeout
```

### "Proxy interference"

**Symptom**: "Connection refused" or "Host not found" with corporate proxy

**Causes**:
- Corporate firewall/proxy
- SSL/TLS man-in-the-middle inspection
- DNS filtering

**Solutions**:
```bash
# 1. Configure proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1

# 2. Test with curl
curl -I https://www.perplexity.ai

# 3. For CloakBrowser, add proxy flags
cloakbrowser \
  --proxy-server=http://proxy.company.com:8080 \
  --remote-debugging-port=9223

# 4. If SSL inspection issue, may need to trust corporate CA
# (Consult your IT team)
```

## File Permission Issues

### "Permission denied" writing cookies

**Symptom**: `Permission denied: ~/.config/perplexity/cookies.json`

**Causes**:
- Directory not writable
- File locked by another process
- umask restricting permissions

**Solutions**:
```bash
# 1. Check directory permissions
ls -la ~/.config/perplexity/

# 2. Fix if needed
mkdir -p ~/.config/perplexity
chmod 700 ~/.config/perplexity

# 3. Remove old file if locked
rm -f ~/.config/perplexity/cookies.json

# 4. Retry login
python3 login.py --email myemail@gmail.com --bw-save
```

## Getting Help

If none of these solutions work:

1. **Collect diagnostic output**:
   ```bash
   python3 health_check.py --full > diagnostics.json
   python3 bw_credentials.py show > config.json
   ```

2. **Check logs**:
   ```bash
   tail -100 ~/.perplexity-auth/logs/*.log
   ```

3. **Run with verbose logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   python3 login.py --email myemail@gmail.com 2>&1 | tee debug.log
   ```

4. **Report issue with**:
   - Error message (exact text)
   - Diagnostic output (sanitized)
   - Steps to reproduce
   - Environment info (Python version, OS, etc.)
