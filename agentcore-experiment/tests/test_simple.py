#!/usr/bin/env python
"""
Simple test for the MCP server using streamable-http
"""

import json
import httpx
import asyncio
from typing import AsyncIterator


async def read_event_stream(response: httpx.Response) -> AsyncIterator[dict]:
    """Parse server-sent events from response"""
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            data = line[6:]  # Remove "data: " prefix
            if data.strip():
                yield json.loads(data)


async def test_mcp_server():
    """Test MCP server with proper streamable-http headers"""
    
    print("🧪 Testing MCP Server with Streamable-HTTP Transport")
    print("=" * 60)
    
    # Create client with proper headers
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "Mcp-Session-Id": "test-session-123"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Initialize
        print("\n📡 Test 1: Initialize Connection")
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",  # Try with full version
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        async with client.stream(
            "POST",
            "http://localhost:8000/mcp",
            json=init_request,
            headers=headers
        ) as response:
            print(f"  Status: {response.status_code}")
            async for event in read_event_stream(response):
                print(f"  Response: {json.dumps(event, indent=2)}")
                if "result" in event:
                    print("  ✅ Initialization successful!")
                break
        
        # Test 2: List Tools
        print("\n📋 Test 2: List Available Tools")
        list_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        async with client.stream(
            "POST",
            "http://localhost:8000/mcp",
            json=list_request,
            headers=headers
        ) as response:
            print(f"  Status: {response.status_code}")
            async for event in read_event_stream(response):
                if "result" in event:
                    tools = event.get("result", {}).get("tools", [])
                    print(f"  Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"    - {tool['name']}")
                    print("  ✅ Tool listing successful!")
                else:
                    print(f"  Response: {json.dumps(event, indent=2)}")
                break
        
        # Test 3: Call Fibonacci Tool
        print("\n🔢 Test 3: Call Fibonacci Tool")
        fib_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "calculate_fibonacci",
                "arguments": {
                    "n": 10
                }
            },
            "id": 3
        }
        
        async with client.stream(
            "POST",
            "http://localhost:8000/mcp",
            json=fib_request,
            headers=headers
        ) as response:
            print(f"  Status: {response.status_code}")
            async for event in read_event_stream(response):
                if "result" in event:
                    content = event.get("result", {}).get("content", [])
                    if content and len(content) > 0:
                        result_text = content[0].get("text", "{}")
                        try:
                            result_data = json.loads(result_text)
                            print(f"  Fibonacci(10) = {result_data.get('fibonacci')}")
                            print(f"  Trace ID: {result_data.get('trace_id')}")
                            print("  ✅ Tool call successful!")
                        except json.JSONDecodeError:
                            print(f"  Raw result: {result_text}")
                else:
                    print(f"  Response: {json.dumps(event, indent=2)}")
                break
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())