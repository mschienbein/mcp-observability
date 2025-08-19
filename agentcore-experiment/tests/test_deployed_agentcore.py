#!/usr/bin/env python
"""
Test client for the deployed AgentCore MCP server
Uses the official MCP client with streamable-http transport
"""

import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json
import boto3
from botocore.exceptions import ClientError


def get_deployment_info():
    """Get deployment info from Parameter Store and Secrets Manager"""
    ssm = boto3.client('ssm', region_name='us-east-1')
    secrets = boto3.client('secretsmanager', region_name='us-east-1')
    
    # Get Agent ARN from Parameter Store
    try:
        response = ssm.get_parameter(Name='/agentcore/mcp-experiment/agent-arn')
        agent_arn = response['Parameter']['Value']
    except ClientError as e:
        print(f"Error getting agent ARN: {e}")
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    
    # Get Cognito credentials from Secrets Manager
    try:
        response = secrets.get_secret_value(SecretId='agentcore/mcp-experiment/cognito')
        cognito_config = json.loads(response['SecretString'])
    except ClientError as e:
        print(f"Error getting Cognito config: {e}")
        # Fallback values from deployment output
        cognito_config = {
            'user_pool_id': 'us-east-1_TN9zS9ABA',
            'client_id': '2hq5q4h4n6m3vocfh29fsrkbne',
            'username': 'mcp-test-user',
            'password': 'TestPassword123!'
        }
    
    return agent_arn, cognito_config


def get_cognito_token(cognito_config):
    """Get a fresh bearer token from Cognito"""
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        # Authenticate and get tokens
        response = cognito_client.admin_initiate_auth(
            UserPoolId=cognito_config['user_pool_id'],
            ClientId=cognito_config['client_id'],
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': cognito_config['username'],
                'PASSWORD': cognito_config['password']
            }
        )
        
        # Return the ID token (used as bearer token)
        return response['AuthenticationResult']['IdToken']
        
    except ClientError as e:
        print(f"Error getting Cognito token: {e}")
        raise


async def test_agentcore_mcp(url, bearer_token):
    """Test the deployed MCP server on AgentCore"""
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    print("🚀 Testing AgentCore MCP Server")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Token: {bearer_token[:50]}...")
    print("=" * 60)
    
    async with streamablehttp_client(
        url=url,
        headers=headers,
    ) as (read_stream, write_stream, _):
        
        async with ClientSession(read_stream, write_stream) as session:
            
            # 1. Initialize connection
            print("\n📡 Initializing MCP...")
            try:
                init_response = await session.initialize()
                print(f"✅ Initialization successful!")
                print(f"   Server: {init_response.serverInfo.name if init_response.serverInfo else 'Unknown'}")
                print(f"   Version: {init_response.serverInfo.version if init_response.serverInfo else 'Unknown'}")
            except Exception as e:
                print(f"❌ Initialization failed: {e}")
                return
            
            # 2. List available tools
            print("\n📋 Listing tools...")
            try:
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
                    print(f"   • {tool.name}: {tool.description[:60] if tool.description else 'No description'}...")
                    
            except Exception as e:
                print(f"❌ Failed to list tools: {e}")
                return
            
            # 3. Test a tool call - Fibonacci
            print("\n🔢 Testing Fibonacci tool...")
            try:
                from mcp.types import Tool
                
                # Find the fibonacci tool
                fib_tool = next((t for t in tools if t.name == "calculate_fibonacci"), None)
                
                if fib_tool:
                    # Call the tool
                    result = await session.call_tool(
                        name="calculate_fibonacci",
                        arguments={"n": 15}
                    )
                    
                    # Parse the result
                    if result.content and len(result.content) > 0:
                        content = result.content[0]
                        if hasattr(content, 'text'):
                            result_data = json.loads(content.text)
                            print(f"✅ Fibonacci(15) = {result_data.get('fibonacci')}")
                            print(f"   Trace ID: {result_data.get('trace_id')}")
                            print(f"   Session ID: {result_data.get('session_id')}")
                            print(f"   Timestamp: {result_data.get('timestamp')}")
                else:
                    print("⚠️ Fibonacci tool not found")
                    
            except Exception as e:
                print(f"❌ Tool call failed: {e}")
            
            # 4. Test another tool - System Health Check
            print("\n🏥 Testing System Health Check...")
            try:
                health_tool = next((t for t in tools if t.name == "system_health_check"), None)
                
                if health_tool:
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
                            print(f"   Active Traces: {result_data.get('active_traces')}")
                            
                            # Show observability metrics
                            metrics = result_data.get('metrics_summary', {})
                            if metrics:
                                print(f"   CloudWatch: {'✅' if metrics.get('cloudwatch_enabled') else '❌'}")
                                print(f"   OpenTelemetry: {'✅' if metrics.get('opentelemetry_enabled') else '❌'}")
                else:
                    print("⚠️ Health check tool not found")
                    
            except Exception as e:
                print(f"❌ Health check failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ AgentCore MCP test completed!")


def main():
    """Main function to test the deployed AgentCore MCP server"""
    
    # Get deployment information
    print("Getting deployment information...")
    agent_arn, cognito_config = get_deployment_info()
    
    # Build the MCP URL
    region = 'us-east-1'
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    # Get a fresh bearer token
    print("Getting authentication token...")
    bearer_token = get_cognito_token(cognito_config)
    
    # Run the async test
    asyncio.run(test_agentcore_mcp(mcp_url, bearer_token))


if __name__ == "__main__":
    main()