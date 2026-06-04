#!/usr/bin/env python3
"""
Bitwarden cookie storage for Perplexity session.
Stores cookies as JSON in a Bitwarden Secure Note.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


BW_ITEM_NAME = "perplexity.ai"
COOKIES_PATH = Path("~/.config/perplexity/cookies.json").expanduser()


class CookieManager:
    def __init__(self, item_name: str = BW_ITEM_NAME, cookies_path: Path = COOKIES_PATH):
        self.item_name = item_name
        self.cookies_path = cookies_path
        self.bw = os.environ.get("BW", "bw")

    def _run_bw(self, args: list) -> dict:
        result = subprocess.run(
            [self.bw] + args,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"bw CLI failed: {result.stderr}")
        try:
            return json.loads(result.stdout)
        except Exception:
            return {}

    def _get_item(self) -> dict:
        try:
            items = self._run_bw(["list", "items", "--search", self.item_name])
            for item in items:
                if item.get("name") == self.item_name:
                    return item
        except Exception:
            pass
        return {}

    def _ensure_dir(self):
        self.cookies_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, cookies: dict) -> bool:
        self._ensure_dir()
        data = {
            "cookies": cookies,
            "last_saved": datetime.utcnow().isoformat() + "Z",
        }
        self.cookies_path.write_text(json.dumps(data, indent=2))

        item = self._get_item()
        item_id = item.get("id")

        json_data = json.dumps({
            "name": self.item_name,
            "notes": json.dumps(data),
            "fields": [{"name": "source", "value": "perplexity-auth skill"}],
        })

        if item_id:
            cmd = [self.bw, "edit", "item", item_id, "--json", json_data]
        else:
            cmd = [self.bw, "create", "item", "--json", json_data]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def load(self) -> dict:
        item = self._get_item()
        if not item:
            return {}

        notes = item.get("notes", "")
        if not notes:
            return {}

        try:
            return json.loads(notes)
        except Exception:
            return {}

    def delete(self) -> bool:
        item = self._get_item()
        item_id = item.get("id")
        if not item_id:
            return True
        result = subprocess.run(
            [self.bw, "delete", "item", item_id],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def status(self) -> dict:
        result = {
            "disk": {"exists": False, "path": str(self.cookies_path)},
            "bitwarden": {"exists": False},
        }

        if self.cookies_path.exists():
            try:
                data = json.loads(self.cookies_path.read_text())
                result["disk"]["exists"] = True
                result["disk"]["cookie_count"] = len(data.get("cookies", {}))
                result["disk"]["last_saved"] = data.get("last_saved", "unknown")
            except Exception:
                result["disk"]["error"] = "Failed to parse cookies file"

        item = self._get_item()
        if item.get("id"):
            result["bitwarden"]["exists"] = True
            result["bitwarden"]["id"] = item["id"]

        return result


def main():
    parser = argparse.ArgumentParser(description="Bitwarden cookie manager")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("save", help="Save cookies to Bitwarden")
    sub.add_parser("load", help="Load cookies from Bitwarden")
    sub.add_parser("status", help="Show disk and Bitwarden cookie status")
    sub.add_parser("delete", help="Delete cookies from Bitwarden")

    args = parser.parse_args()
    cm = CookieManager()

    if args.cmd == "status":
        status = cm.status()
        print(json.dumps(status, indent=2))
        return 0

    if args.cmd == "save":
        if not COOKIES_PATH.exists():
            print(f"No cookies at {COOKIES_PATH}")
            return 1
        data = json.loads(COOKIES_PATH.read_text())
        cookies = data.get("cookies", {})
        ok = cm.save(cookies)
        print("OK" if ok else "FAILED")
        return 0 if ok else 1

    if args.cmd == "load":
        data = cm.load()
        if not data:
            print("No cookies in Bitwarden")
            return 1
        cm._ensure_dir()
        COOKIES_PATH.write_text(json.dumps(data, indent=2))
        print(f"Loaded to {COOKIES_PATH}")
        return 0

    if args.cmd == "delete":
        ok = cm.delete()
        print("OK" if ok else "FAILED")
        return 0 if ok else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())