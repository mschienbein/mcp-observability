#!/usr/bin/env python3
"""
Lambda handler for MCP Feedback Server with AgentCore Runtime
Includes OpenTelemetry and Langfuse integration
"""

import json
import os
import boto3
from typing import Dict, Any, Optional
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
from decimal import Decimal

# Initialize AWS Lambda Powertools
logger = Logger(service="mcp-feedback")
tracer = Tracer(service="mcp-feedback")
metrics = Metrics(namespace="MCP/Feedback")

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
mcp = FastMCP("MCP Feedback Server - AgentCore")

@mcp.tool()
async def submit_feedback(
    session_id: str,
    rating: int,
    comment: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Submit feedback for a session
    
    Args:
        session_id: The session ID to provide feedback for
        rating: Rating from 1-5
        comment: Optional text comment
        metadata: Optional additional metadata
    
    Returns:
        Confirmation of feedback submission
    """
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5")
    
    feedback_id = f"feedback_{session_id}_{int(datetime.now().timestamp())}"
    
    # Store feedback in DynamoDB
    sessions_table.put_item(
        Item={
            "session_id": f"feedback#{session_id}",
            "timestamp": int(datetime.now().timestamp()),
            "feedback_id": feedback_id,
            "rating": rating,
            "comment": comment or "",
            "metadata": metadata or {},
            "ttl": int(datetime.now().timestamp()) + 2592000,  # 30 day TTL
        }
    )
    
    # Send score to Langfuse if available
    if langfuse:
        langfuse.score(
            name="user_feedback",
            value=float(rating) / 5.0,  # Normalize to 0-1
            trace_id=session_id,
            comment=comment,
            data_type="NUMERIC",
        )
    
    return {
        "feedback_id": feedback_id,
        "status": "submitted",
        "rating": rating,
        "comment": comment,
    }

@mcp.tool()
async def get_session_feedback(session_id: str) -> list:
    """
    Get all feedback for a session
    
    Args:
        session_id: The session ID to get feedback for
    
    Returns:
        List of feedback entries
    """
    response = sessions_table.query(
        KeyConditionExpression="session_id = :sid",
        ExpressionAttributeValues={
            ":sid": f"feedback#{session_id}"
        }
    )
    
    return response.get("Items", [])

@mcp.tool()
async def update_feedback(
    feedback_id: str,
    session_id: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update existing feedback
    
    Args:
        feedback_id: The feedback ID to update
        session_id: The session ID the feedback belongs to
        rating: Optional new rating
        comment: Optional new comment
    
    Returns:
        Updated feedback entry
    """
    update_expr = []
    expr_values = {}
    
    if rating is not None:
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        update_expr.append("rating = :r")
        expr_values[":r"] = rating
    
    if comment is not None:
        update_expr.append("comment = :c")
        expr_values[":c"] = comment
    
    if not update_expr:
        raise ValueError("No updates provided")
    
    response = sessions_table.update_item(
        Key={
            "session_id": f"feedback#{session_id}",
            "timestamp": feedback_id.split("_")[-1],
        },
        UpdateExpression=f"SET {', '.join(update_expr)}",
        ExpressionAttributeValues=expr_values,
        ReturnValues="ALL_NEW",
    )
    
    return response.get("Attributes", {})

@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@metrics.log_metrics(capture_cold_start_metric=True)
@observe(as_type="generation")  # Langfuse decorator
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for MCP Feedback Server
    Processes MCP protocol requests via HTTP API Gateway
    """
    
    # Start OpenTelemetry span
    with otel_tracer.start_as_current_span("mcp_feedback_handler") as span:
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
                "Processing MCP feedback request",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "method": body.get("method"),
                }
            )
            
            # Process MCP request
            mcp_response = mcp.process_request(body)
            
            # Create Langfuse trace if available
            if langfuse:
                trace = langfuse.trace(
                    name="mcp_feedback_request",
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
            metrics.add_metric(name="FeedbackProcessed", unit=MetricUnit.Count, value=1)
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
            logger.error(f"Error processing feedback request: {e}")
            
            # Set error status in span
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Record error metric
            metrics.add_metric(name="FeedbackError", unit=MetricUnit.Count, value=1)
            
            # Create error trace in Langfuse if available
            if langfuse:
                langfuse.trace(
                    name="mcp_feedback_error",
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