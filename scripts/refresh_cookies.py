#!/usr/bin/env python3
"""
refresh_cookies.py — Deterministic Perplexity cookie refresh pipeline.

One-shot workflow:
  1. Run perplexity-login skill (CloakBrowser CDP + Gmail OTP)
  2. Update BWS perplexity-cookies secret
  3. Verify PPLX CLI pro mode works

Usage:
    .venv/bin/python scripts/refresh_cookies.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# ─── Configuration ───────────────────────────────────────────────────────────

# Paths
PPLX_ROOT = Path(__file__).resolve().parent.parent
LOGIN_SCRIPT = PPLX_ROOT / "scripts" / "login.py"
COOKIE_PATH = Path.home() / ".config" / "perplexity" / "cookies.json"

# Login settings
LOGIN_EMAIL = "vb.mrme00@gmail.com"
FORWARD_TO = "mrme000.m0@gmail.com"
OTP_APP_PASSWORD = "fqoi ycoa zwvg mpsq"
BW_ITEM = "perplexity-login"
OTP_TIMEOUT = 120  # seconds

# BWS settings
BWS_PROJECT_NAME = "pplx"
BWS_SECRET_KEY = "perplexity-cookies"
BW_NOTE_NAME = "perplexity.ai"

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _run(cmd: list[str], cwd: Optional[Path] = None, timeout: int = 300) -> tuple[int, str, str]:
    """Run a subprocess command and return (returncode, stdout, stderr)."""
    print(f"[run] {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


def _kill_cdp_port(port: int = 9223) -> None:
    """Kill any process listening on the CDP port."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split()
            for pid in pids:
                subprocess.run(["kill", "-9", pid], capture_output=True)
            time.sleep(1)
        print("Killed any CDP processes", file=sys.stderr)
    except Exception:
        print("Killed any CDP processes", file=sys.stderr)


def step1_login(headless: bool = False) -> dict:
    """
    Step 1: Run perplexity-login skill to fetch fresh cookies.
    
    Args:
        headless: Run CloakBrowser in headless mode (no GUI).
    
    Returns:
        dict: Extracted cookies.
    
    Raises:
        RuntimeError: If login fails.
    """
    print("\n" + "=" * 60)
    print("STEP 1: Fetch fresh cookies via CloakBrowser CDP + Gmail OTP")
    if headless:
        print("Mode: headless (no GUI)")
    print("=" * 60)

    # Ensure no stale CDP process
    _kill_cdp_port(9223)

    if not LOGIN_SCRIPT.exists():
        raise RuntimeError(f"Login script not found: {LOGIN_SCRIPT}")

    # First attempt: reuse persisted profile (fast path if already logged in)
    cmd = [
        sys.executable,
        str(LOGIN_SCRIPT),
        "--email", LOGIN_EMAIL,
        "--forward-to", FORWARD_TO,
        "--otp-app-password", OTP_APP_PASSWORD,
        "--bw-item", BW_ITEM,
        "--bw-save",
        "--otp-timeout", str(OTP_TIMEOUT),
        "--reuse-profile",
    ]
    if headless:
        cmd.append("--headless")

    returncode, stdout, stderr = _run(cmd, timeout=OTP_TIMEOUT + 60)

    # Print stderr for visibility
    if stderr:
        print(stderr, file=sys.stderr)

    # If reuse-profile failed, try full login with fresh profile
    if returncode != 0:
        print("\n[retry] Persisted profile failed — attempting full login…", file=sys.stderr)
        _kill_cdp_port(9223)
        cmd = [
            sys.executable,
            str(LOGIN_SCRIPT),
            "--email", LOGIN_EMAIL,
            "--forward-to", FORWARD_TO,
            "--otp-app-password", OTP_APP_PASSWORD,
            "--bw-item", BW_ITEM,
            "--bw-save",
            "--otp-timeout", str(OTP_TIMEOUT),
        ]
        if headless:
            cmd.append("--headless")

        returncode, stdout, stderr = _run(cmd, timeout=OTP_TIMEOUT + 60)
        if stderr:
            print(stderr, file=sys.stderr)

        if returncode != 0:
            raise RuntimeError(f"Login script failed with code {returncode}")

    # Read cookies from the saved file
    if not COOKIE_PATH.exists():
        raise RuntimeError(f"Cookies file not created: {COOKIE_PATH}")

    with open(COOKIE_PATH, "r") as f:
        cookies = json.load(f)

    session_token = cookies.get("__Secure-next-auth.session-token", "")
    print(f"[ok] Extracted {len(cookies)} cookies (session token: {len(session_token)} chars)")
    return cookies


