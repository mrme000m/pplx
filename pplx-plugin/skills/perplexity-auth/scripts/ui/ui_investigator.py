#!/usr/bin/env python3
"""
UI investigator - deep UI investigation via CDP with state extraction.
"""

import argparse
import json
import sys
import time
import websocket
from pathlib import Path


class UIInvestigator:
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
            print(f"Failed to connect: {e}")
            return False

    def send_cdp(self, method: str, params: dict = None) -> dict:
        import uuid
        msg = {"id": str(uuid.uuid4()), "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))
        return json.loads(self.ws.recv())

    def get_dom_snapshot(self) -> str:
        resp = self.send_cdp("Runtime.evaluate", {
            "expression": "document.documentElement.outerHTML"
        })
        return resp.get("result", {}).get("value", "")

    def get_react_state(self) -> dict:
        resp = self.send_cdp("Runtime.evaluate", {
            "expression": """
                (function() {
                    const roots = document.querySelectorAll('#root, [data-root]');
                    const states = [];
                    roots.forEach(root => {
                        const key = Object.keys(root).find(k => k.startsWith('__react'));
                        if (key) states.push({selector: root.id || root.className, key});
                    });
                    return JSON.stringify(states);
                })()
            """
        })
        try:
            return json.loads(resp.get("result", {}).get("value", "{}"))
        except Exception:
            return {}

    def extract_api_config(self) -> dict:
        resp = self.send_cdp("Runtime.evaluate", {
            "expression": """
                (function() {
                    const config = window.__PERPLEXITY_CONFIG__ ||
                                   window.__INITIAL_STATE__ ||
                                   window.__NEXT_DATA__;
                    return config ? JSON.stringify(config) : '{}';
                })()
            """
        })
        try:
            return json.loads(resp.get("result", {}).get("value", "{}"))
        except Exception:
            return {}

    def capture_page(self, url: str, output_dir: Path) -> dict:
        self.send_cdp("Page.navigate", {"url": url})
        time.sleep(3)

        snapshot = self.get_dom_snapshot()
        react_state = self.get_react_state()
        api_config = self.extract_api_config()

        html_path = output_dir / "page.html"
        html_path.write_text(snapshot)

        result = {
            "url": url,
            "snapshot_size": len(snapshot),
            "react_roots": len(react_state) if isinstance(react_state, list) else 0,
            "api_config_found": bool(api_config),
        }

        return result

    def investigate(self, url: str, output_dir: Path) -> dict:
        results = []

        if not self.connect():
            return {"error": "Failed to connect to CDP"}

        for page_url in [url, f"{url}/settings", f"{url}/spaces"]:
            try:
                result = self.capture_page(page_url, output_dir)
                results.append(result)
            except Exception as e:
                results.append({"url": page_url, "error": str(e)})

        return {"pages": results}


def main():
    parser = argparse.ArgumentParser(description="UI investigator via CDP")
    parser.add_argument("--url", default="https://www.perplexity.ai", help="URL to investigate")
    parser.add_argument("--output", default="ui_investigation", help="Output directory")
    parser.add_argument("--cdp-port", type=int, default=9223, help="CDP port")
    args = parser.parse_args()

    investigator = UIInvestigator(cdp_port=args.cdp_port)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Investigating {args.url}...")
    result = investigator.investigate(args.url, output_dir)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())