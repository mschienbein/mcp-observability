#!/usr/bin/env python3
"""
Lambda handler for MCP Tools Server with AgentCore Runtime
Includes OpenTelemetry and Langfuse integration
"""

import json
import os
import boto3
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from langfuse import Langfuse
from langfuse.decorators import observe
from fastmcp import FastMCP
from datetime import datetime

# Initialize AWS Lambda Powertools
logger = Logger(service="mcp-tools")
tracer = Tracer(service="mcp-tools")
metrics = Metrics(namespace="MCP/Tools")

# Initialize OpenTelemetry tracer
otel_tracer = trace.get_tracer(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("DYNAMODB_TABLE_NAME", "mcp-sessions")
sessions_table = dynamodb.Table(table_name)

# Initialize Langfuse client
def get_langfuse_client():
    """Get Langfuse client with credentials from Secrets Manager"""
    secrets_client = boto3.client("secretsmanager")
    try:
        secret_value = secrets_client.get_secret_value(
            SecretId=os.environ.get("LANGFUSE_SECRET_ARN", "LangfuseSecrets")
        )
        secrets = json.loads(secret_value["SecretString"])
        return Langfuse(
            public_key=secrets.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=secrets.get("LANGFUSE_SECRET_KEY"),
            host=secrets.get("LANGFUSE_HOST", "https://langfuse.com"),
        )
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")
        return None

langfuse = get_langfuse_client()

# Initialize FastMCP server
mcp = FastMCP("MCP Tools Server - AgentCore")

@mcp.tool()
async def add_numbers(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

@mcp.tool()
async def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
async def get_aws_account() -> str:
    """Get current AWS account ID"""
    return boto3.client("sts").get_caller_identity()["Account"]

@mcp.tool()
async def list_s3_buckets() -> list:
    """List all S3 buckets in the account"""
    s3 = boto3.client("s3")
    response = s3.list_buckets()
    return [bucket["Name"] for bucket in response.get("Buckets", [])]

@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@metrics.log_metrics(capture_cold_start_metric=True)
@observe(as_type="generation")  # Langfuse decorator
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for MCP Tools Server
    Processes MCP protocol requests via HTTP API Gateway
    """
    
    # Start OpenTelemetry span
    with otel_tracer.start_as_current_span("mcp_tools_handler") as span:
        try:
            # Extract request details
            body = json.loads(event.get("body", "{}"))
            headers = event.get("headers", {})
            
            # Extract session ID from headers or body
            session_id = (
                headers.get("x-mcp-session-id") or
                headers.get("mcp-session-id") or
                body.get("session_id") or
                "unknown"
            )
            
            # Extract user ID from JWT claims
            request_context = event.get("requestContext", {})
            authorizer = request_context.get("authorizer", {})
            jwt_claims = authorizer.get("jwt", {}).get("claims", {})
            user_id = jwt_claims.get("sub", "unknown")
            
            # Set span attributes
            span.set_attribute("mcp.session_id", session_id)
            span.set_attribute("mcp.user_id", user_id)
            span.set_attribute("mcp.method", body.get("method", "unknown"))
            
            # Log request
            logger.info(
                "Processing MCP request",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "method": body.get("method"),
                }
            )
            
            # Record session in DynamoDB
            sessions_table.put_item(
                Item={
                    "session_id": session_id,
                    "timestamp": int(datetime.now().timestamp()),
                    "user_id": user_id,
                    "method": body.get("method", "unknown"),
                    "ttl": int(datetime.now().timestamp()) + 86400,  # 24 hour TTL
                }
            )
            
            # Process MCP request
            mcp_response = mcp.process_request(body)
            
            # Create Langfuse trace if available
            if langfuse:
                trace = langfuse.trace(
                    name="mcp_tools_request",
                    session_id=session_id,
                    user_id=user_id,
                    metadata={
                        "method": body.get("method"),
                        "lambda_request_id": context.request_id,
                        "function_name": context.function_name,
                    },
                    input=body,
                    output=mcp_response,
                )
            
            # Record metrics
            metrics.add_metric(name="RequestProcessed", unit=MetricUnit.Count, value=1)
            metrics.add_metadata(key="session_id", value=session_id)
            metrics.add_metadata(key="user_id", value=user_id)
            
            # Set success status
            span.set_status(Status(StatusCode.OK))
            
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "X-MCP-Session-Id": session_id,
                },
                "body": json.dumps(mcp_response),
            }
            
        except Exception as e:
            # Log error
            logger.error(f"Error processing request: {e}")
            
            # Set error status in span
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Record error metric
            metrics.add_metric(name="RequestError", unit=MetricUnit.Count, value=1)
            
            # Create error trace in Langfuse if available
            if langfuse:
                langfuse.trace(
                    name="mcp_tools_error",
                    session_id=session_id,
                    user_id=user_id,
                    metadata={
                        "error": str(e),
                        "lambda_request_id": context.request_id,
                    },
                    level="ERROR",
                )
            
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                },
                "body": json.dumps({
                    "error": "Internal server error",
                    "message": str(e),
                }),
            }