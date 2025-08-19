#!/usr/bin/env python
"""
Test client for AgentCore MCP Gateway using the official pattern
"""

import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json
import boto3


def fetch_cognito_token():
    """Get bearer token from Cognito using test credentials"""
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    # Our Cognito configuration
    user_pool_id = 'us-east-1_TN9zS9ABA'
    client_id = '2hq5q4h4n6m3vocfh29fsrkbne'
    username = 'mcp-test-user'
    password = 'TestPassword123!'
    
    try:
        # Authenticate and get tokens
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Return the ID token (used as bearer token)
        return response['AuthenticationResult']['IdToken']
        
    except Exception as e:
        print(f"Error getting Cognito token: {e}")
        raise


async def execute_mcp(url, headers=None):
    """Execute MCP commands on the gateway"""
    
    headers = {**headers} if headers else {}
    
    print(f"🚀 Connecting to: {url}")
    print(f"🔑 Authorization: {headers.get('Authorization', 'None')[:60]}...")
    print("=" * 80)
    
    async with streamablehttp_client(
        url=url,
        headers=headers,
    ) as (read_stream, write_stream, _):
        
        async with ClientSession(read_stream, write_stream) as session:
            
            # 1. Perform initialization handshake
            print("\n📡 Initializing MCP...")
            try:
                init_response = await session.initialize()
                print(f"✅ MCP Server Initialize successful!")
                print(f"   Server: {init_response.serverInfo.name if init_response.serverInfo else 'Unknown'}")
                print(f"   Version: {init_response.serverInfo.version if init_response.serverInfo else 'Unknown'}")
                print(f"   Protocol: {init_response.protocolVersion}")
            except Exception as e:
                print(f"❌ Initialization failed: {e}")
                return
            
            # 2. List available tools
            print("\n📋 Listing tools...")
            cursor = True
            tools = []
            
            while cursor:
                next_cursor = cursor
                if type(cursor) == bool:
                    next_cursor = None
                    
                try:
                    list_tools_response = await session.list_tools(next_cursor)
                    tools.extend(list_tools_response.tools)
                    cursor = list_tools_response.nextCursor
                except Exception as e:
                    print(f"❌ Failed to list tools: {e}")
                    break
            
            if tools:
                tool_names = [tool.name for tool in tools]
                tool_names_string = "\n   • ".join(tool_names)
                print(f"✅ Found {len(tools)} tools:")
                print(f"   • {tool_names_string}")
            else:
                print("⚠️ No tools found")
                return
            
            # 3. Test calling a tool - Fibonacci
            print("\n🔢 Testing Fibonacci tool...")
            try:
                result = await session.call_tool(
                    name="calculate_fibonacci",
                    arguments={"n": 20}
                )
                
                # Parse the result
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        result_data = json.loads(content.text)
                        print(f"✅ Fibonacci(20) = {result_data.get('fibonacci')}")
                        print(f"   Trace ID: {result_data.get('trace_id')}")
                        print(f"   Timestamp: {result_data.get('timestamp')}")
                        
            except Exception as e:
                print(f"❌ Fibonacci tool failed: {e}")
            
            # 4. Test weather simulator
            print("\n☁️ Testing Weather Simulator...")
            try:
                result = await session.call_tool(
                    name="weather_simulator",
                    arguments={
                        "location": "New York",
                        "days_ahead": 2
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
                        print(f"   Humidity: {result_data.get('humidity')}%")
                        
            except Exception as e:
                print(f"❌ Weather tool failed: {e}")
            
            # 5. Test system health check
            print("\n🏥 Testing System Health Check...")
            try:
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
                        
                        # Check observability status
                        metrics = result_data.get('metrics_summary', {})
                        if metrics:
                            print(f"   CloudWatch Enabled: {'✅' if metrics.get('cloudwatch_enabled') else '❌'}")
                            print(f"   OpenTelemetry Enabled: {'✅' if metrics.get('opentelemetry_enabled') else '❌'}")
                            print(f"   Total Metrics: {metrics.get('total_metrics', 0)}")
                        
            except Exception as e:
                print(f"❌ Health check failed: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Gateway test completed!")


def main():
    """Main function"""
    
    # Use the direct runtime endpoint (not gateway)
    # This is the format used by bedrock-agentcore-starter-toolkit
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    runtime_url = f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    print("🔐 Getting authentication token from Cognito...")
    access_token = fetch_cognito_token()
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Run the async test
    asyncio.run(execute_mcp(url=runtime_url, headers=headers))


if __name__ == "__main__":
    main()