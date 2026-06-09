#!/usr/bin/env python3
"""
login.py — Fully automated Perplexity sign-in via CloakBrowser CDP.

Workflow:
  1. Launch CloakBrowser with remote debugging on a free port
  2. Navigate to https://www.perplexity.ai
  3. Click "Sign In" → fill email → click "Continue with email"
  4. Poll Gmail via extract_otp.py for the 6-digit token
  5. Fill OTP digits on verification page → click Confirm
  6. Extract cookies via Network.getCookies
  7. Save to ~/.config/perplexity/cookies.json (and optionally Bitwarden)

Usage:
  # Full auto login
  python3 login.py --email vb.mrme00@gmail.com

  # With explicit OTP extraction from forwarding inbox
  python3 login.py --email vb.mrme00@gmail.com \\
      --otp-email mrme000.m0@gmail.com \\
      --otp-app-password "fqoi ycoa zwvg mpsq"

  # Save cookies to Bitwarden after login
  python3 login.py --email vb.mrme00@gmail.com --bw-save

  # Use existing session cookie from Bitwarden instead of logging in
  python3 login.py --bw-load
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

# ─── Constants ───────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
EXTRACT_OTP = SCRIPT_DIR / "extract_otp.py"
COOKIE_PATH = Path.home() / ".config" / "perplexity" / "cookies.json"
CDP_PORT = 9223

# Ephemeral profile used during login (always starts fresh for clean auth)
CLOAK_PROFILE = Path("/tmp/perplexity_cloak_profile")

# Persistent profile directory — saved after successful login so debug sessions
# can reuse an authenticated browser without repeating the OTP flow.
PERSISTED_PROFILE = Path.home() / ".config" / "perplexity" / "cloak_profile"

# ─── CloakBrowser helpers ────────────────────────────────────────────────────

def _find_cloak_binary() -> Optional[Path]:
    """Find CloakBrowser binary, trying both current and global Python envs."""
    import importlib
    for python in [sys.executable, "/opt/homebrew/bin/python3", "/usr/bin/python3"]:
        try:
            result = subprocess.run(
                [python, "-c",
                 "from cloakbrowser import binary_info; print(binary_info()['binary_path'])"],
                capture_output=True, text=True, timeout=10
            )
            path = result.stdout.strip()
            if path and Path(path).exists():
                return Path(path)
        except Exception:
            continue
    return None


def _get_stealth_args() -> list[str]:
    for python in [sys.executable, "/opt/homebrew/bin/python3", "/usr/bin/python3"]:
        try:
            result = subprocess.run(
                [python, "-c",
                 "from cloakbrowser import get_default_stealth_args; import json; print(json.dumps(get_default_stealth_args()))"],
                capture_output=True, text=True, timeout=10
            )
            return json.loads(result.stdout.strip())
        except Exception:
            continue
    return []


def launch_cloakbrowser(reuse_persisted: bool = False, headless: bool = False) -> bool:
    """Launch CloakBrowser with CDP on CDP_PORT. Returns True if successful.

    Args:
        reuse_persisted: If True, use the persisted authenticated profile
            (from PERSISTED_PROFILE) instead of a fresh ephemeral profile.
            This skips the auth flow when the profile already has valid cookies.
        headless: If True, run CloakBrowser in headless mode (no GUI window).
    """
    _kill_port(CDP_PORT)

    cloak = _find_cloak_binary()
    if not cloak:
        print("ERROR: CloakBrowser not found. Run: pip3 install --break-system-packages cloakbrowser", file=sys.stderr)
        return False

    # Choose profile directory
    if reuse_persisted and PERSISTED_PROFILE.exists():
        profile_dir = PERSISTED_PROFILE
        print(f"Reusing persisted profile: {profile_dir}", file=sys.stderr)
    else:
        # Fresh ephemeral profile for login flow
        if CLOAK_PROFILE.exists():
            shutil.rmtree(CLOAK_PROFILE)
        CLOAK_PROFILE.mkdir(parents=True, exist_ok=True)
        profile_dir = CLOAK_PROFILE
        if reuse_persisted:
            print(f"No persisted profile found, using fresh profile", file=sys.stderr)

    stealth_args = _get_stealth_args()
    print(f"CloakBrowser: {cloak}", file=sys.stderr)
    print(f"Stealth args: {' '.join(stealth_args)}", file=sys.stderr)
    if headless:
        print("Mode: headless", file=sys.stderr)

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
        *(["--headless=new"] if headless else []),
        *stealth_args,
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3 if not headless else 7)  # Headless needs more startup time

    # Verify CDP is up
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=5)
        print(f"CDP live on port {CDP_PORT}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"CDP not responding: {e}", file=sys.stderr)
        return False


def stop_cloakbrowser(persist: bool = False) -> None:
    """Stop CloakBrowser and optionally persist the profile.

    Args:
        persist: If True, copy the ephemeral profile to PERSISTED_PROFILE
            so it can be reused by future debug sessions.
    """
    _kill_port(CDP_PORT)
    if persist and CLOAK_PROFILE.exists():
        _persist_profile()
    if CLOAK_PROFILE.exists():
        shutil.rmtree(CLOAK_PROFILE, ignore_errors=True)


def _persist_profile() -> bool:
    """Copy the current ephemeral profile to the persisted location.

    Returns True if the profile was saved successfully.
    """
    if not CLOAK_PROFILE.exists():
        return False

    try:
        if PERSISTED_PROFILE.exists():
            shutil.rmtree(PERSISTED_PROFILE, ignore_errors=True)
        shutil.copytree(CLOAK_PROFILE, PERSISTED_PROFILE, symlinks=False)
        print(f"Profile persisted to {PERSISTED_PROFILE}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"WARNING: Could not persist profile: {e}", file=sys.stderr)
        return False


def has_persisted_profile() -> bool:
    """Check if a persisted authenticated profile exists."""
    return PERSISTED_PROFILE.exists() and any(PERSISTED_PROFILE.iterdir())


def _kill_port(port: int) -> None:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            subprocess.run(["kill"] + result.stdout.strip().split(), capture_output=True)
            time.sleep(0.5)
    except Exception:
        pass


# ─── CDP WebSocket helpers ───────────────────────────────────────────────────

def _cdp_connect():
    """Connect to the Perplexity page via CDP WebSocket. Returns (ws, send_fn)."""
    import threading
    import websocket

    # Find the Perplexity page
    pages = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json").read())
    pplx_page = None
    for p in pages:
        if p["type"] == "page" and "perplexity" in p.get("url", ""):
            pplx_page = p
            break

    if not pplx_page:
        # Open Perplexity in new tab
        urllib.request.urlopen(
            urllib.request.Request(
                f"http://127.0.0.1:{CDP_PORT}/json/new?https://www.perplexity.ai",
                method="PUT",
            ),
            timeout=5,
        )
        time.sleep(5)
        pages = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json").read())
        for p in pages:
            if p["type"] == "page" and "perplexity" in p.get("url", ""):
                pplx_page = p
                break

    if not pplx_page:
        raise RuntimeError("Could not find/open Perplexity page")

    ws_url = pplx_page["webSocketDebuggerUrl"]

    results = {}
    msg_id = [0]
    lock = threading.Lock()
    connected = threading.Event()

    def on_open(_ws):
        connected.set()

    def on_message(_ws, msg):
        try:
            data = json.loads(msg)
        except Exception:
            return
        mid = data.get("id")
        if mid:
            with lock:
                results[mid] = data

    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
    t = threading.Thread(target=ws.run_forever, kwargs={"ping_interval": 30}, daemon=True)
    t.start()

    if not connected.wait(timeout=10):
        raise RuntimeError("WebSocket connection failed")

    def send(method, params=None):
        mid = msg_id[0] + 1
        msg_id[0] = mid
        ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        for _ in range(60):
            time.sleep(0.2)
            with lock:
                if mid in results:
                    return results.pop(mid)
        return {"error": "timeout"}

    send("Runtime.enable")
    send("Page.enable")
    send("DOM.enable")
    send("Network.enable")
    send("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })

    return ws, send


# ─── Page interaction ────────────────────────────────────────────────────────

def _eval(send, js: str) -> str:
    """Evaluate JS on the page and return the result value as JSON string."""
    r = send("Runtime.evaluate", {"expression": js, "returnByValue": True})
    return r.get("result", {}).get("result", {}).get("value", "")


def is_logged_in(send) -> bool:
    """Check if already logged in via session cookie (most reliable method)."""
    # Method 1: Check cookies via CDP
    try:
        r = send("Network.getCookies", {"urls": ["https://www.perplexity.ai"]})
        cookies = r.get("result", {}).get("cookies", [])
        cookie_names = {c["name"] for c in cookies}
        session_ok = "__Secure-next-auth.session-token" in cookie_names
        if session_ok:
            print("  [is_logged_in] Session cookie found", file=sys.stderr)
            return True
    except Exception:
        pass

    # Method 2: DOM heuristics as fallback
    result = _eval(send, """
        (function() {
            let body = document.body ? document.body.innerText : '';
            let hasSignIn = Array.from(document.querySelectorAll('button'))
                .some(b => /sign\\s*in/i.test(b.textContent.trim()));
            let hasHistory = body.includes('History') || body.includes('Library');
            let hasNew = body.includes('New') && body.includes('Spaces');
            let hasSearch = !!document.querySelector('[placeholder*="Ask"]') ||
                           !!document.querySelector('[placeholder*="Search"]');
            // No Sign In button but has logged-in UI = logged in
            if (!hasSignIn && (hasHistory || hasNew || hasSearch)) {
                return true;
            }
            return false;
        })()
    """)
    return result == "true"


def click_sign_in(send) -> bool:
    """Click the Sign In button on the Perplexity homepage. Retries up to 5 times."""
    for attempt in range(5):
        result = _eval(send, """
            (function() {
                // Try exact text match first
                let btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.trim() === 'Sign In');
                if (btn) { btn.click(); return 'text-match'; }
                // Try partial match
                btn = Array.from(document.querySelectorAll('button, a, [role="button"]'))
                    .find(b => /sign.?in/i.test((b.textContent || '').trim()));
                if (btn) { btn.click(); return 'partial-match'; }
                // Try class-based search
                btn = document.querySelector('[class*="sign"], [class*="Sign"], [class*="login"], [class*="Login"]');
                if (btn) { btn.click(); return 'class-match'; }
                return false;
            })()
        """)
        if result and result != "false":
            print(f"  Sign In clicked via {result}", file=sys.stderr)
            time.sleep(2)
            return True
        print(f"  Sign In attempt {attempt+1}/5: not found yet", file=sys.stderr)
        time.sleep(3)
    return False


def fill_email(send, email_addr: str) -> bool:
    """Wait for and fill the email input on the sign-in dialog."""
    for attempt in range(8):
        result = _eval(send, f"""
            (function() {{
                let inp = document.querySelector('input[type="email"]');
                if (!inp) inp = document.querySelector('input[name="email"]');
                if (!inp) return 'no_input';
                let rect = inp.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) return 'invisible';
                inp.focus();
                let ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                ns.call(inp, '{email_addr}');
                inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                let btn = Array.from(document.querySelectorAll('button'))
                    .find(b => (b.textContent || '').toLowerCase().includes('continue with email'));
                return btn ? 'filled_btn:' + (btn.disabled ? 'disabled' : 'enabled') : 'filled_no_btn';
            }})()
        """)
        if result and result.startswith("filled_btn:enabled"):
            print(f"  Email ready: {email_addr}", file=sys.stderr)
            time.sleep(0.5)
            return True
        print(f"  Email state: {result} (attempt {attempt+1}/8)", file=sys.stderr)
        time.sleep(2)
    return False


def submit_email_login(send, email_addr: str) -> bool:
    """
    Submit the email sign-in form by clicking the "Continue with email" button
    using PointerEvent for React compatibility.
    """
    for attempt in range(5):
        result = _eval(send, """
            (function() {
                let inp = document.querySelector('input[type="email"]') || 
                          document.querySelector('input[name="email"]');
                if (!inp || inp.offsetParent === null) return 'no_dialog';

                let btn = Array.from(document.querySelectorAll('button'))
                    .find(b => (b.textContent || '').toLowerCase().includes('continue with email'));
                if (!btn) return 'no_button';
                if (btn.disabled) return 'disabled';

                // Simulate a real user click with pointer events
                let rect = btn.getBoundingClientRect();
                let cx = rect.left + rect.width / 2;
                let cy = rect.top + rect.height / 2;
                
                ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(type => {
                    btn.dispatchEvent(new PointerEvent(type, {
                        bubbles: true, cancelable: true,
                        clientX: cx, clientY: cy,
                        pointerId: 1, pointerType: 'mouse', isPrimary: true
                    }));
                });
                
                return 'submitted';
            })()
        """)
        if result == "submitted":
            print(f"  Email login submitted", file=sys.stderr)
            time.sleep(5)
            return True
        print(f"  Submit: {result} (attempt {attempt+1}/5)", file=sys.stderr)
        time.sleep(2)
    return False


def wait_for_verification_page(send, timeout: int = 30) -> bool:
    """Wait until the page navigates to the verification page."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        url = _eval(send, "location.href")
        if "verify-request" in url:
            return True
        time.sleep(1)
    return False


