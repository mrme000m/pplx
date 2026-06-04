#!/usr/bin/env python3
"""
Health check - quick and full diagnostic of Perplexity auth state.
"""

import argparse
import json
import subprocess
import sys
import importlib.util
from pathlib import Path


def check_imports() -> dict:
    deps = {
        "curl_cffi": "curl_cffi",
        "websocket": "websocket",
        "cloakbrowser": "CloakBrowser",
        "bitwarden": "bw",
    }
    result = {}
    for name, import_path in deps.items():
        if import_path == "bw":
            r = subprocess.run(["bw", "--version"], capture_output=True)
            result[name] = {"ok": r.returncode == 0, "version": r.stdout.strip() if r.returncode == 0 else None}
        else:
            spec = importlib.util.find_spec(import_path)
            result[name] = {"ok": spec is not None, "version": None}
    return result


def check_cookies() -> dict:
    path = Path("~/.config/perplexity/cookies.json").expanduser()
    if not path.exists():
        return {"status": "missing"}
    try:
        data = json.loads(path.read_text())
        cookies = data.get("cookies", {})
        return {"status": "present", "count": len(cookies), "last_saved": data.get("last_saved")}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_bitwarden() -> dict:
    r = subprocess.run(["bw", "list", "items", "--search", "perplexity"], capture_output=True, text=True)
    if r.returncode != 0:
        return {"status": "error"}
    try:
        items = json.loads(r.stdout)
        found = [i for i in items if i.get("name") in ("perplexity.ai", "perplexity-login")]
        return {"status": "present" if found else "not_found", "count": len(found)}
    except Exception:
        return {"status": "error"}


def check_sdk() -> dict:
    spec = importlib.util.find_spec("pplx_sdk")
    if not spec:
        return {"status": "not_installed"}
    try:
        import pplx_sdk
        return {"status": "ok", "version": pplx_sdk.__version__ if hasattr(pplx_sdk, "__version__") else "unknown"}
    except Exception as e:
        return {"status": "import_error", "error": str(e)}


def validate_session() -> dict:
    try:
        from pplx_sdk import PerplexityClient
        client = PerplexityClient()
        session = client.get_session()
        if session:
            return {"status": "valid", "user": session.get("user", {}).get("email", "unknown")}
        return {"status": "invalid"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_health_check(quick: bool = False, full: bool = False) -> dict:
    result = {"timestamp": str(Path("/").stat().st_ctime), "checks": {}}

    result["checks"]["imports"] = check_imports()

    if not quick:
        result["checks"]["cookies"] = check_cookies()
        result["checks"]["bitwarden"] = check_bitwarden()
        result["checks"]["sdk"] = check_sdk()

    if full:
        result["checks"]["session"] = validate_session()

    return result


def main():
    parser = argparse.ArgumentParser(description="Perplexity health check")
    parser.add_argument("--quick", action="store_true", help="Quick check (imports only)")
    parser.add_argument("--full", action="store_true", help="Full diagnostic including API validation")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = run_health_check(quick=args.quick, full=args.full)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=== Perplexity Health Check ===")
        for check, data in result["checks"].items():
            print(f"\n{check}:")
            if isinstance(data, dict):
                for k, v in data.items():
                    print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())