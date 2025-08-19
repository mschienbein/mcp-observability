#!/usr/bin/env python3
"""
Deploy the isolated MCP experiment server to AgentCore Runtime
Based on the official AgentCore samples
"""

import os
import sys
import time
import json
import boto3
from pathlib import Path
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

def setup_cognito_user_pool():
    """
    Set up Amazon Cognito user pool for JWT authentication
    Returns configuration needed for AgentCore Runtime
    """
    print("Setting up Amazon Cognito user pool...")
    
    cognito_client = boto3.client('cognito-idp')
    
    # Create or get existing user pool
    user_pool_name = "mcp-experiment-pool"
    
    try:
        # Check if pool exists
        pools = cognito_client.list_user_pools(MaxResults=10)
        existing_pool = None
        for pool in pools['UserPools']:
            if pool['Name'] == user_pool_name:
                existing_pool = pool
                break
        
        if existing_pool:
            user_pool_id = existing_pool['Id']
            print(f"Using existing user pool: {user_pool_id}")
        else:
            # Create new user pool
            response = cognito_client.create_user_pool(
                PoolName=user_pool_name,
                Policies={
                    'PasswordPolicy': {
                        'MinimumLength': 8,
                        'RequireUppercase': True,
                        'RequireLowercase': True,
                        'RequireNumbers': True,
                        'RequireSymbols': False
                    }
                },
                AutoVerifiedAttributes=['email']
            )
            user_pool_id = response['UserPool']['Id']
            print(f"Created new user pool: {user_pool_id}")
        
        # Create app client with proper auth flows
        try:
            # Check if client already exists
            clients = cognito_client.list_user_pool_clients(UserPoolId=user_pool_id)
            existing_client = None
            for client in clients['UserPoolClients']:
                if client['ClientName'] == 'mcp-experiment-client':
                    existing_client = client
                    client_id = client['ClientId']
                    break
            
            if not existing_client:
                app_client_response = cognito_client.create_user_pool_client(
                    UserPoolId=user_pool_id,
                    ClientName='mcp-experiment-client',
                    GenerateSecret=False,
                    ExplicitAuthFlows=[
                        'ALLOW_USER_PASSWORD_AUTH',
                        'ALLOW_REFRESH_TOKEN_AUTH',
                        'ALLOW_ADMIN_USER_PASSWORD_AUTH'  # Required for AdminInitiateAuth
                    ]
                )
                client_id = app_client_response['UserPoolClient']['ClientId']
        except Exception as e:
            print(f"Error creating app client: {e}")
            raise
        
        # Get region
        region = boto3.Session().region_name
        
        # Build discovery URL for JWT validation (OpenID configuration format)
        discovery_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
        
        # Create a test user and get bearer token
        username = "mcp-test-user"
        password = "TestPassword123!"
        
        try:
            cognito_client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=username,
                TemporaryPassword=password,
                MessageAction='SUPPRESS'
            )
            
            # Set permanent password
            cognito_client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=username,
                Password=password,
                Permanent=True
            )
            print(f"Created test user: {username}")
        except cognito_client.exceptions.UsernameExistsException:
            print(f"Test user already exists: {username}")
        
        # Authenticate and get token
        auth_response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        bearer_token = auth_response['AuthenticationResult']['IdToken']
        
        config = {
            'user_pool_id': user_pool_id,
            'client_id': client_id,
            'discovery_url': discovery_url,
            'bearer_token': bearer_token,
            'username': username
        }
        
        print("Cognito setup completed ✓")
        return config
        
    except Exception as e:
        print(f"Error setting up Cognito: {e}")
        raise

