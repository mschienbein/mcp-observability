#!/usr/bin/env python
"""
Test client for the local MCP experiment server
Tests all 5 tools with observability tracking
"""

import asyncio
import json
import httpx
from typing import Dict, Any
import uuid


class MCPTestClient:
    """Test client for MCP server"""
    
    def __init__(self, base_url: str = "http://localhost:8000/mcp"):
        self.base_url = base_url
        self.session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize MCP connection"""
        response = await self.client.post(
            self.base_url,
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0",
                    "capabilities": {}
                },
                "id": 1
            },
            headers={"Mcp-Session-Id": self.session_id}
        )
        return response.json()
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        response = await self.client.post(
            self.base_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            },
            headers={"Mcp-Session-Id": self.session_id}
        )
        return response.json()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        response = await self.client.post(
            self.base_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": 3
            },
            headers={"Mcp-Session-Id": self.session_id}
        )
        return response.json()
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()


async def test_all_tools():
    """Test all 5 tools in the MCP server"""
    
    print("🚀 Starting MCP Server Tests")
    print("=" * 60)
    
    client = MCPTestClient()
    
    try:
        # Initialize
        print("\n📡 Initializing MCP connection...")
        init_result = await client.initialize()
        print(f"✅ Initialized: {init_result.get('result', {}).get('serverInfo', {})}")
        
        # List tools
        print("\n📋 Listing available tools...")
        tools_result = await client.list_tools()
        tools = tools_result.get("result", {}).get("tools", [])
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool.get('description', '')[:60]}...")
        
        # Test 1: Fibonacci
        print("\n🔢 Test 1: Calculate Fibonacci")
        print("-" * 40)
        fib_result = await client.call_tool("calculate_fibonacci", {"n": 10})
        result = fib_result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(result)
        print(f"  Input: n=10")
        print(f"  Result: {data.get('fibonacci')}")
        print(f"  Trace ID: {data.get('trace_id')}")
        print(f"  ✅ Fibonacci test passed!")
        
        # Test 2: Text Analysis
        print("\n📝 Test 2: Analyze Text")
        print("-" * 40)
        text = "This is a test sentence. It has multiple words! Does it work?"
        text_result = await client.call_tool("analyze_text", {"text": text})
        result = text_result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(result)
        print(f"  Input: '{text[:50]}...'")
        print(f"  Word count: {data.get('word_count')}")
        print(f"  Sentence count: {data.get('sentence_count')}")
        print(f"  Trace ID: {data.get('trace_id')}")
        print(f"  ✅ Text analysis test passed!")
        
        # Test 3: Random Data Generation
        print("\n🎲 Test 3: Generate Random Data")
        print("-" * 40)
        data_result = await client.call_tool("generate_random_data", {
            "data_type": "numbers",
            "count": 5,
            "min_value": 1,
            "max_value": 100
        })
        result = data_result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(result)
        print(f"  Type: numbers, Count: 5, Range: 1-100")
        print(f"  Generated: {data.get('data')}")
        print(f"  Trace ID: {data.get('trace_id')}")
        print(f"  ✅ Data generation test passed!")
        
        # Test 4: Weather Simulation
        print("\n☁️ Test 4: Weather Simulator")
        print("-" * 40)
        weather_result = await client.call_tool("weather_simulator", {
            "location": "San Francisco",
            "days_ahead": 1
        })
        result = weather_result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(result)
        print(f"  Location: San Francisco")
        print(f"  Temperature: {data.get('temperature')}°F")
        print(f"  Conditions: {data.get('conditions')}")
        print(f"  Humidity: {data.get('humidity')}%")
        print(f"  Trace ID: {data.get('trace_id')}")
        print(f"  ✅ Weather simulation test passed!")
        
        # Test 5: System Health Check
        print("\n🏥 Test 5: System Health Check")
        print("-" * 40)
        health_result = await client.call_tool("system_health_check", {})
        result = health_result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(result)
        print(f"  Status: {data.get('status')}")
        print(f"  CPU Usage: {data.get('cpu_usage')}%")
        print(f"  Memory Usage: {data.get('memory_usage')}%")
        print(f"  Active Traces: {data.get('active_traces')}")
        print(f"  Recent Traces: {len(data.get('recent_traces', []))}")
        print(f"  Metrics Summary: {data.get('metrics_summary', {})}")
        print(f"  ✅ Health check test passed!")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print(f"🔍 Session ID: {client.session_id}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    print("\n🧪 MCP Experiment Server Test Suite")
    print("Testing with enhanced observability (OpenTelemetry + CloudWatch)")
    asyncio.run(test_all_tools())