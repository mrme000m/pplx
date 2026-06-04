#!/usr/bin/env python3
"""
Browser debug - low-level CDP browser debugging utilities.
"""

import argparse
import json
import sys
import websocket
from pathlib import Path


class BrowserDebugger:
    def __init__(self, cdp_port: int = 9223):
        self.cdp_port = cdp_port
        self.ws = None

    def connect(self) -> bool:
        try:
            self.ws = websocket.create_connection(
                f"ws://localhost:{self.cdp_port}/devtools/browser",
                timeout=10,
            )
            return True
        except Exception as e:
            print(f"Connect failed: {e}")
            return False

    def send_cdp(self, method: str, params: dict = None) -> dict:
        import uuid
        msg = {"id": str(uuid.uuid4()), "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))
        return json.loads(self.ws.recv())

    def get_cookies(self) -> list:
        resp = self.send_cdp("Network.getAllCookies")
        return resp.get("cookies", [])

    def set_cookie(self, name: str, value: str, domain: str = ".perplexity.ai") -> bool:
        resp = self.send_cdp("Network.setCookie", {
            "name": name,
            "value": value,
            "domain": domain,
            "path": "/",
            "secure": True,
            "httpOnly": "session" in name.lower(),
        })
        return resp.get("result", False)

    def delete_cookie(self, name: str, domain: str = ".perplexity.ai") -> bool:
        resp = self.send_cdp("Network.deleteCookies", {
            "name": name,
            "domain": domain,
        })
        return resp.get("result", False)

    def get_local_storage(self) -> dict:
        resp = self.send_cdp("Runtime.evaluate", {
            "expression": "JSON.stringify(localStorage)"
        })
        try:
            return json.loads(resp.get("result", {}).get("value", "{}"))
        except Exception:
            return {}

    def get_session_storage(self) -> dict:
        resp = self.send_cdp("Runtime.evaluate", {
            "expression": "JSON.stringify(sessionStorage)"
        })
        try:
            return json.loads(resp.get("result", {}).get("value", "{}"))
        except Exception:
            return {}


def main():
    parser = argparse.ArgumentParser(description="Browser debug via CDP")
    parser.add_argument("--cdp-port", type=int, default=9223)
    parser.add_argument("--list-cookies", action="store_true")
    parser.add_argument("--get-storage", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    debugger = BrowserDebugger(cdp_port=args.cdp_port)

    if not debugger.connect():
        print("Failed to connect to CDP")
        return 1

    if args.list_cookies:
        cookies = debugger.get_cookies()
        if args.json:
            print(json.dumps(cookies, indent=2))
        else:
            print(f"Cookies ({len(cookies)}):")
            for c in cookies:
                print(f"  {c['name']}={c['value'][:20]}... domain={c['domain']}")

    if args.get_storage:
        ls = debugger.get_local_storage()
        ss = debugger.get_session_storage()
        if args.json:
            print(json.dumps({"localStorage": ls, "sessionStorage": ss}, indent=2))
        else:
            print(f"localStorage: {len(ls)} items")
            print(f"sessionStorage: {len(ss)} items")

    return 0


if __name__ == "__main__":
    sys.exit(main())