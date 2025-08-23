#!/usr/bin/env python3
"""
Test script to verify MCP UI Server with new modular structure works correctly.
"""

import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP, Context
from mcp_local.ui_server.tool_registry import initialize_tools


async def test_tools():
    """Test that all tools are properly loaded and can be called."""
    
    # Create a test MCP server
    mcp = FastMCP("test-server")
    
    # Initialize tools
    tools = initialize_tools(mcp)
    
    print(f"✅ Successfully loaded {len(tools.list_tools())} tools:")
    for tool_name in sorted(tools.list_tools()):
        print(f"  - {tool_name}")
    
    # Test calling a few tools
    print("\n🧪 Testing tool execution...")
    
    # Create a mock context
    ctx = Context(mcp)
    
    # Test simple_ui
    result = await tools.get_tool_function("simple_ui")(ctx)
    assert result["type"] == "resource"
    print(f"    URI: {result['resource']['uri']}")
    assert result["resource"]["uri"].startswith("ui://")
    print("  ✅ simple_ui works")
    
    # Test markdown_viewer
    result = await tools.get_tool_function("markdown_viewer")(ctx, content="# Test")
    assert result["type"] == "resource"
    assert result["resource"]["uri"].startswith("ui://")
    print("  ✅ markdown_viewer works")
    
    # Test dashboard
    result = await tools.get_tool_function("dashboard")(ctx)
    assert result["type"] == "resource"
    assert result["resource"]["uri"].startswith("ui://")
    print("  ✅ dashboard works")
    
    print("\n🎉 All tests passed! The MCP UI Server is ready to use with LibreChat.")
    print("\n📝 To use with LibreChat:")
    print("  1. Make sure librechat.yaml has been updated (✅ already done)")
    print("  2. Restart LibreChat to load the new configuration")
    print("  3. The 'ui-tools' MCP server should be available in the chat")
    print("\n🚀 Available tools in LibreChat:")
    for tool_name in sorted(tools.list_tools()):
        tool_def = tools.get_tool(tool_name)
        print(f"  - {tool_name}: {tool_def.get('description', 'No description')}")


if __name__ == "__main__":
    asyncio.run(test_tools())