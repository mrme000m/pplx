#!/usr/bin/env python3
"""
otp_utils.py — Shared OTP extraction logic for Perplexity authentication.

Pulled out from extract_otp.py for use by both standalone script and login.py.
Supports IMAP polling, Bitwarden credential fetch, and automatic retry.
"""

from __future__ import annotations

import email
import imaplib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional
import pathlib


def _bw_unlock() -> str:
    """Unlock Bitwarden and return session token (or None if unavailable)."""
    try:
        bw_pass = subprocess.run(
            ["security", "find-generic-password", "-a", "bw-master-password", "-w"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
        if not bw_pass:
            return ""
        result = subprocess.run(
            ["bw", "unlock", "--passwordenv", "BW_PASSWORD", "--raw"],
            env={**os.environ, "BW_PASSWORD": bw_pass},
            capture_output=True, text=True, timeout=30
        )
        session = result.stdout.strip()
        return session if "!" not in session else ""
    except Exception:
        return ""


def _bw_cmd(cmd: list[str]) -> str:
    """Run a BW CLI command (auto-unlocks vault)."""
    session = _bw_unlock()
    if not session:
        return ""
    result = subprocess.run(
        ["bw"] + cmd,
        env={**os.environ, "BW_SESSION": session},
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()


def get_app_password_from_bw(item_name: str, field_name: str = "gmail") -> Optional[str]:
    """Get app password from a Bitwarden login item's custom field."""
    raw = _bw_cmd(["get", "item", item_name])
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
    raw = _bw_cmd(["get", "item", item_name])
    if not raw:
        return None
    try:
        item = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return item.get("login", {}).get("username")


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

        since_date = (datetime.now() - timedelta(minutes=lookback_minutes)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(FROM "team@mail.perplexity.ai" SINCE "{since_date}")')
        ids = messages[0].split()

        if not ids:
            # Fallback: broader subject search
            status, messages = mail.search(
                None,
                f'(SUBJECT "Sign in to Perplexity" SINCE "{since_date}")'
            )
            ids = messages[0].split()

        if not ids:
            mail.logout()
            return None

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

            # Look for token in callback URL: &token=123456 or token%3D123456
            token_match = re.search(r"[&?]token[=%]3?[Dd]?(\d{6})", body)
            if token_match:
                mail.logout()
                return {
                    "otp": token_match.group(1),
                    "sender": sender,
                    "subject": subject.strip(),
                }

            # Fallback: any 6-digit code in body — prefer the most common one
            codes = re.findall(r"\b(\d{6})\b", body)
            if codes:
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


def poll_for_otp(
    email_addr: str,
    app_password: str,
    timeout: int = 120,
    poll_interval: int = 5,
    lookback_minutes: int = 15,
) -> Optional[str]:
    """Poll IMAP for an OTP within a deadline. Returns the OTP string or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            result = fetch_otp(email_addr, app_password, lookback_minutes=lookback_minutes)
            if result:
                return result["otp"]
        except Exception as e:
            print(f"Poll error: {e}", file=sys.stderr)
        time.sleep(poll_interval)
    return None
