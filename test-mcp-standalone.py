#!/usr/bin/env python3
"""Test MCP UI Server standalone to verify it works"""

import json
import subprocess
import sys

def test_mcp_server():
    """Test the MCP server with initialization request"""
    
    # Start the MCP server process
    process = subprocess.Popen(
        [
            "/Users/mooki/Code/mcp-observability/.venv/bin/python",
            "/Users/mooki/Code/mcp-observability/mcp_local/ui_server/mcp_ui_server_fixed.py"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            "PYTHONPATH": "/Users/mooki/Code/mcp-observability",
            "PYTHONUNBUFFERED": "1"
        },
        cwd="/Users/mooki/Code/mcp-observability"
    )
    
    # Send initialization request
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {
                    "listChanged": True
                },
                "sampling": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    }
    
    # Send request
    request_str = json.dumps(init_request) + "\n"
    print(f"Sending: {request_str}")
    
    try:
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print(f"Response: {response}")
        
        if response:
            resp_json = json.loads(response)
            print(f"Parsed response: {json.dumps(resp_json, indent=2)}")
            
            # Test list tools
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }
            
            request_str = json.dumps(tools_request) + "\n"
            print(f"\nSending tools/list: {request_str}")
            process.stdin.write(request_str)
            process.stdin.flush()
            
            response = process.stdout.readline()
            print(f"Tools response: {response}")
            
            if response:
                tools_json = json.loads(response)
                print(f"Available tools: {json.dumps(tools_json, indent=2)}")
        
        # Clean up
        process.terminate()
        
    except Exception as e:
        print(f"Error: {e}")
        # Check stderr
        stderr = process.stderr.read()
        if stderr:
            print(f"Stderr: {stderr}")
        process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    test_mcp_server()