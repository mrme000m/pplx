#!/usr/bin/env python3
"""Diagnostic script for PPLX — tests key endpoints with short timeouts."""

import sys
import json
from pathlib import Path

# Ensure we use the local pplx package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("=" * 60)
print("PPLX Diagnostic Script")
print("=" * 60)

# ------------------------------------------------------------------
# 1. Cookie loading
# ------------------------------------------------------------------
print("\n[1] Loading cookies...")
try:
    from pplx.bw_cookies import load_cookies
    cookies = load_cookies()
    print(f"  ✓ Loaded {len(cookies)} cookie(s)")
    for k in cookies:
        print(f"    - {k[:50]}...")
except Exception as e:
    print(f"  ✗ Cookie load failed: {e}")
    sys.exit(1)

# ------------------------------------------------------------------
# 2. Initialize client (with timeout protection)
# ------------------------------------------------------------------
print("\n[2] Initializing PerplexityClient...")
try:
    from pplx.client import PerplexityClient
    # We already loaded cookies; pass them in to avoid double-load
    client = PerplexityClient(cookies=cookies)
    print(f"  ✓ Client initialized")
    print(f"    own={client.own}, copilot={client.copilot}")
except Exception as e:
    print(f"  ✗ Client init failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ------------------------------------------------------------------
# 3. Test auth/session endpoint
# ------------------------------------------------------------------
print("\n[3] Testing /api/auth/session...")
try:
    resp = client.session.get(
        "https://www.perplexity.ai/api/auth/session",
        timeout=10,
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('content-type', 'N/A')}")
    if resp.status_code == 200:
        data = resp.json()
        user = data.get("user", {})
        print(f"  User: {user.get('email', 'not logged in')}")
        print(f"  is_enterprise: {user.get('is_enterprise')}")
    else:
        print(f"  Body preview: {resp.text[:200]}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ------------------------------------------------------------------
# 4. Test models/config endpoint
# ------------------------------------------------------------------
print("\n[4] Testing /rest/models/config...")
try:
    resp = client.session.get(
        "https://www.perplexity.ai/rest/models/config",
        params={"config_schema": "v1", "version": "2.18", "source": "default"},
        timeout=10,
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('content-type', 'N/A')}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Response keys: {list(data.keys())}")
        models = data.get("models", {})
        print(f"  Models count: {len(models)}")
        if models:
            print(f"  First model: {list(models.keys())[0]}")
    else:
        print(f"  Body preview: {resp.text[:500]}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ------------------------------------------------------------------
# 5. Test search endpoint (lightweight query, 15s timeout)
# ------------------------------------------------------------------
print("\n[5] Testing /rest/sse/perplexity_ask (lightweight search)...")
try:
    payload = {
        "query_str": "hello",
        "params": {
            "frontend_context_uuid": "test-diag-0000-0000-000000000001",
            "frontend_uuid": "test-diag-0000-0000-000000000002",
            "mode": "concise",
            "model_preference": "turbo",
            "source": "default",
            "sources": ["web"],
            "version": "2.18",
            "search_focus": "internet",
            "timezone": "UTC",
            "language": "en-US",
            "is_incognito": True,
            "is_related_query": False,
            "prompt_source": "user",
            "query_source": "home",
            "use_schematized_api": True,
            "send_back_text_in_streaming_api": False,
            "skip_search_enabled": False,
            "local_search_enabled": False,
            "should_ask_for_mcp_tool_confirmation": True,
            "browser_agent_allow_once_from_toggle": False,
            "force_enable_browser_agent": False,
            "supported_features": ["browser_agent_permission_banner_v1.1"],
            "extended_context": False,
            "supported_block_use_cases": [
                "answer_modes", "media_items", "knowledge_cards",
                "inline_entity_cards", "place_widgets", "finance_widgets",
                "sports_widgets", "shopping_widgets", "jobs_widgets",
                "search_result_widgets", "inline_images", "inline_assets",
                "placeholder_cards", "diff_blocks", "canvas_mode",
            ],
        },
    }
    resp = client.session.post(
        "https://www.perplexity.ai/rest/sse/perplexity_ask",
        json=payload,
        stream=True,
        timeout=15,
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('content-type', 'N/A')}")
    
    if resp.status_code == 200:
        # Read first few chunks
        chunk_count = 0
        for chunk in resp.iter_lines(delimiter=b"\r\n\r\n"):
            content = chunk.decode("utf-8", errors="replace")
            if content.startswith("event: message"):
                chunk_count += 1
                if chunk_count == 1:
                    print(f"  First chunk preview: {content[:200]}...")
            elif content.startswith("event: end_of_stream"):
                print(f"  ✓ Stream ended normally after {chunk_count} message(s)")
                break
            if chunk_count >= 3:
                print(f"  ✓ Received {chunk_count}+ chunks, closing...")
                resp.close()
                break
    else:
        print(f"  Body preview: {resp.text[:500]}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Diagnostic complete.")
print("=" * 60)
