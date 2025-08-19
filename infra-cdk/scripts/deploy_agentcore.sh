#!/bin/bash

# Deploy existing MCP servers to AWS AgentCore Runtime
# This script deploys the MCP servers from the mcp/ directory to AgentCore
# Using the bedrock-agentcore-starter-toolkit CLI

set -e

echo "=========================================="
echo "Deploying MCP Servers to AgentCore Runtime"
echo "=========================================="

# Check prerequisites
if ! command -v agentcore &> /dev/null; then
    echo "AgentCore CLI not found. Installing bedrock-agentcore-starter-toolkit..."
    pip install bedrock-agentcore-starter-toolkit
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Configuration
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
MCP_DIR="$PROJECT_ROOT/mcp"
REGION=${AWS_REGION:-us-east-1}
PROFILE=${AWS_PROFILE:-default}

# Export AWS credentials
export AWS_PROFILE=$PROFILE
export AWS_REGION=$REGION

echo "Project root: $PROJECT_ROOT"
echo "Using AWS Profile: $PROFILE"
echo "Deploying to Region: $REGION"

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Install dependencies if needed
echo ""
echo "Ensuring dependencies are installed..."
uv pip install -e .

# Deploy Tools Server
echo ""
echo "=========================================="
echo "1. Deploying Tools Server"
echo "=========================================="

cd "$MCP_DIR/tools_server"

# Create an AgentCore-compatible wrapper that imports the existing server
cat > agentcore_wrapper.py << 'EOF'
#!/usr/bin/env python3
"""AgentCore wrapper for MCP Tools Server"""

import sys
import os

# Add parent directory to path to import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the main server with AgentCore-compatible settings
from tools_server.main import mcp

if __name__ == "__main__":
    # Override settings for AgentCore compatibility
    mcp.host = "0.0.0.0"
    mcp.port = 8000
    mcp.stateless_http = True
    
    # Run in streamable-http mode for AgentCore
    mcp.run(transport="streamable-http")
EOF

# Create requirements file for AgentCore
cat > agentcore_requirements.txt << 'EOF'
fastmcp>=2.10
langfuse>=2.0.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-fastapi>=0.41b0
opentelemetry-exporter-otlp>=1.20.0
python-dotenv>=1.0.0
EOF

echo "Configuring Tools Server with AgentCore CLI..."
agentcore configure \
    --entrypoint agentcore_wrapper.py \
    --name mcp-observability-tools \
    --protocol MCP \
    --requirements-file agentcore_requirements.txt \
    --execution-role "${AGENTCORE_EXECUTION_ROLE:-}"

echo "Launching Tools Server to AgentCore Runtime..."
TOOLS_OUTPUT=$(agentcore launch --output json 2>&1)
if [ $? -eq 0 ]; then
    TOOLS_ARN=$(echo "$TOOLS_OUTPUT" | jq -r '.agent_arn')
    echo "✅ Tools Server deployed: $TOOLS_ARN"
else
    echo "❌ Failed to deploy Tools Server"
    echo "$TOOLS_OUTPUT"
fi

# Deploy Feedback Server
echo ""
echo "=========================================="
echo "2. Deploying Feedback Server"
echo "=========================================="

cd "$MCP_DIR/feedback_server"

# Create an AgentCore-compatible wrapper
cat > agentcore_wrapper.py << 'EOF'
#!/usr/bin/env python3
"""AgentCore wrapper for MCP Feedback Server"""

import sys
import os

# Add parent directory to path to import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the main server with AgentCore-compatible settings
from feedback_server.main import mcp

if __name__ == "__main__":
    # Override settings for AgentCore compatibility
    mcp.host = "0.0.0.0"
    mcp.port = 8000
    mcp.stateless_http = True
    
    # Run in streamable-http mode for AgentCore
    mcp.run(transport="streamable-http")
EOF

# Use same requirements file
cp ../tools_server/agentcore_requirements.txt .

echo "Configuring Feedback Server with AgentCore CLI..."
agentcore configure \
    --entrypoint agentcore_wrapper.py \
    --name mcp-observability-feedback \
    --protocol MCP \
    --requirements-file agentcore_requirements.txt \
    --execution-role "${AGENTCORE_EXECUTION_ROLE:-}"

echo "Launching Feedback Server to AgentCore Runtime..."
FEEDBACK_OUTPUT=$(agentcore launch --output json 2>&1)
if [ $? -eq 0 ]; then
    FEEDBACK_ARN=$(echo "$FEEDBACK_OUTPUT" | jq -r '.agent_arn')
    echo "✅ Feedback Server deployed: $FEEDBACK_ARN"
else
    echo "❌ Failed to deploy Feedback Server"
    echo "$FEEDBACK_OUTPUT"
fi

# Output deployment information
echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="

if [ -n "$TOOLS_ARN" ]; then
    echo "✅ Tools Server ARN: $TOOLS_ARN"
    
    # Save ARN for future use
    echo "$TOOLS_ARN" > "$PROJECT_ROOT/.agentcore_tools_arn"
fi

if [ -n "$FEEDBACK_ARN" ]; then
    echo "✅ Feedback Server ARN: $FEEDBACK_ARN"
    
    # Save ARN for future use
    echo "$FEEDBACK_ARN" > "$PROJECT_ROOT/.agentcore_feedback_arn"
fi

echo ""
echo "To test the deployed servers:"
echo ""
echo "1. Tools Server:"
echo "   agentcore invoke '{\"prompt\": \"Add 5 and 3\"}' --agent-arn $TOOLS_ARN"
echo ""
echo "2. Feedback Server:"
echo "   agentcore invoke '{\"prompt\": \"Submit feedback for session-123 with rating 5\"}' --agent-arn $FEEDBACK_ARN"
echo ""
echo "To integrate with AgentCore Gateway:"
echo "  - Use the ARNs above when configuring gateway endpoints"
echo "  - Gateway will handle MCP protocol translation automatically"
echo ""
echo "Environment Variables (set these in AgentCore console):"
echo "  - LANGFUSE_PUBLIC_KEY"
echo "  - LANGFUSE_SECRET_KEY"
echo "  - LANGFUSE_HOST"
echo ""
echo "Note: The servers are configured with:"
echo "  - Stateless HTTP mode for session isolation"
echo "  - Port 8000 with /mcp endpoint (AgentCore standard)"
echo "  - Full observability via Langfuse middleware"