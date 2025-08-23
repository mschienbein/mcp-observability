# MCP Chat UI

A modern chat interface that integrates with MCP (Model Context Protocol) servers and AWS Bedrock for LLM capabilities. Built with Next.js 15, TypeScript, and Tailwind CSS.

## Features

- 🤖 **AWS Bedrock Integration** - Support for Claude, Llama, and Amazon Nova models
- 🔧 **MCP Server Support** - Connect to multiple MCP servers for tool execution
- 🎨 **MCP-UI SDK Integration** - Rich UI resource rendering from MCP servers
- 💬 **Streaming Responses** - Real-time token-by-token output
- 🔄 **Dynamic Server Management** - Add, remove, and configure MCP servers on the fly
- 📊 **Observability** - Optional Langfuse integration for tracing
- 🐳 **Docker Ready** - Production-ready containerization
- ☁️ **AWS CDK Deployment** - Infrastructure as code for AWS deployment

## Quick Start

### Prerequisites

- Node.js 20+
- AWS Account with Bedrock access
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone and install dependencies:**
```bash
cd mcp-chat-ui
npm install
```

2. **Configure environment variables:**
```bash
cp .env.local.example .env.local
# Edit .env.local with your AWS credentials and MCP server configurations
```

3. **Start the development server:**
```bash
npm run dev
```

4. **Open http://localhost:3000**

### Docker Deployment

1. **Build the Docker image:**
```bash
docker build -t mcp-chat-ui .
```

2. **Run with docker-compose:**
```bash
docker-compose up
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_REGION` | AWS region for Bedrock | Yes |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |
| `MCP_SERVERS` | JSON array of MCP server configs | No |
| `DEFAULT_MODEL` | Default Bedrock model ID | No |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key for observability | No |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | No |
| `LANGFUSE_HOST` | Langfuse host URL | No |

### MCP Server Configuration

MCP servers can be configured via the `MCP_SERVERS` environment variable:

```json
[
  {
    "id": "my-server",
    "name": "My MCP Server",
    "transport": "http",
    "url": "https://my-mcp-server.com",
    "enabled": true,
    "headers": {
      "Authorization": "Bearer token"
    }
  }
]
```

## Supported Models

The application supports the following AWS Bedrock models:

- **Claude 3 Sonnet** - Balanced performance
- **Claude 3 Haiku** - Fast and efficient
- **Claude 3.5 Sonnet** - Most capable
- **Llama 3.1 70B** - Open source alternative
- **Amazon Nova Pro** - AWS native model

## Architecture

```
mcp-chat-ui/
├── app/                  # Next.js app directory
│   ├── api/             # API routes
│   │   ├── chat/        # Chat endpoint with Bedrock
│   │   └── mcp/         # MCP server management
│   └── page.tsx         # Main chat page
├── components/          # React components
│   ├── chat/           # Chat UI components
│   ├── mcp/            # MCP-specific components
│   └── ui/             # Reusable UI components
├── lib/                # Core libraries
│   ├── mcp/            # MCP client and handlers
│   └── utils/          # Utility functions
└── public/             # Static assets
```

## Development

### Running Tests
```bash
npm test
```

### Building for Production
```bash
npm run build
```

### Linting
```bash
npm run lint
```

## Deployment

### AWS CDK Deployment

See the parent project's CDK stack for deploying this application to AWS ECS Fargate.

### Manual Docker Deployment

1. Build the image:
```bash
docker build -t mcp-chat-ui:latest .
```

2. Push to your registry:
```bash
docker tag mcp-chat-ui:latest your-registry/mcp-chat-ui:latest
docker push your-registry/mcp-chat-ui:latest
```

3. Deploy to your container platform of choice (ECS, EKS, etc.)

## Connecting to MCP Servers

### Local MCP Servers

To connect to local MCP servers from the parent project:

1. Start the MCP servers:
```bash
# Terminal 1 - Tools Server
cd .. && uv run python -m mcp.tools_server.main

# Terminal 2 - Feedback Server  
cd .. && uv run python -m mcp.feedback_server.main
```

2. In the MCP Chat UI, click "MCP Servers" and enable the local servers

### AgentCore MCP Server

To connect to the deployed AgentCore MCP server:

1. Get the AgentCore endpoint URL and JWT token from your deployment
2. Add the server configuration in the UI or via environment variables
3. The server will automatically connect and expose available tools

## Troubleshooting

### AWS Credentials Issues
- Ensure your AWS credentials have access to Bedrock
- Check the AWS region supports your selected models

### MCP Connection Failures
- Verify the MCP server URL is accessible
- Check authentication headers are correct
- Ensure CORS is configured on the MCP server

### Build Errors
- Clear `.next` folder and rebuild: `rm -rf .next && npm run build`
- Update dependencies: `npm update`

## Contributing

Contributions are welcome! Please follow the existing code style and add tests for new features.

## License

See LICENSE file in the parent repository.