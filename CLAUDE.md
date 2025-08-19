# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This MCP observability stack is fully deployed with:
- **Langfuse v3**: Observability platform with ClickHouse backend (deployed on AWS)
- **LibreChat**: Self-hosted AI chat interface (deployed on AWS)
- **MCP Servers**: Tools and feedback servers with automatic Langfuse tracing
- **AgentCore Runtime**: Support for deploying MCP servers to AWS Bedrock AgentCore (preview)
- **Infrastructure**: Production-ready CDK stacks for all services

## Deployment Instructions

### Prerequisites
1. AWS Account with appropriate permissions
2. Python 3.10+ with `uv` package manager
3. Node.js 18+ for UI development
4. AWS CDK CLI: `npm install -g aws-cdk`

### Required Environment Variables

Create a `.env` file in the project root with:
```bash
# Langfuse Configuration (REQUIRED)
LANGFUSE_SECRET_KEY=sk-lf-xxxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
LANGFUSE_HOST=http://your-langfuse-alb-url

# Optional: Redis for distributed session tracking
REDIS_URL=redis://localhost:6379

# AWS Configuration (for infrastructure)
AWS_REGION=us-east-1
AWS_PROFILE=your-profile
```

### ClickHouse Schema Setup

**CRITICAL**: The ClickHouse schema must be properly configured for Langfuse to work.

1. Connect to your ClickHouse instance
2. Run the complete schema from: `infra-cdk/scripts/database/langfuse_clickhouse_schema.sql`
3. This creates all required tables with proper columns for:
   - Traces (with environment, latency, cost tracking)
   - Observations (with metrics and performance data)
   - Scores, schema_migrations, event_log, etc.

### Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd mcp-observability

# 2. Install dependencies
uv venv
uv pip install -e .

# 3. Copy and configure .env file
cp .env.example .env  # Edit with your credentials

# 4. Start MCP servers
# Terminal 1: Tools Server (port 3002)
uv run python -m mcp.tools_server.main

# Terminal 2: Feedback Server (port 3003)
uv run python -m mcp.feedback_server.main

# 5. Test the setup
uv run python clients/test_langfuse_simple.py
uv run python clients/mcp_client.py tools
```

### Key Files

1. **Environment Config**: `mcp/common/config.py` - Auto-loads .env file
2. **Middleware**: `mcp/common/mcp_obs_middleware.py` - Langfuse tracing integration
3. **ClickHouse Schema**: `infra-cdk/scripts/database/langfuse_clickhouse_schema.sql` - Complete DB schema
4. **Test Scripts**: `clients/test_langfuse_*.py` - Verify integration
5. **CDK Stacks**: `infra-cdk/stacks/` - Langfuse, LibreChat, and AgentCore deployments
6. **AgentCore App**: `mcp/agentcore_app.py` - MCP servers configured for AgentCore Runtime

## Project Overview

This is an MCP (Model Control Protocol) observability demo that implements separate FastMCP tools and feedback servers with Langfuse tracing. The project combines Python backend services, React frontend, and AWS CDK infrastructure-as-code.

## Architecture

### Components
- **MCP Tools Server** (`mcp/tools_server/`): FastMCP server on port 3002 providing demo tools
- **MCP Feedback Server** (`mcp/feedback_server/`): FastMCP server on port 3003 for feedback collection
- **AgentCore Integration** (`mcp/agentcore_app.py`): MCP servers ready for AgentCore Runtime deployment
- **UI** (`ui/`): React TypeScript frontend built with Vite
- **Infrastructure** (`infra-cdk/`): AWS CDK stacks for Langfuse, LibreChat, and AgentCore MCP deployment
- **Observability Middleware** (`mcp/common/mcp_obs_middleware.py`): Shared Langfuse tracing middleware that captures MCP session IDs and user IDs

### Key Dependencies
- **Python**: FastMCP, Langfuse, FastAPI, Uvicorn, Redis
- **Frontend**: React 19, Vite, TypeScript
- **Infrastructure**: AWS CDK v2, Docker containers for Langfuse

## Common Development Commands

### Python MCP Servers

#### Local Development
```bash
# Start tools server (port 3002)
uv run python mcp/tools_server/main.py
# OR
uv run server-tools

# Start feedback server (port 3003)  
uv run python mcp/feedback_server/main.py
# OR
uv run server-feedback

# Test MCP clients
uv run test-mcp-tools
uv run test-mcp-feedback
```

#### AgentCore Deployment
```bash
# Deploy to AgentCore Runtime (recommended for production)
uv run deploy-agentcore

# Or deploy supporting Lambda infrastructure
uv run deploy-agentcore-infra
```

### Frontend UI
```bash
# Install dependencies
uv run ui-install
# OR
npm --prefix ui install

# Development server
uv run ui-dev
# OR
npm run ui:dev

# Build for production
uv run ui-build
# OR  
npm run ui:build

# Preview production build
uv run ui-preview
# OR
npm run ui:preview
```

### Infrastructure Deployment
```bash
# Install CDK dependencies (first time only)
uv run cdk-install

# Set AWS credentials
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1

# Bootstrap CDK (first time only)
uv run cdk-bootstrap

# Deploy Langfuse stack
uv run deploy-langfuse

# Deploy LibreChat stack
uv run deploy-librechat

# Deploy AgentCore MCP infrastructure
uv run deploy-agentcore-infra

# Deploy MCP servers to AgentCore Runtime
uv run deploy-agentcore

# Deploy all CDK stacks
uv run deploy-all

# Optional: Deploy with ClickHouse EC2 instance
cd infra-cdk && REGION=us-east-1 APPLY=true \
bash scripts/setup/provision_clickhouse_ec2.sh
```

## Code Standards

### Python
- Code formatting: Black (line-length: 100) and isort (profile: black) configured in `pyproject.toml`
- Python 3.10+ required
- Use `uv` for dependency management when available

### TypeScript/React  
- Node.js 22+ required (enforced in ui/package.json)
- TypeScript strict mode
- Vite for build tooling

## Environment Configuration

### MCP Servers
Configure Langfuse credentials in `mcp.json` or environment variables:
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`  
- `LANGFUSE_HOST`

### Infrastructure
The CDK stack creates AWS Secrets Manager entries for:
- Database credentials
- NextAuth secrets
- ClickHouse connection details (populate after deployment)
- Encryption keys

## Development Workflow

1. **Local Development**: Run MCP servers and UI locally with hot-reload enabled
2. **Observability**: All MCP requests are automatically traced via Langfuse middleware
3. **Session Tracking**: The middleware captures session IDs from various headers (Mcp-Session-Id, X-MCP-Session-Id, etc.) and links them to Langfuse traces
4. **Infrastructure**: Deploy the full Langfuse stack to AWS using CDK for production observability

## Testing

Manual test scripts in the `clients/` directory:
- `mcp_client.py`: Tests MCP server connectivity
- `langfuse_test.py`: Comprehensive Langfuse SDK integration test

Run tests with:
```bash
uv run test-langfuse        # Test Langfuse integration
uv run test-mcp-tools       # Test tools server
uv run test-mcp-feedback    # Test feedback server
```