def main():
    """Main deployment function"""
    
    print("="*60)
    print("AgentCore MCP Experiment Deployment")
    print("="*60)
    
    # Get AWS session info
    boto_session = Session()
    region = boto_session.region_name
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    print(f"AWS Account: {account_id}")
    print(f"AWS Region: {region}")
    print()
    
    # Check required files
    # Script is in deployment/ folder, need to go up one level
    project_dir = Path(__file__).parent.parent
    required_files = ['mcps/experiment_server/server.py', 'requirements.txt']
    
    for file in required_files:
        file_path = project_dir / file
        if not file_path.exists():
            print(f"❌ Required file not found: {file_path}")
            sys.exit(1)
    print("✓ All required files found")
    print()
    
    # Set up Cognito authentication
    try:
        cognito_config = setup_cognito_user_pool()
    except Exception as e:
        print(f"❌ Failed to set up Cognito: {e}")
        sys.exit(1)
    
    # Initialize AgentCore Runtime
    agentcore_runtime = Runtime()
    
    # Configure authorization
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [
                cognito_config['client_id']
            ],
            "discoveryUrl": cognito_config['discovery_url'],
        }
    }
    
    # Configure the runtime
    print("\nConfiguring AgentCore Runtime...")
    
    # Change to project directory for correct relative paths
    os.chdir(project_dir)
    print(f"Working directory: {os.getcwd()}")
    
    try:
        response = agentcore_runtime.configure(
            entrypoint="mcps/experiment_server/server.py",
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region,
            authorizer_configuration=auth_config,
            protocol="MCP",
            agent_name="mcp_experiment_agentcore"
        )
        print(f"✓ Configuration completed {response}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        sys.exit(1)
    
    # Launch to AgentCore Runtime
    print("\nLaunching MCP server to AgentCore Runtime...")
    print("This may take several minutes...")
    
    try:
        launch_result = agentcore_runtime.launch()
        print(f"✓ Launch completed {launch_result}")
        print(f"Agent ARN: {launch_result.agent_arn}")
        print(f"Agent ID: {launch_result.agent_id}")
        print(f"ECR URI: {launch_result.ecr_uri}")
    except Exception as e:
        print(f"❌ Launch failed: {e}")
        sys.exit(1)
    
    # Check deployment status
    print("\nChecking AgentCore Runtime status...")
    max_attempts = 60  # 10 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        try:
            status_response = agentcore_runtime.status()
            status = status_response.endpoint['status']
            
            if status == 'READY':
                print(f"✅ AgentCore Runtime is READY!")
                break
            elif status in ['CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']:
                print(f"❌ Deployment failed with status: {status}")
                sys.exit(1)
            else:
                print(f"Status: {status} - waiting... ({attempt}/{max_attempts})")
                time.sleep(10)
                attempt += 1
        except Exception as e:
            print(f"Error checking status: {e}")
            time.sleep(10)
            attempt += 1
    
    if attempt >= max_attempts:
        print("❌ Timeout waiting for deployment")
        sys.exit(1)
    
    # Store configuration for later use
    print("\nStoring configuration...")
    
    ssm_client = boto3.client('ssm', region_name=region)
    secrets_client = boto3.client('secretsmanager', region_name=region)
    
    # Store agent ARN in Parameter Store
    try:
        ssm_client.put_parameter(
            Name='/mcp_experiment/runtime/agent_arn',
            Value=launch_result.agent_arn,
            Type='String',
            Description='Agent ARN for MCP experiment server',
            Overwrite=True
        )
        print("✓ Agent ARN stored in Parameter Store")
    except Exception as e:
        print(f"Warning: Could not store ARN in Parameter Store: {e}")
    
    # Store Cognito credentials in Secrets Manager
    try:
        secret_name = 'mcp_experiment/cognito/credentials'
        try:
            secrets_client.create_secret(
                Name=secret_name,
                Description='Cognito credentials for MCP experiment server',
                SecretString=json.dumps(cognito_config)
            )
        except secrets_client.exceptions.ResourceExistsException:
            secrets_client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(cognito_config)
            )
        print("✓ Cognito credentials stored in Secrets Manager")
    except Exception as e:
        print(f"Warning: Could not store credentials in Secrets Manager: {e}")
    
    # Output summary
    print("\n" + "="*60)
    print("DEPLOYMENT SUCCESSFUL!")
    print("="*60)
    print(f"\n📍 Agent ARN:\n   {launch_result.agent_arn}")
    print(f"\n🔑 Bearer Token (for testing):\n   {cognito_config['bearer_token'][:50]}...")
    print(f"\n🌐 MCP Endpoint URL:")
    
    encoded_arn = launch_result.agent_arn.replace(':', '%3A').replace('/', '%2F')
    mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    print(f"   {mcp_url}")
    
    print("\n📊 Available Tools:")
    tools = [
        "calculate_fibonacci - Calculate Fibonacci numbers with performance tracking",
        "analyze_text - Analyze text and return detailed statistics",
        "generate_random_data - Generate various types of random test data",
        "weather_simulator - Simulate weather data for any location",
        "system_health_check - Check system health and observability metrics"
    ]
    for tool in tools:
        print(f"   • {tool}")
    
    print("\n🔍 Observability Features:")
    print("   • Distributed tracing with trace IDs")
    print("   • Span tracking for detailed execution flow")
    print("   • Metrics collection with tags")
    print("   • Structured logging with context")
    print("   • Health check endpoint with system status")
    
    print("\n📝 Next Steps:")
    print("   1. Test with: python test_deployed_server.py")
    print("   2. Monitor CloudWatch logs for observability data")
    print("   3. Integrate with your AI agents or applications")
    print("   4. Scale as needed through AgentCore Runtime")
    
    print("\n✅ Your isolated MCP experiment is ready for testing!")

if __name__ == "__main__":
    # Change to script directory
    os.chdir(Path(__file__).parent)
    main()