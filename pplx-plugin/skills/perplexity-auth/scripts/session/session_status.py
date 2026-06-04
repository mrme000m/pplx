#!/usr/bin/env python3
"""
Session status checker - verifies Perplexity session validity.
"""

import argparse
import json
import sys
from pathlib import Path


COOKIES_PATH = Path("~/.config/perplexity/cookies.json").expanduser()


def check_disk_cookies() -> dict:
    if not COOKIES_PATH.exists():
        return {"status": "missing", "path": str(COOKIES_PATH)}

    try:
        data = json.loads(COOKIES_PATH.read_text())
        cookies = data.get("cookies", {})
        return {
            "status": "present",
            "count": len(cookies),
            "last_saved": data.get("last_saved"),
            "keys": list(cookies.keys()),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def validate_with_api() -> dict:
    try:
        from pplx_sdk import PerplexityClient
        client = PerplexityClient()
        session = client.get_session()
        if session:
            return {
                "status": "valid",
                "user": session.get("user", {}).get("email", "unknown"),
            }
        return {"status": "invalid"}
    except ImportError:
        return {"status": "sdk_not_available"}
    except Exception as e:
        return {"status": "api_error", "error": str(e)}


def check_bitwarden() -> dict:
    import subprocess
    result = subprocess.run(
        ["bw", "list", "items", "--search", "perplexity.ai"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"status": "bw_error", "error": result.stderr}

    try:
        items = json.loads(result.stdout)
        for item in items:
            if item.get("name") == "perplexity.ai":
                return {"status": "present", "id": item.get("id")}
        return {"status": "not_found"}
    except Exception as e:
        return {"status": "parse_error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Session status checker")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--validate", action="store_true", help="Also validate via API")
    args = parser.parse_args()

    disk = check_disk_cookies()
    bw = check_bitwarden()

    if args.verbose:
        print("Disk cookies:", json.dumps(disk, indent=2))
        print("Bitwarden:", json.dumps(bw, indent=2))
    else:
        print(f"Disk: {disk['status']}")
        print(f"Bitwarden: {bw['status']}")

    if args.validate:
        api = validate_with_api()
        if args.verbose:
            print("API validation:", json.dumps(api, indent=2))
        else:
            print(f"API: {api['status']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())