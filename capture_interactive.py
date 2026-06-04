#!/usr/bin/env python3
"""
Interactive HAR capture using CloakBrowser.
Opens Perplexity in a browser so you can perform UI actions and discover mutation endpoints.
"""

import sys
import time
import json
from pathlib import Path

# Add perplexity-web-wrapper scripts to path for imports
sys.path.insert(0, '/Volumes/ExMac/code/MCP/perplexity-web-wrapper/skills/perplexity-login/scripts')

import cdp_har
from cdp_har import CDPSession, HARBuilder, launch_cloakbrowser, connect_cdp, inject_cookies, kill_port


def capture_with_interaction(url: str, duration: int = 180):
    """Launch browser, let user interact, then analyze captured traffic."""
    har = HARBuilder()

    print("Launching CloakBrowser...")
    if not launch_cloakbrowser(Path("/tmp/perplexity_interactive_capture")):
        print("Failed to launch CloakBrowser")
        return None

    try:
        print("Connecting to CDP...")
        cdp = connect_cdp(target_url=url)
        count = inject_cookies(cdp)
        print(f"Injected {count} cookies")

        cdp.on_request_handler = har.on_request
        cdp.on_response_handler = har.on_response
        cdp.enable_network()

        print(f"\nNavigating to {url}...")
        cdp.navigate(url, wait=5)

        title = cdp.eval("document.title")
        print(f"Page title: {title}")

        # Check if logged in
        body_text = cdp.eval("(document.body && document.body.innerText || '').substring(0, 500)")
        if "sign in" in body_text.lower() or "log in" in body_text.lower():
            print("WARNING: Not logged in! Please ensure cookies are valid.")

        print(f"\n{'='*60}")
        print("BROWSER OPEN - PERFORM UI ACTIONS NOW")
        print(f"{'='*60}")
        print(f"You have {duration} seconds to interact with the browser.")
        print("Actions to try:")
        print("  - Create a new shortcut")
        print("  - Update existing shortcut")
        print("  - Change settings")
        print("  - Any mutation (POST/PUT/PATCH)")
        print(f"\nCapturing for {duration} seconds...")

        start = time.time()
        last_report = start

        while time.time() - start < duration:
            remaining = int(duration - (time.time() - start))
            if time.time() - last_report >= 10:
                print(f"  [{remaining}s left] Captured {len(har.entries)} entries...")
                last_report = time.time()
            time.sleep(0.5)

        print("\nCapture complete!")

        # Analyze results
        print(f"\nTotal entries captured: {len(har.entries)}")

        # Find mutation endpoints
        mutation_endpoints = {}
        for entry in har.entries:
            method = entry.get('method', '')
            url_path = entry.get('url', '')
            if method in ('POST', 'PUT', 'PATCH', 'DELETE') and 'perplexity' in url_path:
                path = url_path.split('perplexity.ai')[1].split('?')[0]
                if path not in mutation_endpoints:
                    mutation_endpoints[path] = []
                mutation_endpoints[path].append({
                    'method': method,
                    'url': url_path[:200],
                    'status': entry.get('status')
                })

        print(f"\n{'='*60}")
        print("MUTATION ENDPOINTS DISCOVERED")
        print('='*60)
        if mutation_endpoints:
            for path, calls in sorted(mutation_endpoints.items()):
                print(f"\n{path}")
                for c in calls:
                    print(f"  [{c['method']}] {c['status']} - {c['url'][:150]}")
        else:
            print("\nNo mutation endpoints found.")
            print("Try performing more actions in the browser.")

        # Also show GET endpoints for context
        get_endpoints = {}
        for entry in har.entries:
            method = entry.get('method', '')
            url_path = entry.get('url', '')
            if method == 'GET' and '/rest/' in url_path and 'perplexity' in url_path:
                path = url_path.split('perplexity.ai')[1].split('?')[0]
                if path not in get_endpoints:
                    get_endpoints[path] = []
                get_endpoints[path].append(entry.get('status'))

        print(f"\n{'='*60}")
        print("READ ENDPOINTS (GET)")
        print('='*60)
        for path, statuses in sorted(get_endpoints.items()):
            print(f"  GET {path} -> {set(statuses)}")

        # Save HAR
        output = Path(f"capture_{int(time.time())}.har")
        har.write_har(output)
        print(f"\nHAR saved to: {output}")

        return har

    finally:
        kill_port(cdp_har.CDP_PORT)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Interactive HAR capture")
    parser.add_argument("--url", default="https://www.perplexity.ai/account/shortcuts")
    parser.add_argument("--duration", type=int, default=180, help="Seconds to capture")
    args = parser.parse_args()

    capture_with_interaction(args.url, args.duration)