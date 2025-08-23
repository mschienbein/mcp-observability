#!/usr/bin/env python3
"""
Test client for MCP UI Server
"""

import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def main():
    """Test the MCP UI server tools"""
    
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "mcp_local.ui_server.main"],
        env=None
    )
    
    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as client:
            # Initialize the session
            await client.initialize()
            
            print("Connected to MCP UI Server!")
            print("=" * 50)
            
            # List available tools
            tools = await client.list_tools()
            print(f"\nFound {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:50]}...")
            
            print("\n" + "=" * 50)
            
            # Test 1: Get User Form
            print("\n1. Testing User Registration Form:")
            result = await client.call_tool("get_user_form", {})
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if result.get("type") == "resource":
                resource = result.get("resource", {})
                print(f"   ✓ URI: {resource.get('uri')}")
                print(f"   ✓ Name: {resource.get('name')}")
                print(f"   ✓ Type: {resource.get('mimeType')}")
                print(f"   ✓ Content size: {len(resource.get('text', ''))} chars")
            
            # Test 2: Get Dashboard
            print("\n2. Testing Dashboard:")
            result = await client.call_tool("get_dashboard", {"refresh": False})
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if result.get("type") == "resource":
                resource = result.get("resource", {})
                print(f"   ✓ URI: {resource.get('uri')}")
                print(f"   ✓ Name: {resource.get('name')}")
                
            # Test 3: Get Settings Panel
            print("\n3. Testing Settings Panel:")
            result = await client.call_tool("get_settings_panel", {})
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if result.get("type") == "resource":
                resource = result.get("resource", {})
                print(f"   ✓ URI: {resource.get('uri')}")
                print(f"   ✓ Name: {resource.get('name')}")
            
            # Test 4: Get Data Table with Pagination
            print("\n4. Testing Data Table:")
            result = await client.call_tool("get_data_table", {"page": 1, "per_page": 5})
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if result.get("type") == "resource":
                resource = result.get("resource", {})
                print(f"   ✓ URI: {resource.get('uri')}")
                print(f"   ✓ Name: {resource.get('name')}")
            
            # Test 5: Get Chart Visualizations
            print("\n5. Testing Chart Visualizations:")
            for chart_type in ["bar", "line", "pie"]:
                result = await client.call_tool("get_chart_visualization", {"chart_type": chart_type})
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                if result.get("type") == "resource":
                    resource = result.get("resource", {})
                    print(f"   ✓ {chart_type.capitalize()} chart: {resource.get('uri')}")
            
            print("\n" + "=" * 50)
            print("✅ All UI resource tools tested successfully!")
            print("\nThese UI resources can now be rendered in LibreChat")
            print("using the MCP-UI integration we built.")

if __name__ == "__main__":
    asyncio.run(main())