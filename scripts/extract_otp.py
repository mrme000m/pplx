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
  python3 extract_otp.py \\
      --email vb.mrme00@gmail.com \\
      --app-password "fqoi ycoa zwvg mpsq"

  python3 extract_otp.py \\
      --email vb.mrme00@gmail.com \\
      --forward-to mrme000.m0@gmail.com \\
      --bw-item "myaccount.google.com"

Output (JSON):
  {"otp": "873106", "sender": "team@mail.perplexity.ai", "subject": "Sign in to Perplexity"}
"""

from __future__ import annotations

import argparse
import email
import imaplib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional


# ─── Bitwarden integration ───────────────────────────────────────────────────

def _bw(cmd: list[str]) -> str:
    """Run bw command with unlocked session."""
    try:
        bw_pass = subprocess.run(
            ["security", "find-generic-password", "-a", "bw-master-password", "-w"],
            capture_output=True, text=True
        ).stdout.strip()

        if not bw_pass:
            raise RuntimeError("Could not get bw master password from Keychain")

        session = subprocess.run(
            ["bw", "unlock", "--passwordenv", "BW_PASSWORD", "--raw"],
            env={**os.environ, "BW_PASSWORD": bw_pass},
            capture_output=True, text=True
        ).stdout.strip()

        if not session:
            raise RuntimeError("Could not unlock Bitwarden vault")

        result = subprocess.run(
            ["bw", *cmd],
            env={**os.environ, "BW_SESSION": session},
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Bitwarden error: {e}", file=sys.stderr)
        return ""


def get_app_password_from_bw(item_name: str, field_name: str = "gmail") -> Optional[str]:
    """Get app password from a Bitwarden login item's custom field."""
    raw = _bw(["get", "item", item_name])
    if not raw:
        return None
    try:
        item = json.loads(raw)
    except json.JSONDecodeError:
        return None

    for field in item.get("fields", []):
        if field.get("name") == field_name:
            return field.get("value")
    return None


def get_email_from_bw(item_name: str) -> Optional[str]:
    """Get email/username from a Bitwarden login item."""
    raw = _bw(["get", "item", item_name])
    if not raw:
        return None
    try:
        item = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return item.get("login", {}).get("username")


# ─── IMAP OTP extraction ─────────────────────────────────────────────────────

def fetch_otp(
    email_addr: str,
    app_password: str,
    imap_server: str = "imap.gmail.com",
    lookback_minutes: int = 15,
) -> Optional[dict]:
    """
    Check inbox for a Perplexity sign-in email and extract the 6-digit token.

    Returns dict with otp, sender, subject, or None if not found.
    """
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_addr, app_password)
        mail.select("INBOX")

        # Search for recent Perplexity sign-in emails
        since_date = (datetime.now() - timedelta(minutes=lookback_minutes)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(FROM "team@mail.perplexity.ai" SINCE "{since_date}")')
        ids = messages[0].split()

        if not ids:
            # Fallback: broader search
            status, messages = mail.search(None, f'(SUBJECT "Sign in to Perplexity" SINCE "{since_date}")')
            ids = messages[0].split()

        if not ids:
            return None

        # Process newest first
        for mid in reversed(ids):
            status, msg_data = mail.fetch(mid, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = msg.get("Subject", "")
            sender = msg.get("From", "")

            # Extract body
            body = ""
            for part in msg.walk():
                ct = part.get_content_type()
                if ct in ("text/plain", "text/html"):
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        body = part.get_payload(decode=True).decode(charset, errors="replace")
                    except Exception:
                        pass
                    if ct == "text/plain":
                        break

            # Look for token in callback URL
            # Pattern: ...&token=123456 or token%3D123456
            token_match = re.search(r"[&?]token[=%]3?[Dd]?(\d{6})", body)
            if token_match:
                mail.logout()
                return {
                    "otp": token_match.group(1),
                    "sender": sender,
                    "subject": subject.strip(),
                }

            # Fallback: any 6-digit code in body
            codes = re.findall(r"\b(\d{6})\b", body)
            if codes:
                # Heuristic: prefer codes that appear multiple times (embedded in URLs)
                from collections import Counter
                counts = Counter(codes)
                best = counts.most_common(1)[0][0]

                mail.logout()
                return {
                    "otp": best,
                    "sender": sender,
                    "subject": subject.strip(),
                }

        mail.logout()
        return None

    except imaplib.IMAP4.error as e:
        raise RuntimeError(f"IMAP login failed: {e}") from e
    except Exception as e:
        raise RuntimeError(f"IMAP error: {e}") from e


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract Perplexity sign-in OTP from Gmail"
    )
    parser.add_argument("--email", help="Gmail address to check (the Perplexity login email)")
    parser.add_argument("--app-password", help="Gmail app password")
    parser.add_argument("--forward-to", help="If email forwards to another inbox, check this one")
    parser.add_argument("--bw-item", default="myaccount.google.com",
                        help="Bitwarden item name for credentials (default: myaccount.google.com)")
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
        print(json.dumps({"error": "No email address provided", "otp": None}), file=sys.stderr)
        return 1
    if not app_password:
        print(json.dumps({"error": "No app password provided", "otp": None}), file=sys.stderr)
        return 1

    # Poll for OTP
    import time
    deadline = time.time() + args.timeout

    while time.time() < deadline:
        try:
            result = fetch_otp(email_addr, app_password, lookback_minutes=args.lookback)
            if result:
                print(json.dumps(result))
                return 0
        except Exception as e:
            print(f"Poll error: {e}", file=sys.stderr)

        time.sleep(args.poll_interval)

    print(json.dumps({"error": "OTP not found within timeout", "otp": None}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
