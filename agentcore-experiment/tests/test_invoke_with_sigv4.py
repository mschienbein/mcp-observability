#!/usr/bin/env python
"""
Test invoking AgentCore Runtime using AWS SigV4 authentication
"""

import boto3
import json
import requests
from requests_aws4auth import AWS4Auth
from botocore.exceptions import ClientError


def get_aws_auth():
    """Get AWS SigV4 authentication"""
    session = boto3.Session()
    credentials = session.get_credentials()
    region = session.region_name or 'us-east-1'
    
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        'bedrock-agentcore',
        session_token=credentials.token
    )
    return auth, region


def invoke_with_sigv4():
    """Invoke the AgentCore runtime using SigV4 authentication"""
    
    auth, region = get_aws_auth()
    
    # Agent runtime details
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    
    # Build the runtime endpoint URL
    url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    print(f"🚀 Testing AgentCore Runtime with SigV4")
    print("=" * 80)
    print(f"URL: {url}")
    print("=" * 80)
    
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
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        print("\n📡 Sending MCP initialize request...")
        response = requests.post(
            url,
            auth=auth,
            headers=headers,
            json=mcp_request,
            stream=True
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\n✅ Success! Response:")
            
            # Handle streaming response
            if 'text/event-stream' in response.headers.get('content-type', ''):
                print("Streaming response detected:")
                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        print(f"  {decoded}")
            else:
                # Regular JSON response
                result = response.json()
                print(json.dumps(result, indent=2))
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")


def test_bedrock_agentcore_api():
    """Test using the bedrock-agentcore API directly"""
    
    client = boto3.client('bedrock-agentcore', region_name='us-east-1')
    
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    
    print("\n🔍 Testing bedrock-agentcore API...")
    print("=" * 80)
    
    try:
        # Try invoke_agent_runtime with correct parameters
        print("Attempting invoke_agent_runtime...")
        
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
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps(mcp_request),
            contentType="application/json",
            accept="application/json"
        )
        
        print(f"✅ Response: {response}")
        
        if 'body' in response:
            body = response['body'].read()
            if body:
                result = json.loads(body)
                print(f"Body: {json.dumps(result, indent=2)}")
                
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ API call failed: {error_code} - {error_msg}")
        
        if error_code == 'AccessDeniedException':
            print("\n💡 This agent requires JWT authentication, not SigV4")


def main():
    """Main function"""
    
    print("🧪 Testing AgentCore Runtime Access Methods")
    print("=" * 80)
    
    # First check if requests-aws4auth is installed
    try:
        import requests_aws4auth
        print("✅ requests-aws4auth is installed")
        
        # Test SigV4 authentication
        invoke_with_sigv4()
        
    except ImportError:
        print("⚠️ requests-aws4auth not installed")
        print("Installing: pip install requests-aws4auth")
    
    # Test bedrock-agentcore API
    test_bedrock_agentcore_api()
    
    print("\n" + "=" * 80)
    print("✅ Test completed!")


if __name__ == "__main__":
    main()