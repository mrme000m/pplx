#!/usr/bin/env python3
"""
extract_otp.py — Fetch Perplexity sign-in OTP from Gmail via IMAP.

Perplexity sends a magic-link email to the login address. The 6-digit token
embedded in the callback URL is the OTP needed for the verification page.

Supports:
  - Direct IMAP access to the login email inbox
  - Checking a forwarding inbox (when login email forwards to another Gmail)
  - Fallback to Bitwarden for app password retrieval

Usage:
  python3 extract_otp.py \
      --email vb.mrme00@gmail.com \
      --app-password "fqoi ycoa zwvg mpsq"

  python3 extract_otp.py \
      --email vb.mrme00@gmail.com \
      --forward-to mrme000.m0@gmail.com \
      --bw-item "myaccount.google.com"

Output (JSON):
  {"otp": "873106", "sender": "team@mail.perplexity.ai", "subject": "Sign in to Perplexity"}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running standalone: fix up import path if needed
if __name__ == "__main__":
    _script_dir = Path(__file__).resolve().parent
    _skills_dir = _script_dir.parent.parent
    sys.path.insert(0, str(_skills_dir))

from scripts.auth.otp_utils import (  # noqa: E402
    fetch_otp,
    get_app_password_from_bw,
    get_email_from_bw,
    poll_for_otp,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract Perplexity sign-in OTP from Gmail"
    )
    parser.add_argument("--email", help="Gmail address to check (the Perplexity login email)")
    parser.add_argument("--app-password", help="Gmail app password")
    parser.add_argument("--forward-to", help="If email forwards to another inbox, check this one")
    parser.add_argument("--bw-item", default="perplexity-login",
                        help="Bitwarden item name for credentials (default: perplexity-login)")
    parser.add_argument("--bw-field", default="gmail",
                        help="Bitwarden custom field name for app password (default: gmail)")
    parser.add_argument("--lookback", type=int, default=15,
                        help="Minutes to look back for OTP email (default: 15)")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Seconds to keep polling for OTP (default: 120)")
    parser.add_argument("--poll-interval", type=int, default=5,
                        help="Seconds between polls (default: 5)")
    args = parser.parse_args()

    # Resolve credentials
    email_addr = args.email
    app_password = args.app_password

    if args.forward_to:
        email_addr = args.forward_to

    if not email_addr or not app_password:
        # Try Bitwarden
        if args.bw_item:
            if not email_addr:
                email_addr = get_email_from_bw(args.bw_item)
                if email_addr:
                    print(f"Got email from Bitwarden: {email_addr}", file=sys.stderr)
            if not app_password:
                app_password = get_app_password_from_bw(args.bw_item, args.bw_field)
                if app_password:
                    print(f"Got app password from Bitwarden", file=sys.stderr)

    if not email_addr:
        print(json.dumps({"error": "No email address provided", "otp": None}))
        return 1
    if not app_password:
        print(json.dumps({"error": "No app password provided", "otp": None}))
        return 1

    print(f"Polling Gmail for OTP (timeout={args.timeout}s)...", file=sys.stderr)

    otp = poll_for_otp(
        email_addr=email_addr,
        app_password=app_password,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
        lookback_minutes=args.lookback,
    )

    if otp:
        # Re-fetch full result for JSON output
        result = fetch_otp(email_addr, app_password, lookback_minutes=args.lookback)
        if result:
            print(json.dumps(result))
        else:
            print(json.dumps({"otp": otp, "sender": "team@mail.perplexity.ai",
                             "subject": "Sign in to Perplexity"}))
        return 0

    print(json.dumps({"error": "OTP not found within timeout", "otp": None}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
