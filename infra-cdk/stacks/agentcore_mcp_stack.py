#!/usr/bin/env python3
"""
AWS CDK Stack for deploying MCP servers with AgentCore Runtime
Includes Lambda functions, API Gateway, and OpenTelemetry integration
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_apigatewayv2 as apigateway,
    aws_apigatewayv2_integrations as integrations,
    aws_logs as logs,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_cognito as cognito,
    aws_secretsmanager as secretsmanager,
    aws_xray as xray,
)
from constructs import Construct
import json


class AgentCoreMCPStack(Stack):
    """
    CDK Stack for deploying MCP servers with AgentCore Runtime
    
    Features:
    - Lambda functions for MCP servers (tools and feedback)
    - HTTP API Gateway for MCP protocol
    - DynamoDB for session management
    - Cognito for authentication
    - X-Ray and OpenTelemetry for observability
    - Integration with Langfuse for tracing
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table for MCP session management
        self.sessions_table = dynamodb.Table(
            self,
            "MCPSessionsTable",
            table_name=f"mcp-sessions-{self.account}",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
        )

        # Cognito User Pool for authentication
        self.user_pool = cognito.UserPool(
            self,
            "MCPUserPool",
            user_pool_name=f"mcp-agentcore-{self.account}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True,
            ),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # User Pool Client for OAuth 2.0
        self.user_pool_client = cognito.UserPoolClient(
            self,
            "MCPUserPoolClient",
            user_pool=self.user_pool,
            auth_flows=cognito.AuthFlow(
                user_srp=True,
                custom=True,
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL],
                callback_urls=["http://localhost:3000/callback"],
            ),
        )

        # Secrets for Langfuse integration
        self.langfuse_secrets = secretsmanager.Secret(
            self,
            "LangfuseSecrets",
            description="Langfuse API keys for MCP observability",
            secret_object_value={
                "LANGFUSE_PUBLIC_KEY": secretsmanager.SecretValue.unsafe_plain_text("pk-lf-xxx"),
                "LANGFUSE_SECRET_KEY": secretsmanager.SecretValue.unsafe_plain_text("sk-lf-xxx"),
                "LANGFUSE_HOST": secretsmanager.SecretValue.unsafe_plain_text("https://langfuse.com"),
            },
        )

        # Lambda Layer for MCP dependencies
        self.mcp_layer = lambda_python.PythonLayerVersion(
            self,
            "MCPDependenciesLayer",
            entry="../../mcp",  # Path to MCP directory
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="MCP server dependencies and utilities",
            layer_version_name="mcp-dependencies",
        )

        # Lambda Layer for OpenTelemetry
        self.otel_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "OTelLayer",
            layer_version_arn=f"arn:aws:lambda:{self.region}:901920570463:layer:aws-otel-python-amd64-ver-1-28-0:1",
        )

        # IAM role for Lambda functions
        self.lambda_role = iam.Role(
            self,
            "MCPLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess"),
            ],
        )

        # Grant permissions
        self.sessions_table.grant_read_write_data(self.lambda_role)
        self.langfuse_secrets.grant_read(self.lambda_role)

        # Environment variables for Lambda functions
        lambda_env = {
            "DYNAMODB_TABLE_NAME": self.sessions_table.table_name,
            "AWS_LAMBDA_EXEC_WRAPPER": "/opt/otel-instrument",  # OpenTelemetry wrapper
            "OTEL_SERVICE_NAME": "mcp-agentcore",
            "OTEL_TRACES_EXPORTER": "otlp",
            "OTEL_METRICS_EXPORTER": "otlp",
            "OTEL_LOGS_EXPORTER": "otlp",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",  # Will be configured for actual endpoint
            "OTEL_PROPAGATORS": "tracecontext,baggage,xray",
            "OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED": "true",
            "_X_AMZN_TRACE_ID": "enabled",  # AWS X-Ray integration
        }

        # Tools Server Lambda Function
        self.tools_lambda = lambda_.Function(
            self,
            "MCPToolsLambda",
            function_name=f"mcp-tools-{self.account}",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_handler.handler",
            code=lambda_.Code.from_asset("../mcp/tools_server"),
            environment=lambda_env,
            timeout=Duration.seconds(30),
            memory_size=1024,
            role=self.lambda_role,
            layers=[self.mcp_layer, self.otel_layer],
            tracing=lambda_.Tracing.ACTIVE,  # Enable X-Ray tracing
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Feedback Server Lambda Function
        self.feedback_lambda = lambda_.Function(
            self,
            "MCPFeedbackLambda",
            function_name=f"mcp-feedback-{self.account}",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_handler.handler",
            code=lambda_.Code.from_asset("../mcp/feedback_server"),
            environment=lambda_env,
            timeout=Duration.seconds(30),
            memory_size=512,
            role=self.lambda_role,
            layers=[self.mcp_layer, self.otel_layer],
            tracing=lambda_.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # HTTP API Gateway for MCP protocol
        self.api = apigateway.HttpApi(
            self,
            "MCPHttpApi",
            api_name=f"mcp-agentcore-{self.account}",
            cors_preflight=apigateway.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigateway.CorsHttpMethod.ANY],
                allow_headers=["*"],
            ),
            description="HTTP API for MCP servers with AgentCore",
        )

        # Cognito authorizer for API Gateway
        self.authorizer = apigateway.HttpAuthorizer(
            self,
            "MCPAuthorizer",
            http_api=self.api,
            type=apigateway.HttpAuthorizerType.JWT,
            jwt_configuration=apigateway.HttpJwtConfiguration(
                audience=[self.user_pool_client.user_pool_client_id],
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool.user_pool_id}",
            ),
            authorizer_name="mcp-jwt-authorizer",
        )

        # Tools Server integration
        tools_integration = integrations.HttpLambdaIntegration(
            "ToolsIntegration",
            handler=self.tools_lambda,
        )

        self.api.add_routes(
            path="/tools/mcp",
            methods=[apigateway.HttpMethod.POST],
            integration=tools_integration,
            authorizer=self.authorizer,
        )

        # Feedback Server integration
        feedback_integration = integrations.HttpLambdaIntegration(
            "FeedbackIntegration",
            handler=self.feedback_lambda,
        )

        self.api.add_routes(
            path="/feedback/mcp",
            methods=[apigateway.HttpMethod.POST],
            integration=feedback_integration,
            authorizer=self.authorizer,
        )

        # AgentCore Runtime configuration
        self.agentcore_config = {
            "runtime": {
                "protocol": "MCP",
                "endpoint": f"{self.api.url}",
                "authentication": {
                    "type": "cognito",
                    "userPoolId": self.user_pool.user_pool_id,
                    "clientId": self.user_pool_client.user_pool_client_id,
                },
                "observability": {
                    "xray": True,
                    "opentelemetry": True,
                    "langfuse": {
                        "enabled": True,
                        "secretArn": self.langfuse_secrets.secret_arn,
                    },
                },
            },
            "servers": [
                {
                    "name": "tools",
                    "path": "/tools/mcp",
                    "lambda_arn": self.tools_lambda.function_arn,
                },
                {
                    "name": "feedback",
                    "path": "/feedback/mcp",
                    "lambda_arn": self.feedback_lambda.function_arn,
                },
            ],
        }

        # Output important values
        CfnOutput(
            self,
            "MCPApiEndpoint",
            value=self.api.url or "",
            description="MCP API Gateway endpoint",
        )

        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
        )

        CfnOutput(
            self,
            "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
        )

        CfnOutput(
            self,
            "SessionsTableName",
            value=self.sessions_table.table_name,
            description="DynamoDB sessions table name",
        )

        CfnOutput(
            self,
            "ToolsLambdaArn",
            value=self.tools_lambda.function_arn,
            description="Tools server Lambda ARN",
        )

        CfnOutput(
            self,
            "FeedbackLambdaArn",
            value=self.feedback_lambda.function_arn,
            description="Feedback server Lambda ARN",
        )

        CfnOutput(
            self,
            "AgentCoreConfig",
            value=json.dumps(self.agentcore_config, indent=2),
            description="AgentCore Runtime configuration",
        )