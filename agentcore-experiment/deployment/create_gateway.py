#!/usr/bin/env python3
"""
Create a Gateway for the deployed AgentCore MCP Runtime
Based on AWS documentation for MCP servers
"""

import boto3
import json
import sys
from pathlib import Path


def create_gateway():
    """Create a Gateway for the MCP runtime"""
    
    client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
    
    # Our runtime details
    agent_runtime_id = "mcp_experiment_agentcore-r1D3AT7jmJ"
    agent_arn = f"arn:aws:bedrock-agentcore:us-east-1:032360566970:runtime/{agent_runtime_id}"
    
    # Cognito configuration
    user_pool_id = 'us-east-1_TN9zS9ABA'
    client_id = '2hq5q4h4n6m3vocfh29fsrkbne'
    discovery_url = f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    
    print("🚀 Creating Gateway for AgentCore MCP Runtime")
    print("=" * 60)
    print(f"Runtime ID: {agent_runtime_id}")
    print(f"Runtime ARN: {agent_arn}")
    
    # Gateway configuration
    gateway_config = {
        "gatewayName": "mcp-experiment-gateway",
        "protocol": "MCP",
        "authorizerConfiguration": {
            "customJWTAuthorizer": {
                "discoveryUrl": discovery_url,
                "allowedClients": [client_id]
            }
        },
        "targets": [
            {
                "targetArn": agent_arn,
                "targetDescription": "MCP Experiment Server with observability"
            }
        ]
    }
    
    try:
        print("\n📝 Creating Gateway...")
        response = client.create_gateway(**gateway_config)
        
        gateway_arn = response.get('gatewayArn')
        gateway_id = response.get('gatewayId')
        gateway_url = response.get('gatewayUrl')
        
        print(f"✅ Gateway created successfully!")
        print(f"   Gateway ARN: {gateway_arn}")
        print(f"   Gateway ID: {gateway_id}")
        print(f"   Gateway URL: {gateway_url}")
        
        # Store gateway info
        gateway_info = {
            'gateway_arn': gateway_arn,
            'gateway_id': gateway_id,
            'gateway_url': gateway_url,
            'runtime_id': agent_runtime_id,
            'runtime_arn': agent_arn,
            'cognito': {
                'user_pool_id': user_pool_id,
                'client_id': client_id,
                'discovery_url': discovery_url
            }
        }
        
        # Save to file for later use
        output_file = Path(__file__).parent / 'gateway_info.json'
        with open(output_file, 'w') as f:
            json.dump(gateway_info, f, indent=2)
        print(f"\n💾 Gateway info saved to: {output_file}")
        
        return gateway_info
        
    except client.exceptions.ValidationException as e:
        print(f"❌ Validation error: {e}")
        print("\n💡 Checking if Gateway already exists...")
        
        # List existing gateways
        try:
            gateways = client.list_gateways()
            for gw in gateways.get('gateways', []):
                if 'mcp-experiment' in gw.get('gatewayName', '').lower():
                    print(f"Found existing gateway: {gw.get('gatewayName')}")
                    print(f"  ARN: {gw.get('gatewayArn')}")
                    print(f"  URL: {gw.get('gatewayUrl')}")
                    return gw
        except Exception as e2:
            print(f"Could not list gateways: {e2}")
            
    except Exception as e:
        print(f"❌ Failed to create Gateway: {e}")
        return None


def test_gateway(gateway_info):
    """Test the Gateway with a simple request"""
    
    if not gateway_info or 'gateway_url' not in gateway_info:
        print("⚠️ No gateway URL to test")
        return
    
    import requests
    
    # Get a fresh Cognito token
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        response = cognito_client.admin_initiate_auth(
            UserPoolId='us-east-1_TN9zS9ABA',
            ClientId='2hq5q4h4n6m3vocfh29fsrkbne',
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': 'mcp-test-user',
                'PASSWORD': 'TestPassword123!'
            }
        )
        bearer_token = response['AuthenticationResult']['IdToken']
        
        print(f"\n🧪 Testing Gateway...")
        print(f"URL: {gateway_info['gateway_url']}")
        
        # Test with simple MCP request
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "capabilities": {}
            },
            "id": 1
        }
        
        response = requests.post(
            gateway_info['gateway_url'],
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Gateway is working!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Gateway test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


def main():
    """Main function"""
    
    print("🌉 AgentCore Gateway Setup")
    print("=" * 60)
    
    # Create or find gateway
    gateway_info = create_gateway()
    
    if gateway_info:
        # Test the gateway
        test_gateway(gateway_info)
        
        print("\n" + "=" * 60)
        print("✅ Gateway setup completed!")
        print("\nNext steps:")
        print("1. Use the Gateway URL with MCP clients")
        print("2. Test with: python tests/test_gateway_mcp.py")
    else:
        print("\n❌ Gateway setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()