# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Control Protocol) observability demo that implements separate FastMCP tools and feedback servers with Langfuse tracing. The project combines Python backend services, React frontend, and AWS CDK infrastructure-as-code.

## Architecture

### Components
- **MCP Tools Server** (`server/tools_server/`): FastMCP server on port 3002 providing demo tools
- **MCP Feedback Server** (`server/feedback_server/`): FastMCP server on port 3003 for feedback collection
- **UI** (`ui/`): React TypeScript frontend built with Vite
- **Infrastructure** (`infra-cdk/`): AWS CDK stack for deploying Langfuse on AWS with ECS, RDS, ElastiCache, and optional ClickHouse
- **Observability Middleware** (`server/common/mcp_obs_middleware.py`): Shared Langfuse tracing middleware that captures MCP session IDs and user IDs

### Key Dependencies
- **Python**: FastMCP, Langfuse, FastAPI, Uvicorn, Redis
- **Frontend**: React 19, Vite, TypeScript
- **Infrastructure**: AWS CDK v2, Docker containers for Langfuse

## Common Development Commands

### Python MCP Servers
```bash
# Start tools server (port 3002)
uv run python server/tools_server/main.py
# OR
npm run server:tools

# Start feedback server (port 3003)  
uv run python server/feedback_server/main.py
# OR
npm run server:feedback

# Test MCP clients
make mcp-tools-client
make mcp-feedback-client
```

### Frontend UI
```bash
# Install dependencies (from root)
make ui-install
# OR
npm --prefix ui install

# Development server
make ui-dev
# OR
npm run ui:dev

# Build for production
make ui-build
# OR  
npm run ui:build

# Preview production build
make ui-preview
# OR
npm run ui:preview
```

### Infrastructure Deployment
```bash
# Navigate to infra directory
cd infra-cdk/

# Set AWS credentials
export AWS_PROFILE=kinpachi
export AWS_REGION=us-east-1

# Synthesize CDK stack
npx -y aws-cdk@^2 synth

# Deploy stack (uses qualifier 'mcpobs')
npx -y aws-cdk@^2 deploy LangfuseStack --require-approval never

# Optional: Deploy with ClickHouse EC2 instance
REGION=us-east-1 PROFILE=kinpachi APPLY=true \
bash infra-cdk/scripts/provision_clickhouse_ec2.sh
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

Currently no automated tests are configured. The `clients/` directory contains manual test scripts:
- `mcp_client.py`: Tests MCP server connectivity
- `langfuse_smoke_test.py`: Validates Langfuse integration