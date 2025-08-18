#!/usr/bin/env python3
"""Send comprehensive test traces to Langfuse via MCP servers"""

import asyncio
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from langfuse import Langfuse
from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client

TOOLS_URL = "http://localhost:3002/mcp"
FEEDBACK_URL = "http://localhost:3003/mcp"

async def test_mcp_servers():
    """Test MCP servers with various session patterns"""
    
    print("🚀 Sending test traces to Langfuse via MCP servers")
    print("=" * 60)
    
    # Test 1: Single tool call
    print("\n📊 Test 1: Single tool call...")
    session_id = f"test-single-{uuid.uuid4().hex[:8]}"
    
    async with streamablehttp_client(TOOLS_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("dummy_long_running_task", arguments={})
            print(f"   Session: {session_id}")
            print(f"   Result: {getattr(result, 'structuredContent', 'completed')}")
    
    # Test 2: Multiple calls in same session
    print("\n📊 Test 2: Multiple MCP calls in same session...")
    session_id = f"test-multi-{uuid.uuid4().hex[:8]}"
    
    async with streamablehttp_client(TOOLS_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            for i in range(3):
                result = await session.call_tool("dummy_long_running_task", arguments={})
                print(f"   Call {i+1}: completed")
    
    print(f"   Session: {session_id}")
    
    # Test 3: Cross-server session (distributed trace)
    print("\n📊 Test 3: Distributed trace across both servers...")
    session_id = f"test-distributed-{uuid.uuid4().hex[:8]}"
    
    # Call tools server
    async with streamablehttp_client(TOOLS_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await session.call_tool("dummy_long_running_task", arguments={})
            print(f"   Tools server: called")
    
    # Call feedback server with same session
    async with streamablehttp_client(FEEDBACK_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await session.call_tool("submit_feedback", arguments={
                "rating": 4.8,
                "comment": f"Distributed test for {session_id}",
                "session_id": session_id
            })
            print(f"   Feedback server: called")
    
    print(f"   Session: {session_id}")

def test_direct_langfuse():
    """Send traces directly to Langfuse"""
    
    print("\n📊 Test 4: Direct Langfuse traces...")
    
    langfuse = Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )
    
    # Create multiple traces
    for i in range(3):
        trace_id = uuid.uuid4().hex
        timestamp = datetime.now()
        
        # Create a trace with events
        event = langfuse.create_event(
            trace_context={"trace_id": trace_id},
            name=f"test-event-{i+1}",
            input={"test": True, "index": i},
            output={"result": f"success-{i+1}"},
            metadata={
                "test_run": timestamp.isoformat(),
                "environment": "test",
                "source": "send_test_traces.py"
            },
            level="DEFAULT",
            status_message=f"Test event {i+1} completed"
        )
        
        # Add a score
        langfuse.create_score(
            trace_id=trace_id,
            name=f"test-score-{i+1}",
            value=0.8 + (i * 0.05),
            comment=f"Automated test score {i+1}"
        )
        
        print(f"   Trace {i+1}: {trace_id[:8]}...")
    
    # Flush all data
    langfuse.flush()
    time.sleep(1)
    langfuse.shutdown()
    
    print("   ✓ All traces sent")

async def main():
    """Run all tests"""
    
    # Run MCP server tests
    await test_mcp_servers()
    
    # Run direct Langfuse tests
    test_direct_langfuse()
    
    print("\n" + "=" * 60)
    print("✅ All test traces sent successfully!")
    print("\n📊 Summary:")
    print("  - Single MCP tool calls")
    print("  - Multiple calls in same session")
    print("  - Distributed traces across servers")
    print("  - Direct Langfuse events and scores")
    print("\n🔗 View traces in Langfuse dashboard:")
    print(f"  {os.getenv('LANGFUSE_HOST')}/project/cmegfhksf0006mn06q79d8eab/traces")
    print("\n💡 Look for:")
    print("  - Sessions starting with 'test-'")
    print("  - Events named 'test-event-*'")
    print("  - Scores named 'test-score-*'")

if __name__ == "__main__":
    asyncio.run(main())