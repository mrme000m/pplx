#!/usr/bin/env python3
"""
CLI command verifier with retries - verifies pplx CLI commands.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import list


class CommandVerifier:
    def __init__(self, max_retries: int = 2, timeout: int = 30, retry_delay: float = 2.0):
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delay = retry_delay

    def verify_command(self, cmd: list, capture_output: bool = True) -> dict:
        last_error = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                print(f"  Retry {attempt}/{self.max_retries} after {self.retry_delay}s...")
                time.sleep(self.retry_delay)

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=capture_output,
                    text=True,
                    timeout=self.timeout,
                )

                if result.returncode == 0:
                    return {
                        "success": True,
                        "attempt": attempt + 1,
                        "output": result.stdout[:500] if capture_output else "",
                        "stderr": result.stderr[:500] if capture_output else "",
                    }

                last_error = result.stderr or "non-zero exit"

            except subprocess.TimeoutExpired:
                last_error = f"timeout after {self.timeout}s"
            except Exception as e:
                last_error = str(e)

        return {
            "success": False,
            "attempt": self.max_retries + 1,
            "error": last_error,
        }

    def verify_all(self, commands: list, capture_output: bool = True) -> dict:
        results = {}
        for cmd in commands:
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            print(f"Verifying: {cmd_str}")
            if isinstance(cmd, list):
                result = self.verify_command(cmd, capture_output)
            else:
                result = self.verify_command(["bash", "-c", cmd], capture_output)
            results[cmd_str] = result
            status = "OK" if result["success"] else f"FAIL ({result.get('error', 'unknown')})"
            print(f"  → {status}")

        return results


def default_commands() -> list:
    return [
        ["pplx", "status"],
        ["pplx", "models"],
        ["pplx", "threads", "list"],
        ["pplx", "spaces", "list"],
        ["pplx", "profile"],
        ["pplx", "settings"],
    ]


def main():
    parser = argparse.ArgumentParser(description="Verify pplx CLI commands")
    parser.add_argument("--commands", nargs="+", help="Commands to verify (as strings)")
    parser.add_argument("--retry", type=int, default=2, help="Max retries")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per command")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    verifier = CommandVerifier(max_retries=args.retry, timeout=args.timeout)

    if args.commands:
        cmds = [c.split() if " " in c else [c] for c in args.commands]
    else:
        cmds = default_commands()

    results = verifier.verify_all(cmds)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n=== Verification Summary ===")
        for cmd, result in results.items():
            status = "OK" if result["success"] else "FAIL"
            print(f"{status}: {cmd}")

        failed = sum(1 for r in results.values() if not r["success"])
        print(f"\n{len(results) - failed}/{len(results)} passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())