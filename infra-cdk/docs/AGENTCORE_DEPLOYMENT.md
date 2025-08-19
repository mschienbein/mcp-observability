# AgentCore MCP Server Deployment

## Overview

Amazon Bedrock AgentCore provides enterprise-grade runtime for deploying AI agents and MCP servers at scale. This guide covers deploying MCP servers to AgentCore Runtime with comprehensive observability.

## Architecture

### AgentCore Services Used

1. **AgentCore Runtime** - Serverless execution environment for MCP servers
2. **AgentCore Gateway** - Transforms MCP servers into agent-ready tools
3. **AgentCore Observability** - Built-in tracing and debugging
4. **AgentCore Identity** - Secure access to AWS services

### Deployment Approaches

We provide two deployment methods:

#### 1. Native AgentCore CLI Deployment (Recommended)
- Uses `agentcore` CLI directly
- Deploys MCP servers as containerized applications
- Full AgentCore Runtime features
- Built-in session isolation and scaling

#### 2. Lambda + API Gateway (CDK Stack)
- Traditional serverless deployment
- Uses CDK for infrastructure
- Custom observability with OpenTelemetry + Langfuse
- More control over infrastructure

## Native AgentCore Deployment

### Prerequisites

```bash
# Install AgentCore CLI
pip install bedrock-agentcore-starter-toolkit

# Configure AWS credentials
aws configure
```

### Quick Deployment

```bash
# Use the deployment script
uv run deploy-agentcore

# Or deploy manually
cd mcp/tools_server
agentcore configure -e agentcore_tools.py --protocol MCP
agentcore launch
```

### MCP Server Requirements

For AgentCore compatibility, MCP servers must:
1. Use stateless HTTP mode
2. Listen on `0.0.0.0:8000`
3. Support streamable-http transport

Example:
```python
from fastmcp import FastMCP

mcp = FastMCP(host="0.0.0.0", port=8000, stateless_http=True)

@mcp.tool()
async def my_tool(param: str) -> str:
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

## Lambda Deployment (CDK)

### Deploy Infrastructure

```bash
# Install CDK dependencies
uv pip install -e .[cdk]

# Deploy the stack
uv run deploy-agentcore-infra
```

### Stack Components

- **Lambda Functions**: Serverless compute for MCP servers
- **API Gateway**: HTTP endpoints with JWT auth
- **Cognito**: User authentication
- **DynamoDB**: Session storage
- **CloudWatch**: Logs and metrics
- **X-Ray**: Distributed tracing

## Observability

### AgentCore Native
- Automatic tracing of all requests
- Session tracking
- Tool invocation metrics
- Error tracking and debugging

### Custom Stack
- **OpenTelemetry**: Distributed tracing
- **Langfuse**: LLM observability
- **CloudWatch**: AWS native monitoring
- **X-Ray**: AWS tracing

## Testing

### Local Testing
```bash
# Run MCP server locally
agentcore launch --local

# Test with MCP Inspector
npx @modelcontextprotocol/inspector mcp_server.py
```

### Remote Testing
```bash
# Get agent ARN from deployment
AGENT_ARN=arn:aws:bedrock-agentcore:...

# Invoke the agent
agentcore invoke '{"prompt": "Test message"}' --agent-arn $AGENT_ARN
```

## Integration with AgentCore Gateway

AgentCore Gateway can expose MCP servers as tools:

1. Deploy MCP server to AgentCore Runtime
2. Configure Gateway endpoint
3. Gateway automatically handles MCP protocol translation
4. Agents can discover and use tools via semantic search

## Environment Variables

### Required for Langfuse Integration
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://your-langfuse-host
```

### Optional for OpenTelemetry
```bash
OTEL_SERVICE_NAME=mcp-agentcore
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-collector
OTEL_TRACES_EXPORTER=otlp
```

## Limitations

### Current Limitations (Preview)
- CDK primitives not yet available (coming soon)
- Requires containerization via CodeBuild
- MCP servers must be stateless
- Session duration limited to 8 hours

### Comparison: AgentCore vs Lambda

| Feature | AgentCore Runtime | Lambda + CDK |
|---------|------------------|--------------|
| Deployment | CLI-based | CDK/IaC |
| Scaling | Automatic | Configured |
| Session Management | Built-in | Custom (DynamoDB) |
| Protocol Support | MCP native | HTTP wrapper |
| Observability | Native + custom | Custom only |
| Cost | Usage-based | Per invocation |
| Setup Complexity | Low | Medium |
| Infrastructure Control | Managed | Full control |

## Best Practices

1. **Use Stateless Servers**: AgentCore requires stateless MCP servers
2. **Enable Observability**: Configure both Langfuse and OpenTelemetry
3. **Session Tracking**: Use consistent session IDs across requests
4. **Error Handling**: Implement comprehensive error handling
5. **Testing**: Test locally before deploying to AgentCore
6. **Monitoring**: Set up CloudWatch alarms for production

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check AWS credentials
   - Ensure Docker is running (for container build)
   - Verify IAM permissions

2. **MCP Server Not Responding**
   - Check server is listening on 0.0.0.0:8000
   - Verify stateless_http=True
   - Check CloudWatch logs

3. **Authentication Errors**
   - Verify Cognito user pool
   - Check JWT token in requests
   - Validate IAM roles

## Resources

- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [AgentCore CLI Reference](https://aws.github.io/bedrock-agentcore-starter-toolkit/api-reference/cli.html)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/blazickjp/FastMCP)