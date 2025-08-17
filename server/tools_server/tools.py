from __future__ import annotations
import time, random
from fastmcp import FastMCP
from langfuse import get_client


def register_dummy_tools(mcp: FastMCP):
    @mcp.tool(
        name="dummy_long_running_task",
        description="Sleeps briefly, returns a random result; intended to produce trace data."
    )
    async def dummy_long_running_task():
        lf = get_client()
        with lf.start_span(name="dummy:work"):
            t = random.uniform(0.2, 1.0)
            time.sleep(t)
            result = {"slept_seconds": round(t, 2), "value": random.randint(1, 100)}
            return result
