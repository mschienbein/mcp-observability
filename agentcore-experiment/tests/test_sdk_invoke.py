#!/usr/bin/env python
"""
Test using AWS SDK to invoke AgentCore Runtime
"""

import boto3
import json
from botocore.exceptions import ClientError


def test_invoke():
    """Test invoking the runtime with AWS SDK"""
    
    client = boto3.client('bedrock-agentcore', region_name='us-east-1')
    
    # Get Cognito token first
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
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
        return
    
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    
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
    
    print(f"\n📡 Invoking runtime via SDK...")
    print(f"Agent ARN: {agent_arn}")
    
    try:
        # Use the correct API parameters
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps(mcp_request),
            contentType="application/json",
            accept="application/json, text/event-stream",
            # Add the bearer token in the SDK call
            runtimeUserId=username,
            mcpSessionId="test-session-123",
            # The SDK should handle the JWT auth header internally
            # based on the runtime's authorizer configuration
        )
        
        print(f"✅ Response Status: {response['ResponseMetadata']['HTTPStatusCode']}")
        
        if 'body' in response:
            body = response['body'].read()
            if body:
                result = json.loads(body.decode('utf-8'))
                print(f"✅ Response Body:")
                print(json.dumps(result, indent=2))
        else:
            print(f"Full Response: {response}")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ SDK call failed: {error_code}")
        print(f"   Message: {error_msg}")
        
        # Try to get more details
        if error_code == 'RuntimeClientError':
            print("\n💡 RuntimeClientError details:")
            print("   - Check if the JWT token is valid")
            print("   - Verify the Cognito user pool configuration")
            print("   - Ensure the agent's authorizer configuration matches")


def main():
    """Main function"""
    print("🧪 Testing AgentCore Runtime via AWS SDK")
    print("=" * 60)
    
    test_invoke()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")


if __name__ == "__main__":
    main()