#!/usr/bin/env python
"""
Simple test following AWS documentation exactly
"""

import asyncio
import os
import sys
import boto3
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    # Get Cognito token
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    # Cognito configuration from deployment
    user_pool_id = 'us-east-1_TN9zS9ABA'
    client_id = '2hq5q4h4n6m3vocfh29fsrkbne'
    username = 'mcp-test-user'
    password = 'TestPassword123!'
    
    print("🔐 Getting bearer token...")
    try:
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        bearer_token = response['AuthenticationResult']['IdToken']
        print(f"✅ Got token: {bearer_token[:50]}...")
    except Exception as e:
        print(f"❌ Failed to get token: {e}")
        sys.exit(1)
    
    # Agent ARN from deployment
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    
    # Encode ARN exactly as shown in documentation
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    
    # Build URL exactly as shown in documentation
    mcp_url = f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    # Headers exactly as shown in documentation (lowercase 'authorization')
    headers = {
        "authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n📡 Invoking: {mcp_url[:80]}...")
    print(f"Headers: authorization: Bearer {bearer_token[:30]}...")
    
    try:
        async with streamablehttp_client(
            mcp_url, 
            headers, 
            timeout=120, 
            terminate_on_close=False
        ) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                print("\n✅ Connected! Initializing...")
                await session.initialize()
                print("✅ Initialized!")
                
                print("\n📋 Listing tools...")
                tool_result = await session.list_tools()
                print(f"✅ Tools: {tool_result}")
                
                # Try calling a tool
                if tool_result.tools:
                    print(f"\n🔧 Calling {tool_result.tools[0].name}...")
                    call_result = await session.call_tool(
                        name=tool_result.tools[0].name,
                        arguments={"n": 10} if "fibonacci" in tool_result.tools[0].name else {}
                    )
                    print(f"✅ Result: {call_result}")
                    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Testing AgentCore MCP Server (Simple)")
    print("=" * 60)
    asyncio.run(main())
    print("\n✅ Test completed!")