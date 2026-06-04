#!/usr/bin/env python3
"""
Bitwarden credential manager for Perplexity login.
Stores email, Gmail app password, forwarding config, and browser settings.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


BW_ITEM_NAME = "perplexity-login"


class CredentialManager:
    def __init__(self):
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

    def get_item(self, name: str) -> dict:
        try:
            items = self._run_bw(["list", "items", "--search", name])
            for item in items:
                if item.get("name") == name:
                    return item
        except Exception:
            pass
        return {}

    def load(self) -> dict:
        item = self.get_item(BW_ITEM_NAME)
        if not item:
            return {}

        result = {}
        fields = item.get("fields", [])
        for f in fields:
            name = f.get("name", "")
            value = f.get("value", "")
            if name and value:
                parts = name.split(".")
                d = result
                for p in parts[:-1]:
                    d = d.setdefault(p, {})
                d[parts[-1]] = value

        login = item.get("login", {})
        result.setdefault("email", login.get("username", ""))
        result.setdefault("notes", login.get("totp", ""))

        return result

    def save(self, data: dict) -> bool:
        fields = []
        def flatten(d, prefix=""):
            for k, v in d.items():
                if isinstance(v, dict):
                    flatten(v, f"{prefix}{k}.")
                else:
                    fields.append({"name": f"{prefix}{k}", "value": str(v)})

        flatten(data)

        item = self.get_item(BW_ITEM_NAME)
        item_id = item.get("id")

        args = ["create", "item"]
        if item_id:
            args = ["edit", "item", item_id]

        name = BW_ITEM_NAME
        username = data.get("email", "")
        totp = data.get("notes", "")

        cmd = [
            self.bw, "create", "item",
            "--json",
            json.dumps({
                "name": name,
                "login": {"username": username, "totp": totp},
                "fields": fields,
            })
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def setup(
        self,
        email: str,
        gmail_app_password: str = None,
        forward_to: str = None,
        browser: str = "cloakbrowser",
        cdp_port: int = 9223,
    ) -> bool:
        data = {
            "email": email,
            "gmail": {
                "app_password": gmail_app_password or "",
                "forward_to": forward_to or "",
            },
            "browser": browser,
            "cdp_port": str(cdp_port),
        }
        return self.save(data)

    def show(self) -> dict:
        data = self.load()
        if not data:
            return {}
        if "gmail" in data and "app_password" in data.get("gmail", {}):
            data["gmail"]["app_password"] = "********"
        return data

    def set_field(self, key: str, value: str) -> bool:
        data = self.load()
        parts = key.split(".")
        d = data
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value
        return self.save(data)

    def list_items(self) -> list:
        item = self.get_item(BW_ITEM_NAME)
        if not item:
            return []
        return [{"name": BW_ITEM_NAME, "fields": list(item.get("fields", {}).keys())}]


def main():
    parser = argparse.ArgumentParser(description="Bitwarden credential manager")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("setup", help="Create/update credential item")
    p.add_argument("--email", required=True)
    p.add_argument("--gmail-app-password")
    p.add_argument("--forward-to")

    p = sub.add_parser("show", help="Display stored credentials (masked)")
    p = sub.add_parser("list", help="List credential fields")

    p = sub.add_parser("set", help="Update a single field")
    p.add_argument("--key", required=True, help="e.g., gmail.app_password")
    p.add_argument("--value", required=True)

    p = sub.add_parser("status", help="Check if item exists")
    p = sub.add_parser("load", help="Load and print credentials as JSON")

    args = parser.parse_args()
    cm = CredentialManager()

    if args.cmd == "setup":
        ok = cm.setup(
            email=args.email,
            gmail_app_password=args.gmail_app_password,
            forward_to=args.forward_to,
        )
        print("OK" if ok else "FAILED")
        return 0 if ok else 1

    if args.cmd == "show":
        data = cm.show()
        print(json.dumps(data, indent=2))
        return 0

    if args.cmd == "list":
        items = cm.list_items()
        print(json.dumps(items, indent=2))
        return 0

    if args.cmd == "set":
        ok = cm.set_field(args.key, args.value)
        print("OK" if ok else "FAILED")
        return 0 if ok else 1

    if args.cmd == "status":
        item = cm.get_item(BW_ITEM_NAME)
        exists = bool(item.get("id"))
        print(f"Item exists: {exists}")
        return 0 if exists else 1

    if args.cmd == "load":
        data = cm.load()
        print(json.dumps(data, indent=2))
        return 0 if data else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())