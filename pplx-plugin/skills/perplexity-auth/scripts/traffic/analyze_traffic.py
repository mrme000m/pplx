#!/usr/bin/env python3
"""
Traffic analyzer - analyzes HAR files and discovers API endpoints.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


class TrafficAnalyzer:
    CATEGORIES = {
        "search": ["/sse/perplexity_ask", "/rest/search"],
        "threads": ["/rest/thread"],
        "spaces": ["/rest/collections", "/rest/spaces"],
        "files": ["/rest/files", "/rest/file-repository"],
        "discover": ["/rest/discover"],
        "memories": ["/rest/memories"],
        "auth": ["/api/auth", "/api/user"],
        "finance": ["/rest/finance"],
        "billing": ["/rest/billing", "/rest/stripe"],
        "assets": ["/rest/assets"],
        "skills": ["/rest/skills"],
        "tasks": ["/rest/tasks", "/rest/workflows"],
        "settings": ["/rest/user", "/rest/rate-limit"],
    }

    def __init__(self):
        self.endpoints = defaultdict(lambda: {"count": 0, "methods": set(), "sample_urls": []})

    def normalize_url(self, url: str) -> str:
        url = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/{uuid}", url, flags=re.I)
        url = re.sub(r"/[0-9a-f]{24,}", "/{id}", url)
        url = re.sub(r"\?.*", "", url)
        return url

    def categorize(self, url: str) -> str:
        for cat, patterns in self.CATEGORIES.items():
            for p in patterns:
                if p in url:
                    return cat
        return "other"

    def analyze_har(self, har_path: Path) -> dict:
        try:
            data = json.loads(har_path.read_text())
        except Exception:
            return {"error": "Failed to parse HAR file"}

        entries = data.get("log", {}).get("entries", [])

        for entry in entries:
            req = entry.get("request", {})
            url = req.get("url", "")
            method = req.get("method", "GET")

            if "perplexity" not in url:
                continue

            normalized = self.normalize_url(url)
            cat = self.categorize(url)

            self.endpoints[normalized]["count"] += 1
            self.endpoints[normalized]["methods"].add(method)
            self.endpoints[normalized]["category"] = cat
            if len(self.endpoints[normalized]["sample_urls"]) < 3:
                self.endpoints[normalized]["sample_urls"].append(url)

        return self.format_results()

    def format_results(self) -> dict:
        result = {"endpoints": [], "categories": defaultdict(list)}

        for url, info in sorted(self.endpoints.items(), key=lambda x: -x[1]["count"]):
            entry = {
                "endpoint": url,
                "count": info["count"],
                "methods": sorted(list(info["methods"])),
                "category": info.get("category", "other"),
                "sample": info["sample_urls"][0] if info["sample_urls"] else "",
            }
            result["endpoints"].append(entry)
            result["categories"][entry["category"]].append(entry["endpoint"])

        return result


def main():
    parser = argparse.ArgumentParser(description="Analyze Perplexity traffic")
    parser.add_argument("har_file", help="HAR file to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    analyzer = TrafficAnalyzer()
    results = analyzer.analyze_har(Path(args.har_file))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=== Endpoint Discovery ===\n")
        for cat, endpoints in sorted(results.get("categories", {}).items()):
            print(f"[{cat}] ({len(endpoints)} endpoints)")
            for ep in endpoints[:10]:
                info = next((e for e in results["endpoints"] if e["endpoint"] == ep), {})
                print(f"  {info.get('methods', ['GET'])[0]} {ep} ({info.get('count', 0)} hits)")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())