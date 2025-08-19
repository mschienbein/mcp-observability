#!/usr/bin/env python3
"""
Test client for the deployed MCP experiment server on AgentCore Runtime
Tests all 5 tools and displays observability data
"""

import asyncio
import boto3
import json
import sys
from boto3.session import Session
from datetime import timedelta

# MCP client imports
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def test_mcp_tools():
    """Test all MCP tools with observability tracking"""
    
    # Get AWS session info
    boto_session = Session()
    region = boto_session.region_name
    
    print(f"Using AWS region: {region}")
    print("="*60)
    
    try:
        # Retrieve stored configuration
        ssm_client = boto3.client('ssm', region_name=region)
        agent_arn_response = ssm_client.get_parameter(Name='/mcp_experiment/runtime/agent_arn')
        agent_arn = agent_arn_response['Parameter']['Value']
        print(f"✓ Retrieved Agent ARN: {agent_arn}")

        secrets_client = boto3.client('secretsmanager', region_name=region)
        response = secrets_client.get_secret_value(SecretId='mcp_experiment/cognito/credentials')
        secret_value = response['SecretString']
        parsed_secret = json.loads(secret_value)
        bearer_token = parsed_secret['bearer_token']
        print("✓ Retrieved bearer token from Secrets Manager")
        
    except Exception as e:
        print(f"❌ Error retrieving credentials: {e}")
        print("\nMake sure you've run deploy_experiment.py first!")
        sys.exit(1)
    
    # Build MCP endpoint URL
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    headers = {
        "authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔗 Connecting to MCP server...")
    print(f"   URL: {mcp_url[:80]}...")
    
    try:
        async with streamablehttp_client(mcp_url, headers, timeout=timedelta(seconds=120), terminate_on_close=False) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                print("\n🔄 Initializing MCP session...")
                await session.initialize()
                print("✅ MCP session initialized")
                
                # List available tools
                print("\n📋 Listing available tools...")
                tool_result = await session.list_tools()
                
                print("\n🛠️  Available MCP Tools:")
                print("="*60)
                for tool in tool_result.tools:
                    print(f"   • {tool.name}")
                    print(f"     {tool.description}")
                print()
                
                # Test each tool
                print("🧪 Testing MCP Tools with Observability")
                print("="*60)
                
                # Test 1: Fibonacci calculation
                try:
                    print("\n1️⃣  Testing calculate_fibonacci(10)...")
                    result = await session.call_tool(
                        name="calculate_fibonacci",
                        arguments={"n": 10}
                    )
                    response = json.loads(result.content[0].text)
                    print(f"   Result: {response['fibonacci']}")
                    print(f"   Trace ID: {response['trace_id']}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
                # Test 2: Text analysis
                try:
                    print("\n2️⃣  Testing analyze_text...")
                    test_text = "This is a sample text for analysis. It contains multiple sentences. The MCP server will analyze it and return statistics about word count, sentence count, and more!"
                    result = await session.call_tool(
                        name="analyze_text",
                        arguments={"text": test_text}
                    )
                    response = json.loads(result.content[0].text)
                    analysis = response['analysis']
                    print(f"   Word count: {analysis['word_count']}")
                    print(f"   Sentence count: {analysis['sentence_count']}")
                    print(f"   Text complexity: {analysis['text_complexity']}")
                    print(f"   Trace ID: {response['trace_id']}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
                # Test 3: Random data generation
                try:
                    print("\n3️⃣  Testing generate_random_data...")
                    result = await session.call_tool(
                        name="generate_random_data",
                        arguments={
                            "data_type": "numbers",
                            "count": 5,
                            "min_value": 1,
                            "max_value": 100
                        }
                    )
                    response = json.loads(result.content[0].text)
                    print(f"   Generated data: {response['data']}")
                    print(f"   Metadata: {response['metadata']}")
                    print(f"   Trace ID: {response['trace_id']}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
                # Test 4: Weather simulation
                try:
                    print("\n4️⃣  Testing weather_simulator...")
                    result = await session.call_tool(
                        name="weather_simulator",
                        arguments={
                            "location": "San Francisco",
                            "days_ahead": 1
                        }
                    )
                    response = json.loads(result.content[0].text)
                    weather = response['weather']
                    print(f"   Location: {weather['location']}")
                    print(f"   Date: {weather['date']}")
                    print(f"   Condition: {weather['condition']}")
                    print(f"   Temperature: {weather['temperature']['current']}°F")
                    print(f"   Trace ID: {response['trace_id']}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
                # Test 5: System health check
                try:
                    print("\n5️⃣  Testing system_health_check...")
                    result = await session.call_tool(
                        name="system_health_check",
                        arguments={}
                    )
                    response = json.loads(result.content[0].text)
                    checks = response['checks']
                    observability = response['observability_summary']
                    print(f"   Status: {response['status']}")
                    print(f"   Memory usage: {checks['memory_usage']}%")
                    print(f"   CPU usage: {checks['cpu_usage']}%")
                    print(f"   Active traces: {checks['active_traces']}")
                    print(f"   Total metrics: {checks['total_metrics']}")
                    print(f"   Recent traces: {len(observability['recent_traces'])}")
                    print(f"   Trace ID: {response['trace_id']}")
                    
                    # Show recent trace summary
                    if observability['recent_traces']:
                        print("\n   📊 Recent Trace Summary:")
                        for trace in observability['recent_traces'][-3:]:
                            print(f"      • {trace['tool']}: {trace['status']} ({trace['duration_ms']:.2f}ms)")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
                print("\n" + "="*60)
                print("✅ All tests completed successfully!")
                print("\n📈 Observability Notes:")
                print("   • Each tool invocation generates a unique trace ID")
                print("   • Traces include spans for detailed execution tracking")
                print("   • Metrics are collected for each operation")
                print("   • System health check shows aggregated observability data")
                print("   • Check CloudWatch logs for detailed observability output")
                
    except Exception as e:
        print(f"\n❌ Error connecting to MCP server: {e}")
        print("\nTroubleshooting:")
        print("   1. Ensure the server is deployed and READY")
        print("   2. Check the bearer token is still valid")
        print("   3. Verify network connectivity to AgentCore endpoint")
        sys.exit(1)

async def main():
    """Main entry point"""
    print("="*60)
    print("🚀 MCP Experiment Server Test Client")
    print("="*60)
    print("\nThis client tests all 5 tools in the deployed MCP server")
    print("and displays observability data from each invocation.\n")
    
    await test_mcp_tools()

if __name__ == "__main__":
    asyncio.run(main())