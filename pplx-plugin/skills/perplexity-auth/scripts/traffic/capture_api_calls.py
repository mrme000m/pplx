#!/usr/bin/env python3
"""
Capture API calls - captures Perplexity API calls via CDP network monitoring.
"""

import argparse
import json
import sys
import time
import websocket
from pathlib import Path


class APICapturer:
    def __init__(self, cdp_port: int = 9223):
        self.cdp_port = cdp_port
        self.ws = None
        self.browser_pid = None
        self.events = []

    def start_browser(self) -> bool:
        try:
            import cloakbrowser
            self.browser_pid = cloakbrowser.launch(port=self.cdp_port, headless=True, remote_debugging=True)
            return self.browser_pid is not None
        except ImportError:
            print("ERROR: CloakBrowser not installed")
            return False

    def stop_browser(self):
        if self.browser_pid:
            import os, signal
            try:
                os.kill(self.browser_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def connect(self) -> bool:
        try:
            self.ws = websocket.create_connection(f"ws://localhost:{self.cdp_port}/devtools/browser", timeout=10)
            return True
        except Exception as e:
            print(f"CDP connect failed: {e}")
            return False

    def send_cdp(self, method: str, params: dict = None) -> dict:
        import uuid
        msg_id = str(uuid.uuid4())
        msg = {"id": msg_id, "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))
        resp = json.loads(self.ws.recv())
        return resp

    def capture_url(self, url: str, duration: int = 30) -> list:
        self.send_cdp("Network.enable")
        self.send_cdp("Page.enable")

        result = self.send_cdp("Page.navigate", {"url": url})
        if "error" in result:
            return []

        start = time.time()
        while time.time() - start < duration:
            try:
                msg = json.loads(self.ws.recv())
                if msg.get("method", "").startswith("Network."):
                    self.events.append(msg)
            except Exception:
                break

        return self.events

    def to_har(self) -> dict:
        entries = []
        for ev in self.events:
            params = ev.get("params", {})
            if ev.get("method") == "Network.requestWillBeSent":
                entries.append({
                    "startedDateTime": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                    "request": {
                        "method": params.get("request", {}).get("method", "GET"),
                        "url": params.get("request", {}).get("url", ""),
                    },
                    "response": {"status": 0},
                    "time": 0,
                })
        return {"log": {"entries": entries}}

    def save(self, path: Path):
        path.write_text(json.dumps(self.to_har(), indent=2))


def main():
    parser = argparse.ArgumentParser(description="Capture Perplexity API calls via CDP")
    parser.add_argument("--url", default="https://www.perplexity.ai", help="URL to capture")
    parser.add_argument("--duration", type=int, default=30, help="Capture duration (seconds)")
    parser.add_argument("--output", default="api_capture.har", help="HAR output path")
    args = parser.parse_args()

    capturer = APICapturer()

    if not capturer.start_browser():
        return 1

    try:
        if not capturer.connect():
            return 1

        print(f"Capturing {args.url} for {args.duration}s...")
        events = capturer.capture_url(args.url, args.duration)
        print(f"Captured {len(events)} network events")

        capturer.save(Path(args.output))
        print(f"Saved to {args.output}")
        return 0

    finally:
        capturer.stop_browser()


if __name__ == "__main__":
    sys.exit(main())