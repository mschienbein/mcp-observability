#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.langfuse_stack import LangfuseStack
from stacks.librechat_stack import LibreChatStack
from stacks.agentcore_mcp_stack import AgentCoreMCPStack

app = cdk.App()

# Ensure we use the same bootstrap qualifier as the environment
synth = cdk.DefaultStackSynthesizer(qualifier="mcpobs")

# Environment configuration
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
)

# Deploy Langfuse stack
langfuse_stack = LangfuseStack(
    app,
    "LangfuseStack",
    synthesizer=synth,
    env=env,
    description="Langfuse observability platform with ClickHouse backend"
)

# Deploy LibreChat stack
librechat_stack = LibreChatStack(
    app,
    "LibreChatStack",
    synthesizer=synth,
    env=env,
    description="LibreChat self-hosted AI chat interface - Simplified Demo"
)

# Deploy AgentCore MCP stack
agentcore_stack = AgentCoreMCPStack(
    app,
    "AgentCoreMCPStack",
    synthesizer=synth,
    env=env,
    description="MCP servers deployed with AWS AgentCore Runtime"
)

# Add stack dependencies if needed
# librechat_stack.add_dependency(langfuse_stack)  # Uncomment if LibreChat depends on Langfuse
# agentcore_stack.add_dependency(langfuse_stack)  # AgentCore can use Langfuse for tracing

app.synth()
