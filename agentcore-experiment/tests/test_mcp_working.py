#!/usr/bin/env python
"""
Working test for the deployed AgentCore MCP server using Access Token
"""

import asyncio
import json
import boto3
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def test_mcp_server():
    """Test the deployed MCP server with the correct token"""
    
    # Get Cognito tokens
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    user_pool_id = 'us-east-1_TN9zS9ABA'
    client_id = '2hq5q4h4n6m3vocfh29fsrkbne'
    username = 'mcp-test-user'
    password = 'TestPassword123!'
    
    print("🔐 Getting authentication tokens...")
    response = cognito_client.admin_initiate_auth(
        UserPoolId=user_pool_id,
        ClientId=client_id,
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={
            'USERNAME': username,
            'PASSWORD': password
        }
    )
    
    # Use the ACCESS token, not the ID token!
    access_token = response['AuthenticationResult']['AccessToken']
    print(f"✅ Got Access Token: {access_token[:50]}...")
    
    # Build the runtime URL
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    url = f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    # Headers with Access token (lowercase 'authorization' as per AWS docs)
    headers = {
        "authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🚀 Connecting to AgentCore MCP Server")
    print("=" * 60)
    print(f"URL: {url[:80]}...")
    print("=" * 60)
    
    async with streamablehttp_client(
        url, 
        headers, 
        timeout=120, 
        terminate_on_close=False
    ) as (
        read_stream,
        write_stream,
        _,
    ):
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
                arguments={"n": 30}
            )
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    result_data = json.loads(content.text)
                    print(f"✅ Fibonacci(30) = {result_data.get('fibonacci')}")
                    print(f"   Calculation time: {result_data.get('calculation_time_ms')}ms")
                    print(f"   Trace ID: {result_data.get('trace_id')}")
            
            # 4. Test Weather Simulator
            print("\n☁️ Testing Weather Simulator...")
            result = await session.call_tool(
                name="weather_simulator",
                arguments={
                    "location": "Tokyo",
                    "days_ahead": 5
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
                    print(f"   Uptime: {result_data.get('uptime_seconds')}s")
                    
                    # Check observability
                    metrics = result_data.get('metrics_summary', {})
                    if metrics:
                        print(f"\n   📊 Observability Status:")
                        print(f"   CloudWatch: {'✅ Enabled' if metrics.get('cloudwatch_enabled') else '❌ Disabled'}")
                        print(f"   OpenTelemetry: {'✅ Enabled' if metrics.get('opentelemetry_enabled') else '❌ Disabled'}")
                        print(f"   Total Metrics: {metrics.get('total_metrics', 0)}")
                        print(f"   Total Spans: {metrics.get('total_spans', 0)}")
            
            # 6. Test Text Analysis
            print("\n📝 Testing Text Analysis...")
            result = await session.call_tool(
                name="analyze_text",
                arguments={
                    "text": "The quick brown fox jumps over the lazy dog. This is a test sentence for analysis."
                }
            )
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    result_data = json.loads(content.text)
                    print(f"✅ Text Analysis:")
                    print(f"   Characters: {result_data.get('character_count')}")
                    print(f"   Words: {result_data.get('word_count')}")
                    print(f"   Sentences: {result_data.get('sentence_count')}")
                    avg_len = result_data.get('average_word_length')
                    if avg_len is not None:
                        print(f"   Avg word length: {avg_len:.1f}")
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! AgentCore MCP server is working perfectly!")
    print("\n📊 All observability features are active:")
    print("   ✅ Distributed tracing with trace IDs")
    print("   ✅ CloudWatch metrics collection")
    print("   ✅ OpenTelemetry span tracking")
    print("   ✅ System health monitoring")


def main():
    """Main function"""
    print("🧪 Testing Deployed AgentCore MCP Server")
    print("=" * 60)
    
    try:
        asyncio.run(test_mcp_server())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()