# Diagnostics & Verification

Guide to health checks, CLI command verification, and network traffic analysis.

## Quick Health Check

Fast validation that authentication works (30 seconds):

```bash
python3 <skill>/scripts/diagnostics/health_check.py --quick

# Output:
{
  "status": "ok",
  "auth": "authenticated",
  "session_age_days": 15,
  "session_expires_in_days": 15,
  "cookie_source": "filesystem"
}
```

Checks:
- Cookies exist (filesystem or Bitwarden)
- Session token valid (API call to /auth/session)
- Session not expired (expiry time in future)
- No immediate action required

## Full Health Check

Comprehensive diagnostic with CLI verification (5 minutes):

```bash
python3 <skill>/scripts/diagnostics/health_check.py --full

# Output:
{
  "status": "ok",
  "auth": "authenticated",
  "session_age_days": 15,
  "session_expires_in_days": 15,
  "cli_health": {
    "status": "ok",
    "commands_verified": 5,
    "commands_failed": 0,
    "commands": {
      "models": "ok",
      "credits": "ok",
      "rate-limits": "ok",
      "memories": "ok",
      "status": "ok"
    }
  },
  "endpoints_discovered": 12,
  "traffic_analysis": {
    "total_requests": 42,
    "request_types": {
      "api": 35,
      "cdn": 5,
      "analytics": 2
    }
  }
}
```

Includes:
- Quick health check
- CLI command verification (with retries)
- Network traffic capture (HAR)
- Endpoint discovery & categorization

## CLI Command Verification

Verify individual pplx CLI commands work:

```bash
python3 <skill>/scripts/diagnostics/verify_cli.py \
  --commands models,credits,status \
  --retry 3

# Output:
{
  "status": "ok",
  "commands": {
    "models": {
      "status": "ok",
      "output_lines": 12,
      "execution_time_ms": 245
    },
    "credits": {
      "status": "ok",
      "output_lines": 3,
      "execution_time_ms": 189
    },
    "status": {
      "status": "ok",
      "output_lines": 5,
      "execution_time_ms": 167
    }
  }
}
```

Options:
- `--commands` - Comma-separated list (default: all)
- `--retry` - Retry failed commands (default: 3)
- `--timeout` - Per-command timeout in seconds (default: 30)
- `--capture-har` - Save traffic as HAR file

## Network Traffic Analysis

Analyze HAR file from CLI verification or debug sessions:

```bash
python3 <skill>/scripts/diagnostics/analyze_traffic.py \
  --har-file ~/.perplexity-debug/sessions/2026-05-28-12-00-00/session.har

# Output:
{
  "status": "ok",
  "total_requests": 42,
  "api_endpoints": {
    "discovered": 12,
    "new": 3
  },
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/query/search",
      "status": 200,
      "response_time_ms": 450
    },
    ...
  ],
  "categories": {
    "api": 35,
    "cdn": 5,
    "analytics": 2
  },
  "comparison_with_baseline": {
    "matches": 9,
    "new": 3,
    "removed": 0
  }
}
```

Compares with `DISCOVERED_ENDPOINTS.md` to detect API changes.

## Common Diagnostics

### Check if session about to expire

```bash
python3 <skill>/scripts/diagnostics/health_check.py --quick

# If session_expires_in_days < 5:
# Run: python3 session_refresh.py --email myemail@gmail.com
```

### Verify all CLI commands

```bash
python3 <skill>/scripts/diagnostics/verify_cli.py --retry 3

# Check output for failed commands
# Fix errors or report to support
```

### Analyze specific endpoint

```bash
# From HAR file, find all /api/auth calls
python3 <skill>/scripts/diagnostics/analyze_traffic.py \
  --har-file session.har \
  --filter-path /api/auth

# Output: detailed analysis of auth endpoints
```

### Detect API changes

```bash
# Compare current traffic to baseline
python3 <skill>/scripts/diagnostics/analyze_traffic.py \
  --har-file session.har \
  --compare-to ~/.perplexity-auth/baselines/endpoints.json

# Output: new, removed, or changed endpoints
```

## Troubleshooting with Diagnostics

### "Session expired" error

```bash
# Step 1: Quick check
python3 health_check.py --quick

# Step 2: If expired, refresh
python3 session_refresh.py --email myemail@gmail.com

# Step 3: Re-run diagnostics
python3 health_check.py --quick
```

### "CLI command failed"

```bash
# Step 1: Verify individual command
pplx models  # Try manually

# Step 2: Run diagnostics with retry
python3 verify_cli.py --commands models --retry 5

# Step 3: Check network traffic
python3 verify_cli.py --commands models --capture-har
python3 analyze_traffic.py --har-file session.har
```

### "Unknown endpoint in traffic"

```bash
# Step 1: Capture traffic
python3 health_check.py --full

# Step 2: Analyze
python3 analyze_traffic.py --har-file session.har

# Step 3: Compare to known endpoints
# If new endpoint: update DISCOVERED_ENDPOINTS.md
```

## Exit Codes

All diagnostic scripts follow consistent exit codes:

- **0**: Success, all checks passed
- **1**: Auth failed (session invalid/expired)
- **2**: Config error (missing env vars)
- **3**: Network error (service unreachable)
- **4**: Partial failure (some checks passed, some failed)

Example:
```bash
python3 health_check.py --quick
if [ $? -eq 0 ]; then
  echo "All checks passed"
else
  echo "Diagnostics failed, check output"
fi
```

## Continuous Monitoring

### Daily Cron Job

```cron
# Run health check every morning
0 8 * * * python3 <skill>/scripts/diagnostics/health_check.py --quick \
  >> ~/.perplexity-auth/logs/health.log 2>&1

# Run full diagnostics weekly
0 8 * * 0 python3 <skill>/scripts/diagnostics/health_check.py --full \
  >> ~/.perplexity-auth/logs/health.log 2>&1
```

### Log Monitoring

```bash
# Watch health check results
tail -f ~/.perplexity-auth/logs/health.log

# Extract errors
grep "status.*error" ~/.perplexity-auth/logs/health.log

# Count by day
grep "health_check" ~/.perplexity-auth/logs/health.log | cut -d' ' -f1 | uniq -c
```

### Alert on Failure

```bash
# Add to cron job
if [ $? -ne 0 ]; then
  echo "Perplexity health check failed" | mail -s "Alert" you@example.com
fi
```
