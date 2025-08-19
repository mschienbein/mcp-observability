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
        # Use observe decorator or manual event creation for tracing
        event = lf.create_event(
            name="dummy:work",
            input={"task": "dummy_long_running_task"},
            level="DEFAULT"
        )
        
        t = random.uniform(0.2, 1.0)
        time.sleep(t)
        result = {"slept_seconds": round(t, 2), "value": random.randint(1, 100)}
        
        # Update event with output
        if event:
            lf.create_event(
                name="dummy:complete",
                output=result,
                metadata={"duration_ms": int(t * 1000)},
                level="DEFAULT"
            )
        
        return result
