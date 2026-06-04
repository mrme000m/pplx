#!/usr/bin/env python3
"""
Debug client with HAR capture - intercepts HTTP requests via curl_cffi hooks.
"""

import json
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path


class HarBuilder:
    def __init__(self):
        self.entries = []
        self.lock = threading.Lock()
        self._started = False

    def add_entry(self, entry: dict):
        with self.lock:
            self.entries.append(entry)

    def to_har(self) -> dict:
        return {
            "log": {
                "version": "1.2",
                "creator": {"name": "perplexity-debug", "version": "1.0"},
                "entries": self.entries,
            }
        }

    def save(self, path: Path):
        path.write_text(json.dumps(self.to_har(), indent=2))


_builder = HarBuilder()


def patch_curl_cffi():
    try:
        import curl_cffi.requests
        original = curl_cffi.requests.Session.request

        def patched_request(self, method, url, **kwargs):
            start_time = time.time()
            response = original(self, method, url, **kwargs)
            elapsed = (time.time() - start_time) * 1000

            entry = {
                "startedDateTime": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "time": elapsed,
                "request": {
                    "method": method,
                    "url": url,
                    "headers": [{"name": k, "value": str(v)} for k, v in response.headers.items()] if hasattr(response, "headers") else [],
                    "queryString": [],
                    "cookies": [],
                },
                "response": {
                    "status": response.status_code if hasattr(response, "status_code") else 0,
                    "statusText": "",
                    "headers": [{"name": k, "value": str(v)} for k, v in response.headers.items()] if hasattr(response, "headers") else [],
                    "cookies": [],
                    "content": {
                        "size": len(response.content) if hasattr(response, "content") else 0,
                        "mimeType": response.headers.get("content-type", "") if hasattr(response, "headers") else "",
                    },
                },
                "cache": {},
                "timings": {"send": 0, "wait": elapsed, "receive": 0},
            }

            _builder.add_entry(entry)
            return response

        curl_cffi.requests.Session.request = patched_request
        _builder._started = True

    except ImportError:
        pass


def capture_commands(cmds: list, har_path: Path = None) -> dict:
    if not _builder._started:
        patch_curl_cffi()

    results = {}
    for cmd in cmds:
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        results[" ".join(cmd)] = {
            "returncode": result.returncode,
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:500],
        }

    if har_path:
        _builder.save(har_path)

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Debug client with HAR capture")
    parser.add_argument("--cmd", nargs="+", action="append", help="Command to run (can be repeated)")
    parser.add_argument("--output", default="capture.har", help="HAR output path")
    args = parser.parse_args()

    if not args.cmd:
        print("No commands provided")
        return 1

    results = capture_commands(args.cmd, Path(args.output))
    print(json.dumps(results, indent=2))
    print(f"HAR saved to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())