def fill_otp(send, otp: str) -> bool:
    """Fill the 6 OTP digits into the verification page inputs and click Confirm."""
    result = _eval(send, f"""
        (function() {{
            let digits = '{otp}'.split('');
            let inputs = document.querySelectorAll('input[type="text"]');

            if (inputs.length >= 6) {{
                let ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                digits.forEach((d, i) => {{
                    ns.call(inputs[i], d);
                    inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                }});
            }} else {{
                // Single input fallback
                let inp = document.querySelector('input:not([type="hidden"])');
                if (inp) {{
                    let ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    ns.call(inp, '{otp}');
                    inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            }}
            return true;
        }})()
    """)
    time.sleep(0.5)

    # Click Confirm
    _eval(send, """
        (function() {
            let btn = Array.from(document.querySelectorAll('button'))
                .find(b => (b.textContent || '').trim() === 'Confirm');
            if (btn && !btn.disabled) { btn.click(); return true; }
            // Fallback: find any enabled visible button
            btn = Array.from(document.querySelectorAll('button'))
                .find(b => !b.disabled && b.offsetParent !== null && b.textContent.trim());
            if (btn) { btn.click(); return true; }
            return false;
        })()
    """)
    time.sleep(5)
    return True


def wait_for_login(send, timeout: int = 15) -> bool:
    """Wait for successful login (homepage with search UI elements)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        url = _eval(send, "location.href")
        body = _eval(send, "document.body ? document.body.innerText.substring(0, 500) : ''")
        # Login succeeded if we're on the homepage, not on auth pages, and see the sidebar
        if "perplexity.ai" in url and "verify-request" not in url:
            if "New" in body or "Computer" in body or "Spaces" in body:
                return True
            # Also check for logged-in sidebar items
            if "History" in body and "Discover" in body:
                return True
        time.sleep(1)
    return False


def extract_cookies(send) -> dict:
    """Extract all cookies from the Perplexity domain."""
    r = send("Network.getCookies", {"urls": ["https://www.perplexity.ai"]})
    cookies = r.get("result", {}).get("cookies", [])
    return {c["name"]: c["value"] for c in cookies}


# ─── Cookie saving ───────────────────────────────────────────────────────────

def save_cookies(cookies: dict) -> Path:
    """Save cookies to ~/.config/perplexity/cookies.json."""
    COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(COOKIE_PATH, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"Saved {len(cookies)} cookies to {COOKIE_PATH}", file=sys.stderr)
    return COOKIE_PATH


# ─── OTP extraction wrapper ──────────────────────────────────────────────────

def fetch_otp_from_email(
    otp_email: str,
    otp_app_password: str,
    forward_to: Optional[str] = None,
    bw_item: Optional[str] = None,
    bw_field: str = "gmail",
    timeout: int = 120,
) -> Optional[str]:
    """Run extract_otp.py and return the OTP string or None."""
    cmd = [sys.executable, str(EXTRACT_OTP)]
    if otp_email:
        cmd += ["--email", otp_email]
    if otp_app_password:
        cmd += ["--app-password", otp_app_password]
    if forward_to:
        cmd += ["--forward-to", forward_to]
    if bw_item:
        cmd += ["--bw-item", bw_item]
    cmd += ["--bw-field", bw_field]
    cmd += ["--timeout", str(timeout)]

    print(f"Running: {' '.join(cmd)}", file=sys.stderr)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    if result.returncode != 0:
        print(f"extract_otp.py failed: {result.stderr}", file=sys.stderr)
        return None

    try:
        data = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        print(f"extract_otp.py invalid output: {result.stdout}", file=sys.stderr)
        return None

    otp = data.get("otp")
    if otp:
        print(f"Got OTP: {otp}", file=sys.stderr)
    else:
        print(f"No OTP found: {data.get('error', 'unknown')}", file=sys.stderr)
    return otp


# ─── Bitwarden integration ──────────────────────────────────────────────────

def _bw_cmd(args: list[str]) -> str:
    """Run a Bitwarden CLI command with unlocked vault."""
    bw_pass = subprocess.run(
        ["security", "find-generic-password", "-a", "bw-master-password", "-w"],
        capture_output=True, text=True
    ).stdout.strip()

    if not bw_pass:
        raise RuntimeError("Could not get bw master password from Keychain")

    session = subprocess.run(
        ["bw", "unlock", "--passwordenv", "BW_PASSWORD", "--raw"],
        env={**os.environ, "BW_PASSWORD": bw_pass},
        capture_output=True, text=True
    ).stdout.strip()

    result = subprocess.run(
        ["bw", *args],
        env={**os.environ, "BW_SESSION": session},
        capture_output=True, text=True
    )
    return result.stdout.strip()


def bw_save_cookies(cookies: dict, item_name: str = "perplexity.ai") -> bool:
    """Save cookies to a Bitwarden secure note."""
    template = _bw_cmd(["get", "template", "item"])
    if not template:
        return False

    try:
        item = json.loads(template)
    except json.JSONDecodeError:
        return False

    item["type"] = 2  # Secure Note
    item["name"] = item_name
    item["notes"] = json.dumps(cookies, indent=2)

    # Check if item already exists
    existing = _bw_cmd(["list", "items", "--search", item_name])
    try:
        existing_items = json.loads(existing) if existing else []
    except json.JSONDecodeError:
        existing_items = []

    for ex in existing_items:
        if ex.get("name") == item_name:
            # Edit existing
            raw = _bw_cmd(["get", "item", ex["id"]])
            if raw:
                existing_item = json.loads(raw)
                existing_item["notes"] = item["notes"]
                encoded = _bw_cmd(["encode"])
                result = _bw_cmd(["edit", "item", ex["id"], json.dumps(existing_item)])
                print(f"Updated Bitwarden item '{item_name}'", file=sys.stderr)
                return True

    # Create new
    encoded = subprocess.run(
        ["bw", "encode"],
        input=json.dumps(item), capture_output=True, text=True
    ).stdout.strip()

    # Need to do this with bw session
    bw_pass = subprocess.run(
        ["security", "find-generic-password", "-a", "bw-master-password", "-w"],
        capture_output=True, text=True
    ).stdout.strip()
    session = subprocess.run(
        ["bw", "unlock", "--passwordenv", "BW_PASSWORD", "--raw"],
        env={**os.environ, "BW_PASSWORD": bw_pass},
        capture_output=True, text=True
    ).stdout.strip()

    result = subprocess.run(
        ["bw", "create", "item", encoded],
        env={**os.environ, "BW_SESSION": session},
        capture_output=True, text=True
    )
    print(f"Created Bitwarden item '{item_name}'", file=sys.stderr)
    return True


def bw_load_cookies(item_name: str = "perplexity.ai") -> Optional[dict]:
    """Load cookies from a Bitwarden secure note."""
    raw = _bw_cmd(["get", "item", item_name])
    if not raw:
        return None

    try:
        item = json.loads(raw)
        return json.loads(item.get("notes", "{}"))
    except (json.JSONDecodeError, KeyError):
        return None


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automated Perplexity login via CloakBrowser CDP"
    )
    parser.add_argument("--email", required=True,
                        help="Perplexity login email address")
    parser.add_argument("--otp-email",
                        help="Gmail address to check for OTP (defaults to --email)")
    parser.add_argument("--otp-app-password",
                        help="Gmail app password for OTP extraction")
    parser.add_argument("--forward-to",
                        help="If --email forwards to another Gmail, check this inbox instead")
    parser.add_argument("--bw-item", default="perplexity-login",
                        help="Bitwarden item name for credential lookup (default: perplexity-login)")
    parser.add_argument("--bw-field", default="gmail",
                        help="Bitwarden custom field name for app password")
    parser.add_argument("--otp-timeout", type=int, default=120,
                        help="Seconds to wait for OTP email (default: 120)")
    parser.add_argument("--bw-save", action="store_true",
                        help="Save cookies to Bitwarden secure note after login")
    parser.add_argument("--bw-load", action="store_true",
                        help="Load cookies from Bitwarden instead of logging in")
    parser.add_argument("--keep-browser", action="store_true",
                        help="Don't kill CloakBrowser after login (for debugging)")
    parser.add_argument("--persist-profile", action="store_true", default=True,
                        help="Persist the browser profile for reuse in debug sessions (default: True)")
    parser.add_argument("--no-persist-profile", action="store_false", dest="persist_profile",
                        help="Don't persist the browser profile after login")
    parser.add_argument("--reuse-profile", action="store_true",
                        help="Reuse the persisted authenticated profile instead of fresh login")
    parser.add_argument("--headless", action="store_true",
                        help="Run CloakBrowser in headless mode (no GUI window)")
    args = parser.parse_args()

    # ── Load from Bitwarden ──────────────────────────────────────────────────
    if args.bw_load:
        cookies = bw_load_cookies("perplexity.ai")
        if cookies:
            save_cookies(cookies)
            print("Loaded cookies from Bitwarden", file=sys.stderr)
            return 0
        print("No cookies found in Bitwarden — falling through to login", file=sys.stderr)

    # Ensure websocket-client is importable (auto-install if needed)
    try:
        import websocket  # noqa: F401
    except ImportError:
        import subprocess as _sp
        for pip in ["pip3", "pip"]:
            _sp.run([sys.executable, "-m", pip, "install", "--break-system-packages", "websocket-client"],
                    capture_output=True, timeout=60)

    # ── Launch CloakBrowser ──────────────────────────────────────────────────
    if not launch_cloakbrowser(reuse_persisted=args.reuse_profile, headless=args.headless):
        return 1

    try:
        # ── Connect CDP ──────────────────────────────────────────────────────
        ws, send = _cdp_connect()

        # ── Sign-in flow ─────────────────────────────────────────────────────
        page_load_wait = 5 if not args.headless else 10
        print(f"Waiting {page_load_wait}s for page load…", file=sys.stderr)
        time.sleep(page_load_wait)

        # Verify page is loaded (not Cloudflare block)
        title = _eval(send, "document.title")
        body_preview = _eval(send, "document.body?.innerText?.substring(0, 100) || ''")
        print(f"Page title: {title}", file=sys.stderr)
        if "moment" in title.lower() or "verifying" in body_preview.lower():
            print("ERROR: Cloudflare challenge detected — CloakBrowser may not be working", file=sys.stderr)
            return 1

        # ── Check if already logged in (e.g., from persisted profile) ──────────
        if is_logged_in(send):
            print("Already logged in — skipping auth flow", file=sys.stderr)
        else:
            # ── Sign-in flow ─────────────────────────────────────────────────
            print("Clicking Sign In…", file=sys.stderr)
            if not click_sign_in(send):
                print("ERROR: Could not find Sign In button", file=sys.stderr)
                return 1

            print(f"Filling email: {args.email}", file=sys.stderr)
            # Give the sign-in dialog time to render
            time.sleep(3)
            if not fill_email(send, args.email):
                print("ERROR: Could not fill email", file=sys.stderr)
                return 1

            time.sleep(1)

            print("Submitting email login…", file=sys.stderr)
            if not submit_email_login(send, args.email):
                print("ERROR: Could not submit email login", file=sys.stderr)
                return 1

            # Debug: check page URL after submit
            post_url = _eval(send, "location.href")
            print(f"Page URL after submit: {post_url}", file=sys.stderr)

            print("Waiting for verification page…", file=sys.stderr)
            if not wait_for_verification_page(send):
                print("ERROR: Verification page did not appear", file=sys.stderr)
                return 1

            # ── Extract OTP ──────────────────────────────────────────────────
            otp_email = args.otp_email or args.email
            print(f"Fetching OTP for {otp_email}…", file=sys.stderr)

            otp = fetch_otp_from_email(
                otp_email=otp_email,
                otp_app_password=args.otp_app_password or "",
                forward_to=args.forward_to,
                bw_item=args.bw_item,
                bw_field=args.bw_field,
                timeout=args.otp_timeout,
            )

            if not otp:
                # Try without app password — use bw for both
                print("Retrying OTP with Bitwarden credentials…", file=sys.stderr)
                otp = fetch_otp_from_email(
                    otp_email="",
                    otp_app_password="",
                    forward_to=args.forward_to or args.email,
                    bw_item=args.bw_item,
                    bw_field=args.bw_field,
                    timeout=args.otp_timeout,
                )

            if not otp:
                url = _eval(send, "location.href")
                print(f"Page URL: {url}", file=sys.stderr)
                return 1

            # ── Fill OTP and confirm ─────────────────────────────────────────
            print(f"Filling OTP: {otp}", file=sys.stderr)
            fill_otp(send, otp)

            print("Waiting for login completion…", file=sys.stderr)
            if not wait_for_login(send):
                print("ERROR: Login may have failed — check page", file=sys.stderr)
                url = _eval(send, "location.href")
                body = _eval(send, "document.body?.innerText?.substring(0, 500) || 'N/A'")
                print(f"URL: {url}", file=sys.stderr)
                print(f"Body: {body}", file=sys.stderr)
                return 1

        # ── Extract cookies ──────────────────────────────────────────────────
        print("Extracting cookies…", file=sys.stderr)
        cookies = extract_cookies(send)
        save_cookies(cookies)

        # Verify
        session_token = cookies.get("__Secure-next-auth.session-token")
        if session_token:
            print(f"Session token obtained ({len(session_token)} chars)", file=sys.stderr)
        else:
            print("WARNING: No session token in cookies", file=sys.stderr)

        # ── Save to Bitwarden ────────────────────────────────────────────────
        if args.bw_save:
            bw_save_cookies(cookies)

        # ── Persist browser profile for debug reuse ──────────────────────────
        if args.persist_profile:
            _persist_profile()

        ws.close()
        print("Login successful!", file=sys.stderr)

        # Output cookies path for chaining
        print(str(COOKIE_PATH))

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    finally:
        if not args.keep_browser:
            stop_cloakbrowser(persist=args.persist_profile)


if __name__ == "__main__":
    sys.exit(main())
