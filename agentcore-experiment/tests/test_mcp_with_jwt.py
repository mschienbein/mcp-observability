#!/usr/bin/env python
"""
Test the deployed AgentCore MCP server using the MCP client pattern with JWT auth
"""

import asyncio
import json
import boto3
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def get_cognito_token():
    """Get bearer token from Cognito"""
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    # Cognito configuration from deployment
    user_pool_id = 'us-east-1_TN9zS9ABA'
    client_id = '2hq5q4h4n6m3vocfh29fsrkbne'
    username = 'mcp-test-user'
    password = 'TestPassword123!'
    
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
        
        return response['AuthenticationResult']['IdToken']
        
    except Exception as e:
        print(f"Error getting Cognito token: {e}")
        raise


async def test_mcp_server():
    """Test the deployed MCP server"""
    
    # Get fresh JWT token
    print("🔐 Getting JWT token from Cognito...")
    bearer_token = get_cognito_token()
    print(f"✅ Got token: {bearer_token[:50]}...")
    
    # Build the runtime URL
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    url = f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🚀 Connecting to AgentCore MCP Server")
    print("=" * 60)
    print(f"URL: {url[:80]}...")
    print("=" * 60)
    
    try:
        async with streamablehttp_client(
            url=url,
            headers=headers
        ) as (read_stream, write_stream, _):
            
            async with ClientSession(read_stream, write_stream) as session:
                
                # 1. Initialize MCP connection
                print("\n📡 Initializing MCP...")
                init_response = await session.initialize()
                print(f"✅ Initialization successful!")
                
                server_info = init_response.serverInfo
                if server_info:
                    print(f"   Server: {server_info.name}")
                    print(f"   Version: {server_info.version}")
                print(f"   Protocol: {init_response.protocolVersion}")
                
                # 2. List available tools
                print("\n📋 Listing tools...")
                tools = []
                cursor = None
                
                while True:
                    list_tools_response = await session.list_tools(cursor)
                    tools.extend(list_tools_response.tools)
                    
                    if not list_tools_response.nextCursor:
                        break
                    cursor = list_tools_response.nextCursor
                
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   • {tool.name}")
                
                # 3. Test Fibonacci tool
                print("\n🔢 Testing Fibonacci tool...")
                result = await session.call_tool(
                    name="calculate_fibonacci",
                    arguments={"n": 25}
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        result_data = json.loads(content.text)
                        print(f"✅ Fibonacci(25) = {result_data.get('fibonacci')}")
                        print(f"   Calculation time: {result_data.get('calculation_time_ms')}ms")
                        print(f"   Trace ID: {result_data.get('trace_id')}")
                
                # 4. Test Weather Simulator
                print("\n☁️ Testing Weather Simulator...")
                result = await session.call_tool(
                    name="weather_simulator",
                    arguments={
                        "location": "San Francisco",
                        "days_ahead": 3
                    }
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        result_data = json.loads(content.text)
                        print(f"✅ Weather for {result_data.get('location')}:")
                        print(f"   Date: {result_data.get('date')}")
                        print(f"   Temperature: {result_data.get('temperature')}°F")
                        print(f"   Conditions: {result_data.get('conditions')}")
                
                # 5. Test System Health Check
                print("\n🏥 Testing System Health Check...")
                result = await session.call_tool(
                    name="system_health_check",
                    arguments={}
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        result_data = json.loads(content.text)
                        print(f"✅ System Status: {result_data.get('status')}")
                        print(f"   CPU Usage: {result_data.get('cpu_usage')}%")
                        print(f"   Memory Usage: {result_data.get('memory_usage')}%")
                        
                        # Check observability
                        metrics = result_data.get('metrics_summary', {})
                        if metrics:
                            print(f"   CloudWatch: {'✅' if metrics.get('cloudwatch_enabled') else '❌'}")
                            print(f"   OpenTelemetry: {'✅' if metrics.get('opentelemetry_enabled') else '❌'}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ AgentCore MCP test completed!")


def main():
    """Main function"""
    print("🧪 Testing Deployed AgentCore MCP Server")
    print("=" * 60)
    
    # Run the async test
    asyncio.run(test_mcp_server())


if __name__ == "__main__":
    main()