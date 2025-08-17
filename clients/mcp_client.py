"""
Simple MCP streamable HTTP client for local testing.

Usage:
  uv run clients/mcp_client.py tools [--session <id>] [--user <id>]
  uv run clients/mcp_client.py feedback [--rating <n>] [--comment <text>] [--session <id>] [--user <id>]

If uv is not installed, you can run with plain Python (ensure deps are installed):
  python3 clients/mcp_client.py tools

This connects to one of the FastMCP servers:
  tools    -> http://localhost:3002/mcp (calls dummy_long_running_task)
  feedback -> http://localhost:3003/mcp (calls submit_feedback)

Note: The official MCP Python SDK's streamablehttp_client currently doesn't expose a custom
headers parameter. The observability middleware will create a trace even without explicit
session/user headers; when provided, we additionally include those attributes in the trace
via the feedback tool's arguments.
"""

from __future__ import annotations
import sys
import asyncio
from typing import Optional

from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client


TOOLS_URL = "http://localhost:3002/mcp"
FEEDBACK_URL = "http://localhost:3003/mcp"


def parse_args(argv: list[str]) -> dict:
    mode = "tools"
    rating: Optional[float] = None
    comment: str = ""
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    if len(argv) >= 2:
        mode = argv[1]
    i = 2
    while i < len(argv):
        a = argv[i]
        if a in ("--rating", "-r") and i + 1 < len(argv):
            rating = float(argv[i + 1])
            i += 2
        elif a in ("--comment", "-c") and i + 1 < len(argv):
            comment = argv[i + 1]
            i += 2
        elif a in ("--session", "-s") and i + 1 < len(argv):
            session_id = argv[i + 1]
            i += 2
        elif a in ("--user", "-u") and i + 1 < len(argv):
            user_id = argv[i + 1]
            i += 2
        else:
            i += 1
    return {
        "mode": mode,
        "rating": rating,
        "comment": comment,
        "session_id": session_id,
        "user_id": user_id,
    }


async def run_tools(url: str, session_id: Optional[str], user_id: Optional[str]) -> None:
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # Call the demo tool
            result = await session.call_tool("dummy_long_running_task", arguments={})
            # Parse structured content if available
            payload = getattr(result, "structuredContent", None)
            if payload:
                print("Result:", payload)
            else:
                # Fallback: text content
                for c in result.content:
                    if isinstance(c, types.TextContent):
                        print("Result:", c.text)


async def run_feedback(url: str, rating: Optional[float], comment: str,
                       session_id: Optional[str], user_id: Optional[str]) -> None:
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # Prefer direct submit tool; include session/trace hints in args
            args: dict = {}
            if rating is not None:
                args["rating"] = float(rating)
            if comment:
                args["comment"] = comment
            if session_id:
                args["session_id"] = session_id
            # user_id is tracked by middleware via headers; we include it here only for visibility
            if user_id:
                args["user_id"] = user_id  # not used by tool, but printed for debugging

            if not args:
                print("No rating/comment provided; nothing to submit. Use --rating and optional --comment.")
                return

            result = await session.call_tool("submit_feedback", arguments=args)
            payload = getattr(result, "structuredContent", None)
            if payload:
                print("Result:", payload)
            else:
                for c in result.content:
                    if isinstance(c, types.TextContent):
                        print("Result:", c.text)


async def main() -> None:
    cfg = parse_args(sys.argv)
    mode = (cfg["mode"] or "tools").lower()

    if mode.startswith("tool"):
        await run_tools(TOOLS_URL, cfg["session_id"], cfg["user_id"])
    elif mode.startswith("feed"):
        await run_feedback(FEEDBACK_URL, cfg["rating"], cfg["comment"], cfg["session_id"], cfg["user_id"])
    else:
        print("Unknown mode. Use 'tools' or 'feedback'.")


if __name__ == "__main__":
    asyncio.run(main())