def _get_bws_client():
    """Get authenticated BWS client."""
    from pplx.bws_auth import get_bws_client
    return get_bws_client()


def _get_or_create_project(client, name: str):
    """Get or create a BWS project."""
    from pplx.bws_auth import get_or_create_project
    return get_or_create_project(name, client=client)


def _get_secret_by_key(key: str, project_id: str, client):
    """Look up a BWS secret by key."""
    from pplx.bws_auth import get_secret_by_key
    return get_secret_by_key(key, project_id, client=client)


def step2_update_bws(cookies: dict) -> None:
    """
    Step 2: Update BWS perplexity-cookies secret with fresh cookies.
    
    Args:
        cookies: Fresh cookies dict from Step 1.
    
    Raises:
        RuntimeError: If BWS update fails.
    """
    print("\n" + "=" * 60)
    print("STEP 2: Update BWS perplexity-cookies secret")
    print("=" * 60)

    try:
        client = _get_bws_client()
        project = _get_or_create_project(client, BWS_PROJECT_NAME)
        secret = _get_secret_by_key(BWS_SECRET_KEY, project.id, client)

        cookies_json = json.dumps(cookies, indent=2)

        if secret:
            # Update existing
            result = client.secrets().update(
                id=secret.id,
                key=BWS_SECRET_KEY,
                value=cookies_json,
                note="Perplexity session cookies - auto-refreshed",
                organization_id=os.getenv("BITWARDEN_ORG_ID", ""),
                project_ids=[project.id],
            )
            print(f"[ok] Updated BWS secret '{BWS_SECRET_KEY}' (id: {secret.id})")
        else:
            # Create new
            result = client.secrets().create(
                key=BWS_SECRET_KEY,
                value=cookies_json,
                note="Perplexity session cookies - auto-refreshed",
                organization_id=os.getenv("BITWARDEN_ORG_ID", ""),
                project_ids=[project.id],
            )
            print(f"[ok] Created BWS secret '{BWS_SECRET_KEY}'")

        # Also sync to Bitwarden vault secure note for legacy compatibility
        _sync_to_bw_vault(cookies)

    except Exception as e:
        raise RuntimeError(f"BWS update failed: {e}")


def _sync_to_bw_vault(cookies: dict) -> None:
    """Sync cookies to Bitwarden vault secure note (legacy fallback)."""
    try:
        # Unlock vault
        bw_pass = subprocess.run(
            ["security", "find-generic-password", "-a", "bw-master-password", "-w"],
            capture_output=True, text=True
        ).stdout.strip()

        if not bw_pass:
            print("[warn] Cannot get bw master password from Keychain", file=sys.stderr)
            return

        session = subprocess.run(
            ["bw", "unlock", "--passwordenv", "BW_PASSWORD", "--raw"],
            env={**os.environ, "BW_PASSWORD": bw_pass},
            capture_output=True, text=True
        ).stdout.strip()

        # Search for existing note
        list_result = subprocess.run(
            ["bw", "list", "items", "--search", BW_NOTE_NAME],
            env={**os.environ, "BW_SESSION": session},
            capture_output=True, text=True
        )

        if list_result.returncode != 0:
            print(f"[warn] bw list failed: {list_result.stderr}", file=sys.stderr)
            return

        items = json.loads(list_result.stdout or "[]")
        notes = [i for i in items if i.get("name") == BW_NOTE_NAME and i.get("type") == 2]

        cookies_json = json.dumps(cookies, indent=2)

        def _bw_encode(data: dict) -> str:
            """Encode item JSON for bw CLI (required by edit/create)."""
            result = subprocess.run(
                ["bw", "encode"],
                input=json.dumps(data),
                capture_output=True, text=True
            )
            return result.stdout.strip()

        if notes:
            # Update existing
            item_id = notes[0]["id"]
            get_result = subprocess.run(
                ["bw", "get", "item", item_id],
                env={**os.environ, "BW_SESSION": session},
                capture_output=True, text=True
            )
            if get_result.returncode == 0:
                item = json.loads(get_result.stdout)
                item["notes"] = cookies_json
                encoded = _bw_encode(item)
                edit_result = subprocess.run(
                    ["bw", "edit", "item", item_id, encoded],
                    env={**os.environ, "BW_SESSION": session},
                    capture_output=True, text=True
                )
                if edit_result.returncode == 0:
                    print(f"[ok] Updated Bitwarden vault note '{BW_NOTE_NAME}'")
                else:
                    print(f"[warn] bw edit failed: {edit_result.stderr}", file=sys.stderr)
        else:
            # Create new secure note
            template_result = subprocess.run(
                ["bw", "get", "template", "item"],
                env={**os.environ, "BW_SESSION": session},
                capture_output=True, text=True
            )
            if template_result.returncode == 0:
                template = json.loads(template_result.stdout)
                template["type"] = 2
                template["name"] = BW_NOTE_NAME
                template["notes"] = cookies_json
                encoded = _bw_encode(template)
                create_result = subprocess.run(
                    ["bw", "create", "item", encoded],
                    env={**os.environ, "BW_SESSION": session},
                    capture_output=True, text=True
                )
                if create_result.returncode == 0:
                    print(f"[ok] Created Bitwarden vault note '{BW_NOTE_NAME}'")
                else:
                    print(f"[warn] bw create failed: {create_result.stderr}", file=sys.stderr)

    except Exception as e:
        print(f"[warn] Bitwarden vault sync failed: {e}", file=sys.stderr)


