#!/usr/bin/env python3
"""
PPLX MCP Server — Expose Perplexity AI as an MCP server for Qwen Code and other MCP clients.

Runs over stdio. Requires the pplx package and valid Perplexity cookies
(BWS_ACCESS_TOKEN or PERPLEXITY_COOKIES_PATH).

Example Qwen Code settings.json entry:
{
  "mcpServers": {
    "pplx": {
      "command": "/Volumes/ExMac/code/MCP/pplx/.venv/bin/python",
      "args": ["/Volumes/ExMac/code/MCP/pplx/pplx_mcp_server.py"],
      "env": {
        "BWS_ACCESS_TOKEN": "${BWS_ACCESS_TOKEN}"
      },
      "timeout": 600000
    }
  }
}
"""

import json
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from pplx import PerplexityClient


APP_NAME = "pplx-mcp-server"


def _refresh_cookies():
    """Run the deterministic cookie refresh pipeline."""
    import subprocess
    from pathlib import Path
    script = Path(__file__).resolve().parent / "scripts" / "refresh_cookies.py"
    if not script.exists():
        return {"success": False, "error": "refresh_cookies.py not found"}
    result = subprocess.run(
        ["python3", str(script)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    ok = result.returncode == 0
    return {
        "success": ok,
        "stdout": result.stdout[-2000:] if result.stdout else "",
        "stderr": result.stderr[-2000:] if result.stderr else "",
    }

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

TOOLS: list[Tool] = [
    Tool(
        name="pplx_search",
        description="Search the web with Perplexity AI. Returns a grounded answer with citations.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
                "mode": {
                    "type": "string",
                    "description": "Search mode: auto, pro, reasoning, deep_research.",
                    "enum": ["auto", "pro", "reasoning", "deep_research"],
                    "default": "auto",
                },
                "model": {
                    "type": "string",
                    "description": "Optional model label (e.g. 'GPT-5.4'). Leave empty for default.",
                    "default": "",
                },
                "thinking": {
                    "type": "boolean",
                    "description": "Enable thinking mode for reasoning models.",
                    "default": False,
                },
                "sources": {
                    "type": "string",
                    "description": "Optional comma-separated source filter.",
                    "default": "",
                },
                "follow_up": {
                    "type": "string",
                    "description": "Optional backend_uuid of a previous query to continue the conversation.",
                    "default": "",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="pplx_list_models",
        description="List available Perplexity models and search modes.",
        inputSchema={
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "Optional mode filter (auto, pro, reasoning, deep_research).",
                    "default": "",
                },
            },
        },
    ),
    Tool(
        name="pplx_list_threads",
        description="List recent Perplexity threads.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of threads to return.",
                    "default": 20,
                },
                "search_term": {
                    "type": "string",
                    "description": "Optional search term.",
                    "default": "",
                },
            },
        },
    ),
    Tool(
        name="pplx_list_spaces",
        description="List Perplexity Spaces (persistent knowledge bases).",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of spaces to return.",
                    "default": 30,
                },
            },
        },
    ),
    Tool(
        name="pplx_search_space",
        description="Search inside a Perplexity Space by UUID.",
        inputSchema={
            "type": "object",
            "properties": {
                "uuid": {
                    "type": "string",
                    "description": "Space UUID.",
                },
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
                "mode": {
                    "type": "string",
                    "description": "Search mode.",
                    "enum": ["auto", "pro", "reasoning", "deep_research"],
                    "default": "auto",
                },
            },
            "required": ["uuid", "query"],
        },
    ),
    Tool(
        name="pplx_refresh_cookies",
        description="Refresh Perplexity session cookies via CloakBrowser + Gmail OTP automation. Call this when any tool returns an auth/session error.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="pplx_validate_session",
        description="Check if the current Perplexity session is still valid without consuming a query.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client() -> PerplexityClient:
    """Create a Perplexity client, propagating env-based auth."""
    return PerplexityClient()


def _extract_answer(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract readable answer from raw Perplexity response."""
    text_obj = raw.get("text", {})
    if isinstance(text_obj, str):
        try:
            text_obj = json.loads(text_obj)
        except json.JSONDecodeError:
            text_obj = None

    answer = None
    citations: list[dict[str, Any]] = []
    if isinstance(text_obj, list):
        for step in text_obj:
            if not isinstance(step, dict):
                continue
            step_type = step.get("step_type", "")
            content = step.get("content", {})
            if step_type == "FINAL" and isinstance(content, dict):
                answer_json = content.get("answer", "")
                if isinstance(answer_json, str):
                    try:
                        parsed = json.loads(answer_json)
                        if isinstance(parsed, dict):
                            answer = parsed.get("answer")
                            citations = parsed.get("citations", [])
                    except json.JSONDecodeError:
                        answer = answer_json
                elif isinstance(answer_json, dict):
                    answer = answer_json.get("answer")
                    citations = answer_json.get("citations", [])
            elif step_type == "SEARCH_RESULTS" and isinstance(content, dict) and not answer:
                results = content.get("web_results", [])
                if results:
                    snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
                    answer = "\n\n".join(snippets)
                    citations = [
                        {"title": r.get("title"), "url": r.get("url")}
                        for r in results
                        if r.get("url")
                    ]
    elif isinstance(text_obj, dict):
        answer = text_obj.get("answer")
        citations = text_obj.get("citations", [])

    return {
        "answer": answer,
        "backend_uuid": raw.get("backend_uuid"),
        "citations": citations,
    }


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def main() -> None:
    server = Server(APP_NAME)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            client = _client()

            if name == "pplx_search":
                query = arguments["query"]
                mode = arguments.get("mode", "auto") or "auto"
                model = arguments.get("model", "") or None
                thinking = bool(arguments.get("thinking", False))
                sources = arguments.get("sources", "") or None
                follow_up = arguments.get("follow_up", "") or None

                raw = client.search(
                    query=query,
                    mode=mode,
                    model=model,
                    thinking=thinking,
                    sources=sources,
                    follow_up=follow_up,
                )
                result = _extract_answer(raw)
                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

            elif name == "pplx_list_models":
                mode = arguments.get("mode", "") or None
                models = client.list_models(mode=mode)
                return [TextContent(type="text", text=json.dumps(models, indent=2, ensure_ascii=False))]

            elif name == "pplx_list_threads":
                limit = int(arguments.get("limit", 20))
                search_term = arguments.get("search_term", "") or ""
                threads = client.list_threads(limit=limit, search_term=search_term)
                return [TextContent(type="text", text=json.dumps(threads, indent=2, ensure_ascii=False))]

            elif name == "pplx_list_spaces":
                limit = int(arguments.get("limit", 30))
                spaces = client.list_spaces(limit=limit)
                return [TextContent(type="text", text=json.dumps(spaces, indent=2, ensure_ascii=False))]

            elif name == "pplx_search_space":
                uuid = arguments["uuid"]
                query = arguments["query"]
                mode = arguments.get("mode", "auto") or "auto"
                raw = client.search_in_space(uuid=uuid, query=query, mode=mode)
                result = _extract_answer(raw)
                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

            elif name == "pplx_refresh_cookies":
                result = _refresh_cookies()
                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

            elif name == "pplx_validate_session":
                result = client.validate_session()
                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

            else:
                return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        except Exception as e:
            err_msg = str(e)
            if any(k in err_msg.lower() for k in ("session", "auth", "unauthorized", "401", "403", "expired")):
                err_msg += (
                    "\n\n💡 Session appears expired. "
                    "Call the 'pplx_refresh_cookies' tool to regenerate cookies, then retry your request."
                )
            return [TextContent(type="text", text=json.dumps({"error": err_msg}, indent=2, ensure_ascii=False))]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
