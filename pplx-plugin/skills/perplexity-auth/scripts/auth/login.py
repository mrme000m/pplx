#!/usr/bin/env python3
"""
Perplexity automated login via CloakBrowser CDP with Gmail OTP extraction.
Consolidated from perplexity-web-wrapper skills.
"""

import argparse
import asyncio
import json
import os
import sys
import time
import webbrowser
import signal
from pathlib import Path
from typing import Optional

try:
    import websocket
except ImportError:
    print("ERROR: websocket-client not installed. Run: pip3 install websocket-client")
    sys.exit(1)


class CloakBrowserLogin:
    def __init__(
        self,
        email: str,
        cookies_path: str = "~/.config/perplexity/cookies.json",
        cdp_port: int = 9223,
        headless: bool = False,
    ):
        self.email = email
        self.cookies_path = Path(cookies_path).expanduser()
        self.cookies_path.parent.mkdir(parents=True, exist_ok=True)
        self.cdp_port = cdp_port
        self.headless = headless
        self.ws = None
        self._browser = None

    def send_cdp(self, method: str, params: dict = None) -> dict:
        msg = {"id": 1, "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))
        resp = json.loads(self.ws.recv())
        return resp.get("result", {})

    def launch_browser(self) -> bool:
        try:
            import cloakbrowser
            self._browser = cloakbrowser.launch(
                headless=self.headless,
                args=[
                    f"--remote-debugging-port={self.cdp_port}",
                    "--remote-allow-origins=*",
                ],
                stealth_args=False,
            )
            return self._browser is not None
        except ImportError:
            print("ERROR: cloakbrowser not installed. Run: pip3 install cloakbrowser")
            return False

    def stop_browser(self):
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass

    def navigate(self, url: str) -> bool:
        result = self.send_cdp("Page.navigate", {"url": url})
        return "error" not in result

    def wait_for_selector(self, selector: str, timeout: int = 30) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            resp = self.send_cdp("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}') !== null"
            })
            if resp.get("result", {}).get("value"):
                return True
            time.sleep(0.5)
        return False

    def click_element(self, selector: str) -> bool:
        resp = self.send_cdp("Runtime.evaluate", {
            "expression": f"""
                (function() {{
                    const el = document.querySelector('{selector}');
                    if (el) {{ el.click(); return true; }}
                    return false;
                }})()
            """
        })
        return resp.get("result", {}).get("value", False)

    def fill_input(self, selector: str, value: str) -> bool:
        resp = self.send_cdp("Runtime.evaluate", {
            "expression": f"""
                (function() {{
                    const el = document.querySelector('{selector}');
                    if (el) {{ el.value = '{value}'; el.dispatchEvent(new Event('input', {{bubbles: true}})); el.dispatchEvent(new Event('change', {{bubbles: true}})); return true; }}
                    return false;
                }})()
            """
        })
        return resp.get("result", {}).get("value", False)

    def get_cookies(self) -> dict:
        resp = self.send_cdp("Network.getAllCookies")
        cookies = resp.get("cookies", [])
        result = {}
        for c in cookies:
            result[c["name"]] = c["value"]
        return result

    def save_cookies(self, cookies: dict):
        data = {
            "cookies": cookies,
            "last_saved": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.cookies_path.write_text(json.dumps(data, indent=2))
        print(f"Cookies saved to {self.cookies_path}")

    def login(self, bw_save: bool = False, bw_load: bool = False) -> dict:
        if bw_load:
            return self.login_from_bitwarden()
        return self.full_login_flow(bw_save=bw_save)

    def login_from_bitwarden(self) -> dict:
        from .session.bw_cookies import CookieManager
        cm = CookieManager()
        cookies_data = cm.load()
        if not cookies_data:
            print("No cookies in Bitwarden. Running full login...")
            return self.full_login_flow()
        self.save_cookies(cookies_data.get("cookies", {}))
        return cookies_data.get("cookies", {})

    def full_login_flow(self, bw_save: bool = False) -> dict:
        print(f"Starting login flow for {self.email}")

        if not self.launch_browser():
            raise RuntimeError("Failed to launch CloakBrowser")

        try:
            if not self.connect_cdp():
                raise RuntimeError("Failed to connect to CDP")

            print("Navigating to perplexity.ai...")
            self.send_cdp("Network.enable")
            self.navigate("https://www.perplexity.ai")

            if not self.wait_for_selector("body", timeout=30):
                raise RuntimeError("Page failed to load")

            # Check for Cloudflare challenge
            time.sleep(3)
            title_resp = self.send_cdp("Runtime.evaluate", {
                "expression": "document.title"
            })
            if "Just a moment" in title_resp.get("result", {}).get("value", ""):
                raise RuntimeError("Cloudflare challenge detected. CloakBrowser may not be properly stealthed.")

            print("Looking for Sign In button...")
            if not self.click_sign_in():
                raise RuntimeError("Could not find Sign In button")

            print("Filling email...")
            if not self.fill_email():
                raise RuntimeError("Could not fill email")

            print("Waiting for OTP email...")
            from .auth.extract_otp import OTPFetcher
            fetcher = OTPFetcher(self.email)
            otp = fetcher.wait_for_otp(timeout=120)
            if not otp:
                raise RuntimeError("OTP not received")

            print("Filling OTP...")
            if not self.fill_otp(otp):
                raise RuntimeError("Failed to fill OTP")

            print("Waiting for redirect...")
            if not self.wait_for_url_contains("perplexity.ai", timeout=30):
                raise RuntimeError("Login did not complete")

            print("Extracting cookies...")
            cookies = self.get_cookies()
            if not cookies:
                raise RuntimeError("No cookies extracted")

            self.save_cookies(cookies)

            if bw_save:
                from .session.bw_cookies import CookieManager
                cm = CookieManager()
                cm.save(cookies)
                print("Cookies saved to Bitwarden")

            return cookies

        finally:
            self.stop_browser()


def main():
    parser = argparse.ArgumentParser(description="Perplexity automated login")
    parser.add_argument("--email", required=True, help="Gmail email for magic-link")
    parser.add_argument("--bw-load", action="store_true", help="Load cookies from Bitwarden")
    parser.add_argument("--bw-save", action="store_true", help="Save cookies to Bitwarden")
    parser.add_argument("--cookies-path", default="~/.config/perplexity/cookies.json")
    parser.add_argument("--cdp-port", type=int, default=9223)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    login = CloakBrowserLogin(
        email=args.email,
        cookies_path=args.cookies_path,
        cdp_port=args.cdp_port,
        headless=args.headless,
    )

    try:
        cookies = login.login(bw_save=args.bw_save, bw_load=args.bw_load)
        print(f"Login successful. {len(cookies)} cookies extracted.")
        return 0
    except Exception as e:
        print(f"Login failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())