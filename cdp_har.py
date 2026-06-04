#!/usr/bin/env python3
"""
cdp_har.py — Standalone CDP network HAR capture using CloakBrowser.

Launches CloakBrowser Chromium (or connects to existing), injects cookies,
navigates to target URLs, captures network request/response pairs as HAR-style
traces so we can reverse-engineer the actual API endpoints.

Usage:
    python3 cdp_har.py --url https://www.perplexity.ai/account/shortcuts [--output shortcuts.har]
    python3 cdp_har.py --url https://www.perplexity.ai/account/personalize [--browser-already-running]
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
import time
import urllib.request
import websocket
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Optional

CDP_PORT = 9223
CLOAK_PROFILE = Path("/tmp/perplexity_har_profile")
COOKIE_PATH = Path.home() / ".config" / "perplexity" / "cookies.json"


def find_cloak_binary() -> Optional[Path]:
    for python in [sys.executable, "/opt/homebrew/bin/python3", "/usr/bin/python3"]:
        try:
            r = subprocess.run(
                [python, "-c",
                 "from cloakbrowser import binary_info; print(binary_info()['binary_path'])"],
                capture_output=True, text=True, timeout=10
            )
            p = r.stdout.strip()
            if p and Path(p).exists():
                return Path(p)
        except Exception:
            continue
    return None


def get_stealth_args() -> list[str]:
    for python in [sys.executable, "/opt/homebrew/bin/python3", "/usr/bin/python3"]:
        try:
            r = subprocess.run(
                [python, "-c",
                 "from cloakbrowser import get_default_stealth_args; import json; print(json.dumps(get_default_stealth_args()))"],
                capture_output=True, text=True, timeout=10
            )
            return json.loads(r.stdout.strip())
        except Exception:
            continue
    return []


def kill_port(port: int) -> None:
    try:
        r = subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
                           capture_output=True, text=True)
        if r.stdout.strip():
            subprocess.run(["kill"] + r.stdout.strip().split(), capture_output=True)
            time.sleep(0.5)
    except Exception:
        pass


def launch_cloakbrowser(profile_dir: Path) -> bool:
    kill_port(CDP_PORT)
    cloak = find_cloak_binary()
    if not cloak:
        print("ERROR: CloakBrowser not found", file=sys.stderr)
        return False
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    stealth = get_stealth_args()
    cmd = [
        str(cloak),
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-debugging-address=127.0.0.1",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-sandbox",
        "--window-size=1280,900",
        *stealth,
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=5)
        return True
    except Exception as e:
        print(f"CDP error: {e}", file=sys.stderr)
        return False


# ─── CDP Session ──────────────────────────────────────────────────────────────

class CDPSession:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws: Optional[websocket.WebSocketApp] = None
        self.results: dict[int, dict] = {}
        self.msg_id = 0
        self.lock = Lock()
        self.connected = Event()
        self.on_request_handler = None
        self.on_response_handler = None
        self._start()

    def _start(self):
        def on_open(ws):
            self.connected.set()
        def on_message(ws, msg):
            try:
                data = json.loads(msg)
            except Exception:
                return
            method = data.get("method", "")
            params = data.get("params", {})
            if method == "Network.requestWillBeSent":
                if self.on_request_handler:
                    self.on_request_handler(params)
            elif method == "Network.responseReceived":
                if self.on_response_handler:
                    self.on_response_handler(params)
            elif method == "Network.loadingFinished":
                pass
            mid = data.get("id")
            if mid is not None:
                with self.lock:
                    self.results[mid] = data
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=on_open,
            on_message=on_message,
        )
        t = Thread(target=self.ws.run_forever, kwargs={"ping_interval": 30}, daemon=True)
        t.start()
        if not self.connected.wait(timeout=10):
            raise RuntimeError("WS failed")

    def send(self, method: str, params: Optional[dict] = None) -> dict:
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        for _ in range(60):
            time.sleep(0.2)
            with self.lock:
                if mid in self.results:
                    return self.results.pop(mid)
        return {"error": "timeout"}

    def close(self):
        if self.ws:
            self.ws.close()

    def enable_network(self) -> None:
        self.send("Network.enable")

    def set_cookie(self, name: str, value: str, domain: str = ".perplexity.ai") -> None:
        self.send("Network.setCookie", {
            "name": name, "value": value, "domain": domain,
            "path": "/", "secure": True,
        })

    def navigate(self, url: str, wait: float = 10) -> None:
        self.send("Page.navigate", {"url": url})
        time.sleep(wait)

    def eval(self, js: str) -> str:
        r = self.send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value", "")

    def get_response_body(self, request_id: str) -> Optional[str]:
        r = self.send("Network.getResponseBody", {"requestId": request_id})
        body = r.get("result", {}).get("body", "")
        if r.get("result", {}).get("base64Encoded"):
            try:
                return base64.b64decode(body).decode("utf-8", errors="replace")
            except Exception:
                return None
        return body


def connect_cdp(port: int = CDP_PORT, target_url: str = None) -> CDPSession:
    base = f"http://127.0.0.1:{port}"
    pages = json.loads(urllib.request.urlopen(f"{base}/json").read())
    page = next((p for p in pages if p["type"] == "page" and "perplexity" in p.get("url", "")
                 and "count" not in p.get("url", "")), None)
    if not page:
        # Create a new page and navigate to target URL
        navigate_url = target_url or "https://www.perplexity.ai"
        req = urllib.request.Request(
            f"{base}/json/new?{navigate_url}",
            method="PUT"
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            page = json.loads(resp.read())
        except Exception:
            # Fallback: try with just the domain
            req = urllib.request.Request(
                f"{base}/json/new?https://www.perplexity.ai",
                method="PUT"
            )
            resp = urllib.request.urlopen(req, timeout=10)
            page = json.loads(resp.read())
    return CDPSession(page["webSocketDebuggerUrl"])


def inject_cookies(cdp: CDPSession) -> int:
    if not COOKIE_PATH.exists():
        return 0
    with open(COOKIE_PATH) as f:
        cookies = json.load(f)
    for name, value in cookies.items():
        cdp.set_cookie(name, value)
    return len(cookies)


# ─── HAR Builder ───────────────────────────────────────────────────────────────

class HARBuilder:
    def __init__(self):
        self.entries: list[dict] = []
        self.lock = Lock()
        self.request_map: dict[str, dict] = {}
        self.response_data: dict[str, dict] = {}

    def on_request(self, params: dict) -> None:
        req = params.get("request", {})
        url = req.get("url", "")
        # Skip non-API calls (images, fonts, etc)
        if not url or "perplexity" not in url:
            return
        entry = {
            "requestId": params.get("requestId"),
            "timestamp": params.get("timestamp", 0),
            "type": params.get("type", "other"),
            "method": req.get("method", "GET"),
            "url": url,
            "headers": dict(req.get("headers", {})),
            "query": req.get("url", "").split("?")[1] if "?" in req.get("url", "") else "",
        }
        pd = req.get("postData", "")
        if pd:
            entry["postData"] = pd.get("text", "") if isinstance(pd, dict) else str(pd)
        with self.lock:
            self.request_map[params["requestId"]] = entry

    def on_response(self, params: dict) -> None:
        rid = params.get("requestId")
        resp = params.get("response", {})
        with self.lock:
            if rid in self.request_map:
                entry = self.request_map.pop(rid)
                entry["status"] = resp.get("status", 0)
                entry["status_text"] = resp.get("statusText", "")
                entry["response_headers"] = dict(resp.get("headers", {}))
                entry["mime_type"] = resp.get("mimeType", "")
                self.entries.append(entry)
                self.response_data[rid] = entry

    def get_entries(self) -> list[dict]:
        with self.lock:
            unfinished = list(self.request_map.values())
            return sorted(self.entries + unfinished, key=lambda x: x["timestamp"])

    def write_har(self, path: Path) -> None:
        entries = self.get_entries()
        # Enrich with response bodies for REST API calls
        for entry in entries:
            if "/rest/" in entry["url"] or "/api/" in entry["url"]:
                entry["_is_api"] = True
        with open(path, "w") as f:
            json.dump({"log": {"entries": entries}}, f, indent=2)


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="CDP HAR network capture")
    parser.add_argument("--url", required=True, help="URL to capture traffic from")
    parser.add_argument("--output", "-o", help="Output HAR file")
    parser.add_argument("--browser-already-running", action="store_true",
                        help="Don't launch browser, connect to existing CDP")
    parser.add_argument("--profile", default=str(CLOAK_PROFILE), help="Profile dir")
    parser.add_argument("--wait", type=float, default=10, help="Seconds to wait after navigation")
    args = parser.parse_args()

    har = HARBuilder()
    output_path = Path(args.output) if args.output else Path(f"capture_{int(time.time())}.har")

    if not args.browser_already_running:
        if not launch_cloakbrowser(Path(args.profile)):
            return 1

    try:
        cdp = connect_cdp()
        count = inject_cookies(cdp)
        print(f"Injected {count} cookies", file=sys.stderr)

        cdp.on_request_handler = har.on_request
        cdp.on_response_handler = har.on_response
        cdp.enable_network()
        time.sleep(2)

        print(f"Navigating to {args.url}…", file=sys.stderr)
        cdp.navigate(args.url, wait=args.wait)

        title = cdp.eval("document.title")
        body = cdp.eval("(document.body && document.body.innerText || '').substring(0, 200)")
        print(f"Page title: {title}", file=sys.stderr)
        print(f"Body preview: {body[:100]}", file=sys.stderr)

        har.write_har(output_path)
        print(f"HAR saved to: {output_path}", file=sys.stderr)

        # Print API calls found
        print("\n--- API Calls Found ---", file=sys.stderr)
        for entry in har.get_entries():
            if entry.get("_is_api"):
                print(f"  [{entry['method']}] {entry['status']} {entry['url']}", file=sys.stderr)

        cdp.close()
        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return 1
    finally:
        if not args.browser_already_running:
            kill_port(CDP_PORT)


if __name__ == "__main__":
    sys.exit(main())
