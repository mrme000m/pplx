#!/usr/bin/env python3
"""
UI crawler - interactive element discovery via CDP.
"""

import argparse
import json
import sys
import time
import websocket
from pathlib import Path


class UICrawler:
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
        except Exception:
            return False

    def send_cdp(self, method: str, params: dict = None) -> dict:
        import uuid
        msg = {"id": str(uuid.uuid4()), "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))
        return json.loads(self.ws.recv())

    def get_clickable_elements(self) -> list:
        resp = self.send_cdp("Runtime.evaluate", {
            "expression": """
                (function() {
                    const els = document.querySelectorAll(
                        'button, a, [role="button"], [onclick], input[type="submit"]'
                    );
                    return Array.from(els).map(el => ({
                        tag: el.tagName,
                        text: el.innerText?.trim().substring(0, 50),
                        class: el.className,
                        id: el.id,
                        href: el.href,
                    }));
                })()
            """
        })
        try:
            return json.loads(resp.get("result", {}).get("value", "[]"))
        except Exception:
            return []

    def discover(self, url: str, limit: int = 20) -> dict:
        if not self.connect():
            return {"error": "Failed to connect to CDP"}

        self.send_cdp("Page.navigate", {"url": url})
        time.sleep(2)

        elements = self.get_clickable_elements()
        return {
            "url": url,
            "element_count": len(elements),
            "elements": elements[:limit],
        }

    def save(self, path: Path, data: dict):
        path.write_text(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="UI element crawler")
    parser.add_argument("--url", default="https://www.perplexity.ai", help="URL to crawl")
    parser.add_argument("--limit", type=int, default=20, help="Max elements")
    parser.add_argument("--output", default="elements.json", help="Output file")
    args = parser.parse_args()

    crawler = UICrawler()
    result = crawler.discover(args.url, args.limit)

    crawler.save(Path(args.output), result)
    print(f"Discovered {result.get('element_count', 0)} elements → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())