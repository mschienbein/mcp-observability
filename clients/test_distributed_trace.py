#!/usr/bin/env python3
"""Test distributed tracing across MCP servers"""

import asyncio
import sys
import uuid
from typing import Optional
from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client
import os
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

TOOLS_URL = "http://localhost:3002/mcp"
FEEDBACK_URL = "http://localhost:3003/mcp"

async def test_distributed_trace():
    """
    Test distributed tracing:
    1. Call tools server with a session ID
    2. Call feedback server with the same session ID
    3. Both should be linked in the same trace
    """
    
    # Generate a unique session ID for this test
    session_id = f"dist-trace-{uuid.uuid4().hex[:8]}"
    user_id = "test-user-distributed"
    
    print(f"🔗 Testing distributed tracing with session: {session_id}")
    print("=" * 60)
    
    # Step 1: Call tools server
    print("\n📊 Step 1: Calling tools server...")
    async with streamablehttp_client(TOOLS_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Call the dummy tool
            result = await session.call_tool("dummy_long_running_task", arguments={})
            
            # Extract result
            for c in result.content:
                if isinstance(c, types.TextContent):
                    print(f"   Tool result: {c.text}")
            
            payload = getattr(result, "structuredContent", None)
            if payload:
                print(f"   Tool result: {payload}")
    
    print("   ✓ Tools server call completed")
    
    # Step 2: Call feedback server with same session
    print("\n📊 Step 2: Calling feedback server with same session...")
    async with streamablehttp_client(FEEDBACK_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Submit feedback
            result = await session.call_tool(
                "submit_feedback", 
                arguments={
                    "rating": 5.0,
                    "comment": f"Distributed trace test for session {session_id}",
                    "session_id": session_id
                }
            )
            
            # Extract result
            for c in result.content:
                if isinstance(c, types.TextContent):
                    print(f"   Feedback result: {c.text}")
            
            payload = getattr(result, "structuredContent", None)
            if payload:
                print(f"   Feedback result: {payload}")
    
    print("   ✓ Feedback server call completed")
    
    print("\n" + "=" * 60)
    print("✅ Distributed trace test completed!")
    print(f"\n🔍 Both calls should appear in Langfuse under session: {session_id}")
    print(f"   Check: {os.getenv('LANGFUSE_HOST')}/project/cmegfhksf0006mn06q79d8eab/sessions")
    print(f"\n💡 The middleware should have:")
    print("   1. Created spans for each MCP endpoint")
    print("   2. Linked them via the session_id")
    print("   3. Stored trace IDs in Redis/memory for correlation")

if __name__ == "__main__":
    asyncio.run(test_distributed_trace())