def step3_verify() -> None:
    """
    Step 3: Verify PPLX CLI works with pro mode.
    
    Raises:
        RuntimeError: If verification fails.
    """
    print("\n" + "=" * 60)
    print("STEP 3: Verify PPLX CLI pro mode")
    print("=" * 60)

    # Test 3a: profile
    print("\n[verify] Testing: pplx profile")
    returncode, stdout, stderr = _run(["pplx", "profile"], timeout=15)

    if returncode != 0:
        raise RuntimeError(f"pplx profile failed: {stderr}")

    try:
        profile = json.loads(stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"pplx profile returned invalid JSON: {stdout[:200]}")

    email = profile.get("email", "")
    tier = profile.get("subscription_tier", "")
    status = profile.get("subscription_status", "")

    print(f"[ok] Profile: {email}, tier={tier}, status={status}")

    if not email:
        raise RuntimeError("Not authenticated — no email in profile")
    if tier != "pro":
        raise RuntimeError(f"Expected pro tier, got: {tier}")
    if status != "active":
        raise RuntimeError(f"Expected active status, got: {status}")

    # Test 3b: pro search
    print("\n[verify] Testing: pplx search --mode pro")
    returncode, stdout, stderr = _run(
        ["pplx", "search", "What is 2+2?", "--mode", "pro"],
        timeout=60
    )

    if returncode != 0:
        raise RuntimeError(f"pplx search --mode pro failed: {stderr}")

    if not stdout.strip():
        raise RuntimeError("pplx search returned empty output")

    # Check for pro-mode indicators (citations or non-error response)
    output = stdout.strip()
    if "Sign up" in output or "repeat your request" in output:
        raise RuntimeError(f"Pro mode rejected: {output[:200]}")

    # Show first line of output
    first_line = output.split("\n")[0][:80]
    print(f"[ok] Pro search response: {first_line}...")

    # Test 3c: models list
    print("\n[verify] Testing: pplx models")
    returncode, stdout, stderr = _run(["pplx", "models"], timeout=10)

    if returncode != 0:
        raise RuntimeError(f"pplx models failed: {stderr}")

    if "PRO:" not in stdout:
        raise RuntimeError("Models list missing PRO section")

    print("[ok] Models listing works")


def main() -> int:
    """
    Main entry point: run the full deterministic refresh pipeline.
    
    Returns:
        0 on success, 1 on failure.
    """
    import argparse
    parser = argparse.ArgumentParser(
        description="PPLX Cookie Refresh — deterministic pipeline"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run CloakBrowser in headless mode (no GUI window)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PPLX Cookie Refresh Pipeline")
    print("=" * 60)
    print(f"Login email:     {LOGIN_EMAIL}")
    print(f"OTP forward-to:  {FORWARD_TO}")
    print(f"Cookie path:     {COOKIE_PATH}")
    print(f"BWS secret:      {BWS_SECRET_KEY}")
    if args.headless:
        print("Mode:            headless")
    print("=" * 60)

    try:
        # Step 1: Fetch cookies
        cookies = step1_login(headless=args.headless)

        # Step 2: Update BWS
        step2_update_bws(cookies)

        # Step 3: Verify
        step3_verify()

        print("\n" + "=" * 60)
        print("ALL STEPS PASSED — PPLX CLI is fully operational")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"FAILED: {e}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
