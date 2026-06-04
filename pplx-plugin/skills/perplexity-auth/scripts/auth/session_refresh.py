#!/usr/bin/env python3
"""
Session refresh - checks session validity and re-authenticates if needed.
"""

import argparse
import json
import sys
from pathlib import Path


def get_session_status() -> dict:
    cookies_path = Path("~/.config/perplexity/cookies.json").expanduser()
    if not cookies_path.exists():
        return {"status": "no_cookies", "message": "No cookies file found"}

    try:
        data = json.loads(cookies_path.read_text())
        cookies = data.get("cookies", {})
        last_saved = data.get("last_saved", "unknown")

        if not cookies:
            return {"status": "empty", "message": "Cookies file is empty"}

        return {
            "status": "cookies_present",
            "cookie_count": len(cookies),
            "last_saved": last_saved,
            "cookies": list(cookies.keys()),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def validate_session_via_api() -> bool:
    try:
        from pplx_sdk import PerplexityClient
        client = PerplexityClient()
        session = client.get_session()
        return session is not None
    except Exception:
        return False


def refresh_session(force: bool = False) -> dict:
    status = get_session_status()

    if status["status"] == "no_cookies" or force:
        print("No cookies or force=True. Running full login...")
        from .login import main as login_main
        login_main()
        return get_session_status()

    if validate_session_via_api():
        return {"status": "valid", "message": "Session is active"}

    print("Session expired. Attempting to reload from Bitwarden...")
    try:
        from ..session.bw_cookies import CookieManager
        cm = CookieManager()
        cookies_data = cm.load()
        if cookies_data:
            cookies_path.write_text(json.dumps(cookies_data))
            if validate_session_via_api():
                return {"status": "refreshed", "message": "Session restored from Bitwarden"}
    except Exception as e:
        pass

    print("All refresh options exhausted. Run login manually.")
    return {"status": "failed", "message": "Re-authentication required"}


def main():
    parser = argparse.ArgumentParser(description="Perplexity session management")
    parser.add_argument("--status", action="store_true", help="Show session status")
    parser.add_argument("--validate", action="store_true", help="Validate session via API")
    parser.add_argument("--refresh", action="store_true", help="Refresh session if expired")
    parser.add_argument("--force", action="store_true", help="Force full re-authentication")
    args = parser.parse_args()

    if args.status:
        status = get_session_status()
        print(json.dumps(status, indent=2))
        return 0

    if args.validate:
        valid = validate_session_via_api()
        print(f"Session valid: {valid}")
        return 0 if valid else 1

    if args.refresh:
        result = refresh_session(force=args.force)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] in ("valid", "refreshed") else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())