#!/usr/bin/env python
"""
Test invoking the AgentCore runtime using AWS SDK
"""

import boto3
import json
from datetime import datetime


def invoke_agentcore_runtime():
    """Invoke the AgentCore runtime directly using AWS SDK"""
    
    client = boto3.client('bedrock-agentcore', region_name='us-east-1')
    
    agent_runtime_id = "mcp_experiment_agentcore-r1D3AT7jmJ"
    
    print(f"🚀 Invoking AgentCore Runtime: {agent_runtime_id}")
    print("=" * 80)
    
    # Try to get a workload access token first
    try:
        print("\n🔑 Getting workload access token...")
        token_response = client.get_workload_access_token(
            agentRuntimeId=agent_runtime_id,
            agentRuntimeEndpointName="DEFAULT"
        )
        
        access_token = token_response.get('accessToken')
        print(f"✅ Got access token: {access_token[:50]}...")
        
    except Exception as e:
        print(f"❌ Could not get workload token: {e}")
        access_token = None
    
    # Try to invoke the runtime
    try:
        print("\n📡 Invoking runtime...")
        
        # MCP initialize request
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "capabilities": {}
            },
            "id": 1
        }
        
        response = client.invoke_agent_runtime(
            agentRuntimeId=agent_runtime_id,
            agentRuntimeEndpointName="DEFAULT",
            inputText=json.dumps(mcp_request)
        )
        
        # Parse response
        if 'body' in response:
            body = response['body'].read()
            result = json.loads(body) if body else {}
            print(f"✅ Response received:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"❌ Failed to invoke runtime: {e}")
        
        # Try a different approach - list sessions
        try:
            print("\n📋 Listing sessions...")
            sessions = client.list_sessions(
                agentRuntimeId=agent_runtime_id,
                agentRuntimeEndpointName="DEFAULT",
                maxResults=5
            )
            print(f"Sessions: {sessions}")
        except Exception as e2:
            print(f"❌ Could not list sessions: {e2}")


def check_runtime_status():
    """Check the runtime status using control plane"""
    
    control_client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
    
    agent_runtime_id = "mcp_experiment_agentcore-r1D3AT7jmJ"
    
    try:
        print("\n🔍 Checking runtime status...")
        runtime = control_client.get_agent_runtime(
            agentRuntimeId=agent_runtime_id
        )
        
        print(f"✅ Runtime Status: {runtime.get('status')}")
        print(f"   Name: {runtime.get('agentRuntimeName')}")
        print(f"   Version: {runtime.get('agentRuntimeVersion')}")
        print(f"   Protocol: {runtime.get('protocolConfiguration', {}).get('serverProtocol')}")
        
        # Check endpoint
        endpoints = control_client.list_agent_runtime_endpoints(
            agentRuntimeId=agent_runtime_id
        )
        
        for endpoint in endpoints.get('runtimeEndpoints', []):
            print(f"\n   Endpoint: {endpoint.get('name')}")
            print(f"   Status: {endpoint.get('status')}")
            print(f"   Version: {endpoint.get('liveVersion')}")
            
    except Exception as e:
        print(f"❌ Could not get runtime status: {e}")


def main():
    """Main function"""
    
    print("🧪 Testing AgentCore Runtime Invocation")
    print("=" * 80)
    
    # Check runtime status first
    check_runtime_status()
    
    # Try to invoke the runtime
    invoke_agentcore_runtime()
    
    print("\n" + "=" * 80)
    print("✅ Test completed!")


if __name__ == "__main__":
    main()