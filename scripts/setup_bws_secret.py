#!/usr/bin/env python3
"""Bootstrap script for Bitwarden Secrets Manager integration with PPLX.

Prerequisites:
  - bitwarden-sdk installed   (pip install -e .)
  - BITWARDEN_CLIENT_ID and BITWARDEN_CLIENT_SECRET set in .env

Usage:
  python scripts/setup_bws_secret.py --create-token
  python scripts/setup_bws_secret.py --setup-cookies /path/to/cookies.json
  python scripts/setup_bws_secret.py --show
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure pplx package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pplx.config import load_project_env
from pplx.bws_auth import (
    get_user_access_token,
    get_sm_service_account_token,
    get_bws_client,
    get_or_create_project,
    create_or_update_secret,
    get_secret_by_key,
)

load_project_env()
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _write_env(key: str, value: str):
    """Append or update a key in .env."""
    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text().splitlines()

    prefix = f"{key}="
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(prefix) or line.startswith(f"# {key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break

    if not updated:
        lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(lines) + "\n")
    print(f"   Updated .env: {key}=<redacted>")


def cmd_create_token(args):
    """Create a BWS service-account access token and store it in .env."""
    print("Step 1 / 3: Authenticating with Bitwarden identity server...")
    try:
        user_token = get_user_access_token()
        print("   User access token obtained successfully.")
    except RuntimeError as e:
        print(f"   ERROR: {e}")
        sys.exit(1)

    print("\nStep 2 / 3: Creating / locating SM service account...")
    try:
        bws_token = get_sm_service_account_token(token=user_token)
        print("   Service-account access token created.")
    except RuntimeError as e:
        print(f"   ERROR: {e}")
        sys.exit(1)

    print("\nStep 3 / 3: Saving BWS_ACCESS_TOKEN to .env")
    _write_env("BWS_ACCESS_TOKEN", bws_token)
    print("\nDone. You can now use PPLX with Bitwarden Secrets Manager.")
    print("Run:  python scripts/setup_bws_secret.py --show")


def cmd_setup_cookies(args):
    """Upload existing cookies JSON into BWS as a secret."""
    cookie_path = Path(args.file)
    if not cookie_path.exists():
        print(f"ERROR: File not found: {cookie_path}")
        sys.exit(1)

    raw = cookie_path.read_text()
    # Validate JSON
    try:
        json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in cookie file: {e}")
        sys.exit(1)

    print("Step 1 / 2: Connecting to BWS...")
    client = get_bws_client()
    print("   Authenticated.")

    print("\nStep 2 / 2: Creating / updating 'perplexity-cookies' secret...")
    project = get_or_create_project("pplx", client=client)
    secret = create_or_update_secret(
        key="perplexity-cookies",
        value=raw,
        project_id=project.id,
        note="Perplexity AI session cookies (auto-managed by pplx)",
        client=client,
    )
    print(f"   Secret saved. ID: {secret.id}")
    print("\nDone. PPLX will now load cookies from Secrets Manager.")


def cmd_show(args):
    """Show current BWS project and secret status."""
    print("Checking BWS configuration...\n")
    client = get_bws_client()
    project = get_or_create_project("pplx", client=client)
    print(f"Project 'pplx' ID: {project.id}")

    secret = get_secret_by_key("perplexity-cookies", project.id, client=client)
    if secret:
        print(f"Secret 'perplexity-cookies' ID: {secret.id}")
        print(f"  Note: {secret.note}")
        print(f"  Value chars: {len(secret.value)}")
        # Validate JSON
        try:
            cookies = json.loads(secret.value)
            print(f"  Valid JSON with {len(cookies)} cookie key(s).")
        except json.JSONDecodeError:
            print("  WARNING: Value is NOT valid JSON!")
    else:
        print("Secret 'perplexity-cookies' not found in project.")
        print("Run: python scripts/setup_bws_secret.py --setup-cookies <file>")


def main():
    p = argparse.ArgumentParser(
        description="Bootstrap Bitwarden Secrets Manager for PPLX"
    )
    sub = p.add_subparsers(dest="command")

    tok = sub.add_parser("create-token", help="Create a BWS service-account token")
    tok.set_defaults(func=cmd_create_token)

    setup = sub.add_parser(
        "setup-cookies", help="Upload a cookie JSON file into BWS"
    )
    setup.add_argument("file", help="Path to cookies JSON file")
    setup.set_defaults(func=cmd_setup_cookies)

    show = sub.add_parser("show", help="Show BWS project/secret status")
    show.set_defaults(func=cmd_show)

    args = p.parse_args()
    if not hasattr(args, "func"):
        p.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
