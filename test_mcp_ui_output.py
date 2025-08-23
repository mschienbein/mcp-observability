#!/usr/bin/env python3
"""
Test script to verify MCP UI server output format
"""

import sys
import json
import subprocess
import asyncio

async def test_mcp_ui():
    """Test the MCP UI server tools directly"""
    sys.path.insert(0, '/Users/mooki/Code/mcp-observability/mcp_local/ui_server')
    
    from mcp_ui_server_debug import show_dashboard, show_form, show_chart, mcp
    from fastmcp import Context
    
    # Create a mock context with the mcp instance
    ctx = Context(mcp)
    
    print("=" * 60)
    print("Testing MCP UI Server Output Format")
    print("=" * 60)
    
    # Test dashboard
    print("\n1. Testing show_dashboard:")
    print("-" * 40)
    dashboard_result = await show_dashboard(ctx)
    print(f"Type: {type(dashboard_result)}")
    print(f"Keys: {list(dashboard_result.keys()) if isinstance(dashboard_result, dict) else 'N/A'}")
    
    if isinstance(dashboard_result, dict):
        print(f"Response type: {dashboard_result.get('type')}")
        if 'resource' in dashboard_result:
            resource = dashboard_result['resource']
            print(f"Resource URI: {resource.get('uri')}")
            print(f"Resource mimeType: {resource.get('mimeType')}")
            print(f"Resource name: {resource.get('name')}")
            print(f"Resource text length: {len(resource.get('text', ''))}")
            
            # Check if HTML contains debug info
            if 'text' in resource and '🔍 Debug Info' in resource['text']:
                print("✅ HTML contains debug info")
            
    # Save to file for inspection
    with open('/tmp/mcp_dashboard_output.json', 'w') as f:
        json.dump(dashboard_result, f, indent=2)
    print(f"\nFull output saved to: /tmp/mcp_dashboard_output.json")
    
    # Test form
    print("\n2. Testing show_form:")
    print("-" * 40)
    form_result = await show_form(ctx)
    print(f"Type: {type(form_result)}")
    print(f"Response type: {form_result.get('type') if isinstance(form_result, dict) else 'N/A'}")
    
    # Test chart
    print("\n3. Testing show_chart:")
    print("-" * 40)
    chart_result = await show_chart(ctx, chart_type="bar")
    print(f"Type: {type(chart_result)}")
    print(f"Response type: {chart_result.get('type') if isinstance(chart_result, dict) else 'N/A'}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed")
    print("Check /tmp/mcp_ui_debug.log for detailed logs")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_mcp_ui())