#!/usr/bin/env python
"""
Test direct HTTP request to AgentCore Runtime to debug the 403 error
"""

import requests
import json
import boto3


def test_direct_http():
    """Test with direct HTTP request to see exact error"""
    
    # Get Cognito token
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    user_pool_id = 'us-east-1_TN9zS9ABA'
    client_id = '2hq5q4h4n6m3vocfh29fsrkbne'
    username = 'mcp-test-user'
    password = 'TestPassword123!'
    
    print("🔐 Getting bearer token...")
    response = cognito_client.admin_initiate_auth(
        UserPoolId=user_pool_id,
        ClientId=client_id,
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={
            'USERNAME': username,
            'PASSWORD': password
        }
    )
    
    id_token = response['AuthenticationResult']['IdToken']
    access_token = response['AuthenticationResult']['AccessToken']
    
    print(f"✅ Got ID token: {id_token[:50]}...")
    print(f"✅ Got Access token: {access_token[:50]}...")
    
    # Build URL
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/mcp_experiment_agentcore-r1D3AT7jmJ"
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    url = f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    # MCP request
    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0.0",
            "capabilities": {}
        },
        "id": 1
    }
    
    print(f"\n📡 Testing different authorization formats...")
    print(f"URL: {url[:80]}...")
    print("=" * 60)
    
    # Test 1: With ID token and lowercase authorization
    print("\n1. Testing with ID token (lowercase 'authorization'):")
    headers = {
        "authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text[:200]}")
    
    # Test 2: With Access token
    print("\n2. Testing with Access token:")
    headers = {
        "authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text[:200]}")
    
    # Test 3: With uppercase Authorization
    print("\n3. Testing with ID token (uppercase 'Authorization'):")
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text[:200]}")
    
    # Test 4: With additional MCP headers
    print("\n4. Testing with MCP session headers:")
    headers = {
        "authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": "test-session-123",
        "X-MCP-Session-Id": "test-session-123"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ SUCCESS!")
        print(f"   Response: {response.text[:500]}")
    else:
        print(f"   Error: {response.text[:200]}")
    
    # Decode the JWT to check its contents
    print("\n🔍 JWT Token Analysis:")
    import base64
    
    # Split the token and decode the payload
    parts = id_token.split('.')
    if len(parts) >= 2:
        # Add padding if needed
        payload_part = parts[1]
        payload_part += '=' * (4 - len(payload_part) % 4)
        
        try:
            decoded = base64.urlsafe_b64decode(payload_part)
            jwt_payload = json.loads(decoded)
            
            print("   Token claims:")
            print(f"   - aud (audience): {jwt_payload.get('aud')}")
            print(f"   - client_id: {jwt_payload.get('client_id')}")
            print(f"   - iss (issuer): {jwt_payload.get('iss')}")
            print(f"   - token_use: {jwt_payload.get('token_use')}")
            print(f"   - auth_time: {jwt_payload.get('auth_time')}")
            print(f"   - exp: {jwt_payload.get('exp')}")
            
        except Exception as e:
            print(f"   Could not decode JWT: {e}")


def main():
    """Main function"""
    print("🧪 Direct HTTP Testing for AgentCore Runtime")
    print("=" * 60)
    
    test_direct_http()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")


if __name__ == "__main__":
    main()