#!/usr/bin/env python3
"""
Deterministic test suite for the PPLX CLI.

Tests all commands, reports pass/fail, and cleans up any mutations.
All searches use --incognito to minimize library pollution.

Usage:
    export PERPLEXITY_COOKIES_PATH=/path/to/cookies.json
    python scripts/test_pplx_cli.py

    # Include destructive tests (create/delete spaces, threads, assets)
    python scripts/test_pplx_cli.py --destructive

Exit codes:
    0 = all tests passed, cleanup successful
    1 = one or more tests failed
    2 = cleanup failed (tests may have passed)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
CLI_SCRIPT = PROJECT_ROOT / "pplx_cli.py"
COOKIE_PATH = Path.home() / ".config" / "perplexity" / "cookies.json"

# Use venv Python if available, fallback to sys.executable
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

# Test query used for searches (deterministic, unlikely to collide with real queries)
TEST_QUERY = "pplx-cli-deterministic-test-query-42"

# ---------------------------------------------------------------------------
# Test result tracking
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    passed: bool
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    error: str = ""

@dataclass
class TestState:
    results: list[TestResult] = field(default_factory=list)
    mutations: dict[str, list[dict]] = field(default_factory=lambda: {
        "threads": [],
        "spaces": [],
        "assets": [],
        "tasks": [],
    })
    before_threads: set[str] = field(default_factory=set)
    before_spaces: set[str] = field(default_factory=set)
    before_assets: set[str] = field(default_factory=set)
    destructive: bool = False

    def add(self, result: TestResult) -> None:
        self.results.append(result)

    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def summary(self) -> str:
        total = len(self.results)
        passed = self.passed()
        failed = self.failed()
        return f"{passed}/{total} passed, {failed}/{total} failed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env() -> dict[str, str]:
    """Return environment with cookies configured."""
    env = os.environ.copy()
    cookie_path = os.getenv("PERPLEXITY_COOKIES_PATH", str(COOKIE_PATH))
    if Path(cookie_path).exists():
        env["PERPLEXITY_COOKIES_PATH"] = cookie_path
    return env


def _run(
    *args: str,
    timeout: int = 30,
    capture_json: bool = False,
) -> tuple[int, str, str, Any | None]:
    """Run a CLI command and return (rc, stdout, stderr, parsed_json)."""
    cmd = [PYTHON, str(CLI_SCRIPT), *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_env(),
    )
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    parsed = None
    if capture_json and stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            pass
    return result.returncode, stdout, stderr, parsed


def _test(
    state: TestState,
    name: str,
    *args: str,
    timeout: int = 30,
    expect_rc: int = 0,
    expect_contains: str | list[str] | None = None,
    expect_json: bool = False,
    json_predicate: callable | None = None,
) -> tuple[str, str, Any | None]:
    """Run a test case and record the result."""
    start = datetime.now()
    try:
        rc, stdout, stderr, parsed = _run(*args, timeout=timeout, capture_json=expect_json)
    except subprocess.TimeoutExpired as e:
        duration = int((datetime.now() - start).total_seconds() * 1000)
        state.add(TestResult(name, False, "", "", duration, f"Timeout after {timeout}s"))
        return "", "", None
    except Exception as e:
        duration = int((datetime.now() - start).total_seconds() * 1000)
        state.add(TestResult(name, False, "", "", duration, str(e)))
        return "", "", None

    duration = int((datetime.now() - start).total_seconds() * 1000)
    error = ""
    passed = rc == expect_rc

    if passed and expect_contains:
        checks = [expect_contains] if isinstance(expect_contains, str) else expect_contains
        for check in checks:
            if check not in stdout and check not in stderr:
                passed = False
                error = f"Expected output to contain: {check!r}"
                break

    if passed and expect_json and parsed is None:
        passed = False
        error = "Expected valid JSON output"

    if passed and json_predicate and parsed is not None:
        try:
            if not json_predicate(parsed):
                passed = False
                error = "JSON predicate failed"
        except Exception as e:
            passed = False
            error = f"JSON predicate error: {e}"

    if not passed and not error:
        if rc != expect_rc:
            error = f"Exit code {rc}, expected {expect_rc}"
        else:
            error = "Assertion failed"

    state.add(TestResult(name, passed, stdout, stderr, duration, error))
    return stdout, stderr, parsed


# ---------------------------------------------------------------------------
# State capture (for cleanup)
# ---------------------------------------------------------------------------

def _capture_threads() -> set[str]:
    """Capture all thread context_uuids."""
    uuids: set[str] = set()
    offset = 0
    limit = 100
    while True:
        rc, stdout, _, parsed = _run(
            "threads", "list",
            "--limit", str(limit),
            "--offset", str(offset),
            timeout=30,
            capture_json=True,
        )
        if rc != 0 or not parsed:
            break
        items = parsed if isinstance(parsed, list) else parsed.get("threads", [])
        if not items:
            break
        for item in items:
            if isinstance(item, dict):
                cuuid = item.get("context_uuid")
                if cuuid:
                    uuids.add(cuuid)
        if len(items) < limit:
            break
        offset += len(items)
    return uuids


def _capture_spaces() -> set[str]:
    """Capture all space UUIDs."""
    uuids: set[str] = set()
    offset = 0
    limit = 100
    while True:
        rc, stdout, _, parsed = _run(
            "spaces", "list",
            "--limit", str(limit),
            "--offset", str(offset),
            timeout=30,
            capture_json=True,
        )
        if rc != 0 or not parsed:
            break
        items = parsed if isinstance(parsed, list) else parsed.get("spaces", [])
        if not items:
            break
        for item in items:
            if isinstance(item, dict):
                uuid = item.get("uuid")
                if uuid:
                    uuids.add(uuid)
        if len(items) < limit:
            break
        offset += len(items)
    return uuids


def _capture_assets() -> set[str]:
    """Capture all asset IDs."""
    ids: set[str] = set()
    rc, stdout, _, parsed = _run(
        "assets", "list",
        "--limit", "1000",
        timeout=30,
        capture_json=True,
    )
    if rc == 0 and parsed and isinstance(parsed, dict):
        for asset in parsed.get("assets", []):
            if isinstance(asset, dict):
                aid = asset.get("asset_id")
                if aid:
                    ids.add(aid)
    return ids


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def _cleanup_threads(state: TestState) -> None:
    """Delete threads created during testing."""
    after = _capture_threads()
    new_threads = after - state.before_threads
    if not new_threads:
        print("  No new threads to clean up.")
        return

    print(f"  Cleaning up {len(new_threads)} new thread(s)...")
    # Delete in batches of 10
    batch = list(new_threads)[:10]
    rc, stdout, stderr, _ = _run(
        "threads", "delete",
        ",".join(batch),
        "--force",
        timeout=60,
    )
    if rc == 0:
        print(f"    Deleted {len(batch)} thread(s).")
    else:
        print(f"    Failed to delete threads: {stderr or stdout}")


def _cleanup_spaces(state: TestState) -> None:
    """Delete spaces created during testing."""
    after = _capture_spaces()
    new_spaces = after - state.before_spaces
    if not new_spaces:
        print("  No new spaces to clean up.")
        return

    print(f"  Cleaning up {len(new_spaces)} new space(s)...")
    for uuid in new_spaces:
        rc, stdout, stderr, _ = _run(
            "spaces", "delete",
            uuid,
            "--force",
            timeout=30,
        )
        if rc == 0:
            print(f"    Deleted space {uuid}.")
        else:
            print(f"    Failed to delete space {uuid}: {stderr or stdout}")


# ---------------------------------------------------------------------------
# Test suites
# ---------------------------------------------------------------------------

def test_basic(state: TestState) -> None:
    """Test --version and --help."""
    print("\n=== Basic ===")
    _test(state, "version", "--version", expect_contains="0.1.0")
    _test(state, "help", "--help", expect_contains="search")


def test_info(state: TestState) -> None:
    """Test info/status commands."""
    print("\n=== Info / Status ===")
    _test(state, "models", "models", expect_contains="AUTO:")
    _test(state, "models verbose", "models", "--verbose", expect_contains="[")
    _test(state, "models raw", "models", "--raw", expect_json=True,
          json_predicate=lambda d: "auto" in d and "pro" in d)
    _test(state, "profile", "profile", expect_json=True,
          json_predicate=lambda d: "email" in d)
    _test(state, "settings", "settings", expect_json=True,
          json_predicate=lambda d: "subscription_tier" in d)
    _test(state, "credits", "credits", expect_json=True)
    _test(state, "billing", "billing", expect_json=True)
    _test(state, "notifications", "notifications")
    _test(state, "ai-profile", "ai-profile")
    _test(state, "rate-limits raw", "rate-limits", "--raw", expect_json=True)
    _test(state, "discover", "discover", "--limit", "2", expect_json=True)
    _test(state, "discover category", "discover", "--category", "Technology", "--limit", "2", expect_json=True)
    _test(state, "workflows", "workflows", expect_json=True)


def test_sources(state: TestState) -> None:
    """Test source connector commands."""
    print("\n=== Sources ===")
    _test(state, "sources list", "sources", "list", expect_json=True)
    _test(state, "sources discover", "sources", "discover", expect_json=True)


def test_threads(state: TestState) -> None:
    """Test thread management commands."""
    print("\n=== Threads ===")
    _test(state, "threads list", "threads", "list", "--limit", "3", expect_json=True)
    _test(state, "threads recent", "threads", "recent", expect_json=True)
    _test(state, "threads pinned", "threads", "pinned", expect_json=True)

    # Get a thread slug from list for detail tests
    rc, stdout, _, parsed = _run("threads", "list", "--limit", "1", capture_json=True)
    if rc == 0 and parsed and isinstance(parsed, list) and len(parsed) > 0:
        slug = parsed[0].get("slug", "")
        if slug:
            _test(state, "threads get", "threads", "get", slug, expect_json=True)
            _test(state, "threads share", "threads", "share", slug, expect_json=True)


def test_spaces(state: TestState) -> None:
    """Test space management commands."""
    print("\n=== Spaces ===")
    _test(state, "spaces list", "spaces", "list", "--limit", "3", expect_json=True)
    _test(state, "spaces landing", "spaces", "landing", "--limit", "3", expect_json=True)
    _test(state, "spaces recent", "spaces", "recent", expect_json=True)
    _test(state, "spaces writable", "spaces", "writable", expect_json=True)
    _test(state, "spaces pins", "spaces", "pins", expect_json=True)

    # Get a space for detail tests
    rc, stdout, _, parsed = _run("spaces", "list", "--limit", "1", capture_json=True)
    if rc == 0 and parsed:
        items = parsed if isinstance(parsed, list) else parsed.get("spaces", [])
        if items and isinstance(items[0], dict):
            space = items[0]
            slug = space.get("slug", "")
            uuid = space.get("uuid", "")
            if slug:
                _test(state, "spaces get", "spaces", "get", slug, expect_json=True)
                _test(state, "spaces threads", "spaces", "threads", slug, "--limit", "2", expect_json=True)
                _test(state, "spaces articles", "spaces", "articles", slug, "--limit", "2", expect_json=True)
                _test(state, "spaces links list", "spaces", "links", "list", slug, expect_json=True)
            if uuid:
                _test(state, "spaces files", "spaces", "files", uuid, "--page-size", "2", expect_json=True)
                _test(state, "spaces skills list", "spaces", "skills", "list", uuid, "--limit", "2", expect_json=True)
                _test(state, "spaces tasks", "spaces", "tasks", uuid, expect_json=True)
                _test(state, "spaces pinned-threads", "spaces", "pinned-threads", uuid, expect_json=True)
                _test(state, "spaces memory-config", "spaces", "memory-config", uuid, expect_json=True)
                _test(state, "spaces upload-status", "spaces", "upload-status", uuid, expect_json=True)


def test_assets(state: TestState) -> None:
    """Test asset management commands."""
    print("\n=== Assets ===")
    _test(state, "assets list", "assets", "list", "--limit", "2", expect_json=True)
    _test(state, "assets pins", "assets", "pins", "--limit", "2", expect_json=True)
    _test(state, "assets shared", "assets", "shared", "--limit", "2", expect_json=True)


def test_memories(state: TestState) -> None:
    """Test memory management commands."""
    print("\n=== Memories ===")
    _test(state, "memories list", "memories", "list", "--limit", "3", expect_json=True)

    # Get a memory key for detail test
    rc, stdout, _, parsed = _run("memories", "list", "--limit", "1", capture_json=True)
    if rc == 0 and parsed and isinstance(parsed, dict):
        memories = parsed.get("memories", [])
        if memories and isinstance(memories[0], dict):
            key = memories[0].get("memory_key", "")
            if key:
                _test(state, "memories get", "memories", "get", key, expect_json=True)


def test_tasks(state: TestState) -> None:
    """Test task management commands."""
    print("\n=== Tasks ===")
    _test(state, "tasks list", "tasks", "list", expect_json=True)
    _test(state, "tasks recurring", "tasks", "recurring", expect_json=True)


def test_computer_tasks(state: TestState) -> None:
    """Test computer/ASI task commands."""
    print("\n=== Computer Tasks ===")
    _test(state, "computer-tasks", "computer-tasks", "--limit", "2", expect_json=True)


def test_finance(state: TestState) -> None:
    """Test finance commands."""
    print("\n=== Finance ===")
    _test(state, "finance quote", "finance", "quote", "XAUUSD", expect_json=True,
          json_predicate=lambda d: "symbol" in d and "price" in d)


def test_search(state: TestState) -> None:
    """Test search commands (all use --incognito)."""
    print("\n=== Search ===")

    # Auto mode
    _test(state, "search auto", "search", TEST_QUERY, "--mode", "auto", "--incognito",
          timeout=60, expect_contains="pplx-cli-deterministic-test-query-42")

    # Pro mode
    _test(state, "search pro", "search", TEST_QUERY, "--mode", "pro", "--incognito",
          timeout=60)

    # Reasoning mode
    _test(state, "search reasoning", "search", TEST_QUERY, "--mode", "reasoning", "--incognito",
          timeout=60)

    # Thinking flag
    _test(state, "search thinking", "search", TEST_QUERY, "--mode", "pro", "--thinking", "--incognito",
          timeout=60)

    # With sources
    _test(state, "search sources", "search", TEST_QUERY, "--mode", "auto", "--sources", "web", "--incognito",
          timeout=60)

    # Raw output
    _test(state, "search raw", "search", TEST_QUERY, "--mode", "auto", "--raw", "--incognito",
          timeout=60, expect_json=True,
          json_predicate=lambda d: "backend_uuid" in d)

    # Follow-up (need backend_uuid from a search)
    rc, stdout, _, parsed = _run(
        "search", TEST_QUERY, "--mode", "auto", "--raw", "--incognito",
        timeout=60, capture_json=True,
    )
    if rc == 0 and parsed and isinstance(parsed, dict) and "backend_uuid" in parsed:
        backend_uuid = parsed["backend_uuid"]
        _test(state, "follow-up", "follow-up", "explain more", backend_uuid,
              "--mode", "auto", timeout=60)


def test_space_search(state: TestState) -> None:
    """Test searching within a space."""
    print("\n=== Space Search ===")
    rc, stdout, _, parsed = _run("spaces", "list", "--limit", "1", capture_json=True)
    if rc == 0 and parsed:
        items = parsed if isinstance(parsed, list) else parsed.get("spaces", [])
        if items and isinstance(items[0], dict):
            uuid = items[0].get("uuid", "")
            if uuid:
                _test(state, "spaces search", "spaces", "search", uuid, TEST_QUERY,
                      "--mode", "auto", timeout=60)


def test_destructive(state: TestState) -> None:
    """Test mutating commands and track resources for cleanup."""
    if not state.destructive:
        print("\n=== Destructive (skipped, use --destructive) ===")
        return

    print("\n=== Destructive ===")

    # Create a test space
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_space_title = f"pplx-test-space-{ts}"
    rc, stdout, _, parsed = _run(
        "spaces", "create",
        "--title", test_space_title,
        "--description", "Temporary test space",
        timeout=30, capture_json=True,
    )
    if rc == 0 and parsed and isinstance(parsed, dict):
        space_uuid = parsed.get("uuid", "")
        if space_uuid:
            state.mutations["spaces"].append({"uuid": space_uuid, "title": test_space_title})
            _test(state, "spaces create", "spaces", "create",
                  "--title", test_space_title, "--description", "test",
                  expect_json=True, json_predicate=lambda d: "uuid" in d)

            # Edit the space
            _test(state, "spaces edit", "spaces", "edit", space_uuid,
                  "--title", f"{test_space_title}-edited",
                  expect_json=True)

            # Upload a tiny test file
            test_file = Path(f"/tmp/pplx_test_{ts}.txt")
            test_file.write_text("This is a test file for PPLX CLI.")
            _test(state, "spaces upload", "spaces", "upload", space_uuid, str(test_file),
                  expect_json=True)
            test_file.unlink(missing_ok=True)

            # Check upload status
            _test(state, "spaces upload-status after", "spaces", "upload-status", space_uuid,
                  expect_json=True)

            # Delete the space
            _test(state, "spaces delete", "spaces", "delete", space_uuid, "--force",
                  expect_json=True)
            # Remove from mutations since we already deleted it
            state.mutations["spaces"] = [s for s in state.mutations["spaces"] if s["uuid"] != space_uuid]

    # Test thread rename (on an existing thread)
    rc, stdout, _, parsed = _run("threads", "list", "--limit", "1", capture_json=True)
    if rc == 0 and parsed and isinstance(parsed, list) and len(parsed) > 0:
        context_uuid = parsed[0].get("context_uuid", "")
        if context_uuid:
            # Save original title
            original_title = parsed[0].get("title", "")
            _test(state, "threads rename", "threads", "rename", context_uuid,
                  f"pplx-test-rename-{ts}", expect_json=True)
            # Rename back
            _run("threads", "rename", context_uuid, original_title, timeout=30)


def test_refresh_cookies_help(state: TestState) -> None:
    """Test refresh-cookies help (don't actually run the refresh)."""
    print("\n=== Refresh Cookies ===")
    _test(state, "refresh-cookies help", "refresh-cookies", "--help", expect_contains="headless")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic PPLX CLI test suite")
    parser.add_argument("--destructive", action="store_true",
                        help="Run mutating tests and clean up afterwards")
    parser.add_argument("--skip-cleanup", action="store_true",
                        help="Skip cleanup (for debugging)")
    parser.add_argument("--test", default="",
                        help="Run only tests matching this prefix (e.g., 'search')")
    args = parser.parse_args()

    # Verify setup
    if not Path(PYTHON).exists():
        print(f"ERROR: Python not found: {PYTHON}")
        return 1
    if not CLI_SCRIPT.exists():
        print(f"ERROR: CLI script not found: {CLI_SCRIPT}")
        return 1

    cookie_path = os.getenv("PERPLEXITY_COOKIES_PATH", str(COOKIE_PATH))
    if not Path(cookie_path).exists():
        print(f"ERROR: Cookie file not found: {cookie_path}")
        print("Set PERPLEXITY_COOKIES_PATH or ensure ~/.config/perplexity/cookies.json exists.")
        return 1

    print("=" * 60)
    print("PPLX CLI Deterministic Test Suite")
    print("=" * 60)
    print(f"Python: {PYTHON}")
    print(f"CLI:    {CLI_SCRIPT}")
    print(f"Cookies: {cookie_path}")
    print(f"Destructive: {args.destructive}")
    print()

    state = TestState(destructive=args.destructive)

    # Capture pre-test state
    print("Capturing pre-test state...")
    state.before_threads = _capture_threads()
    state.before_spaces = _capture_spaces()
    state.before_assets = _capture_assets()
    print(f"  Threads: {len(state.before_threads)}, Spaces: {len(state.before_spaces)}, Assets: {len(state.before_assets)}")

    # Run tests
    test_suites = [
        ("basic", test_basic),
        ("info", test_info),
        ("sources", test_sources),
        ("threads", test_threads),
        ("spaces", test_spaces),
        ("assets", test_assets),
        ("memories", test_memories),
        ("tasks", test_tasks),
        ("computer", test_computer_tasks),
        ("finance", test_finance),
        ("search", test_search),
        ("space_search", test_space_search),
        ("destructive", test_destructive),
        ("refresh", test_refresh_cookies_help),
    ]

    for name, suite in test_suites:
        if args.test and not name.startswith(args.test):
            continue
        try:
            suite(state)
        except Exception as e:
            print(f"  SUITE ERROR in {name}: {e}")
            traceback.print_exc()

    # Report
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    passed = 0
    failed = 0
    for r in state.results:
        status = "PASS" if r.passed else "FAIL"
        if r.passed:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {r.name:<45} ({r.duration_ms}ms)")
        if not r.passed and r.error:
            print(f"         -> {r.error}")

    print(f"\n{passed}/{len(state.results)} passed, {failed}/{len(state.results)} failed")

    # Cleanup
    if not args.skip_cleanup:
        print("\n" + "=" * 60)
        print("CLEANUP")
        print("=" * 60)

        # Clean up threads created during tests
        _cleanup_threads(state)

        # Clean up spaces created during tests (destructive mode)
        if state.destructive:
            _cleanup_spaces(state)
            # Also clean up any tracked mutations
            for space in state.mutations.get("spaces", []):
                uuid = space.get("uuid")
                if uuid and uuid not in state.before_spaces:
                    print(f"  Deleting tracked test space: {uuid}")
                    _run("spaces", "delete", uuid, "--force", timeout=30)

        # Verify cleanup
        after_threads = _capture_threads()
        after_spaces = _capture_spaces()
        new_threads = after_threads - state.before_threads
        new_spaces = after_spaces - state.before_spaces

        if new_threads:
            print(f"  WARNING: {len(new_threads)} thread(s) still remain after cleanup.")
        else:
            print("  All new threads cleaned up.")

        if new_spaces:
            print(f"  WARNING: {len(new_spaces)} space(s) still remain after cleanup.")
        else:
            print("  All new spaces cleaned up.")
    else:
        print("\nCleanup skipped (--skip-cleanup).")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
