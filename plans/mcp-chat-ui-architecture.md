# MCP Chat UI with AWS Bedrock - Architecture Plan

## Executive Summary

This document outlines the architecture and implementation plan for building a production-ready chat interface that integrates Model Context Protocol (MCP) servers with AWS Bedrock LLM services. The solution will provide a modern, scalable chat application with support for MCP tools, rich UI resources, and streaming responses.

## Project Overview

### Goals
1. Create a web-based chat interface that connects to MCP servers
2. Integrate AWS Bedrock for LLM capabilities (Claude, Llama, Nova)
3. Support MCP UI resources rendering using `@mcp-ui/client`
4. Deploy on AWS using CDK for infrastructure as code
5. Enable observability with existing Langfuse setup

### Key Features
- **MCP Server Integration**: Connect to multiple MCP servers (HTTP/SSE/stdio)
- **LLM Streaming**: Real-time streaming responses from AWS Bedrock
- **Rich UI Rendering**: Support for HTML, Remote DOM, and external URLs
- **Tool Execution**: Execute MCP tools and display results inline
- **Production Deployment**: AWS ECS Fargate with auto-scaling

## Technical Stack

### Frontend
- **Framework**: Next.js 15.4+ with App Router
- **UI Library**: shadcn/ui components with Radix UI
- **Styling**: Tailwind CSS v4
- **State Management**: React hooks + Tanstack Query
- **MCP Client**: `@modelcontextprotocol/sdk`
- **UI Rendering**: `@mcp-ui/client` for MCP resources

### Backend
- **Runtime**: Node.js 20+
- **API Routes**: Next.js API routes
- **LLM Provider**: AWS Bedrock via `@ai-sdk/amazon-bedrock`
- **Streaming**: Vercel AI SDK for streaming responses
- **Database** (optional): PostgreSQL with Drizzle ORM

### Infrastructure
- **Container**: Docker with multi-stage builds
- **Compute**: AWS ECS Fargate
- **Load Balancer**: Application Load Balancer (ALB)
- **CDN**: CloudFront (optional)
- **Secrets**: AWS Secrets Manager
- **Monitoring**: CloudWatch + X-Ray

## Architecture Diagram

```mermaid
graph TB
    subgraph "Client Browser"
        UI[Next.js Chat UI]
        MCP_UI[MCP UI Renderer]
    end
    
    subgraph "AWS Infrastructure"
        subgraph "ECS Fargate"
            APP[Next.js App]
            API[API Routes]
        end
        
        ALB[Application Load Balancer]
        
        subgraph "AWS Services"
            BEDROCK[AWS Bedrock]
            SECRETS[Secrets Manager]
            CW[CloudWatch]
        end
    end
    
    subgraph "MCP Servers"
        AGENTCORE[AgentCore Runtime]
        LOCAL[Local MCP Servers]
        REMOTE[Remote MCP Servers]
    end
    
    UI --> ALB
    ALB --> APP
    APP --> API
    API --> BEDROCK
    API --> SECRETS
    API --> AGENTCORE
    API --> LOCAL
    API --> REMOTE
    APP --> CW
    MCP_UI --> UI
```

## Implementation Plan

### Phase 1: Local Development Setup
1. Fork/clone Scira MCP Chat repository
2. Add AWS Bedrock integration
3. Integrate MCP-UI SDK
4. Test with local MCP servers
5. Connect to deployed AgentCore server

### Phase 2: Core Features
1. Implement MCP server management UI
2. Add tool execution display
3. Integrate UI resource rendering
4. Add streaming response handling
5. Implement error handling and retry logic

### Phase 3: AWS Integration
1. Configure AWS Bedrock provider
2. Set up authentication (Cognito)
3. Implement secrets management
4. Add CloudWatch logging
5. Integrate with Langfuse observability

### Phase 4: Production Deployment
1. Create Docker container
2. Build CDK stack
3. Configure auto-scaling
4. Set up monitoring alerts
5. Implement CI/CD pipeline

## Directory Structure

```
mcp-chat-ui/
├── app/
│   ├── api/
│   │   ├── chat/
│   │   │   └── route.ts         # Chat API endpoint
│   │   └── mcp/
│   │       └── route.ts         # MCP server management
│   ├── chat/
│   │   └── [id]/
│   │       └── page.tsx         # Chat interface
│   └── layout.tsx
├── components/
│   ├── chat/
│   │   ├── chat-interface.tsx
│   │   ├── message-list.tsx
│   │   └── input-form.tsx
│   ├── mcp/
│   │   ├── server-config.tsx
│   │   ├── tool-display.tsx
│   │   └── ui-resource-renderer.tsx
│   └── ui/                      # shadcn components
├── lib/
│   ├── mcp/
│   │   ├── client.ts           # MCP client wrapper
│   │   ├── handler.ts          # Tool execution handler
│   │   └── config.ts           # Server configurations
│   ├── bedrock/
│   │   └── client.ts           # Bedrock integration
│   └── utils.ts
├── infra-cdk/
│   ├── stacks/
│   │   └── mcp-chat-stack.ts   # CDK stack definition
│   ├── app.ts
│   └── cdk.json
├── docker/
│   └── Dockerfile
└── package.json
```

## Key Components

### 1. Chat API Route
```typescript
// app/api/chat/route.ts
import { streamText } from 'ai';
import { bedrock } from '@ai-sdk/amazon-bedrock';
import { MCPToolHandler } from '@/lib/mcp/handler';

export async function POST(req: Request) {
  const { messages, mcpServers, model } = await req.json();
  
  // Initialize MCP connections
  const mcpHandler = new MCPToolHandler(mcpServers);
  const mcpTools = await mcpHandler.getTools();
  
  // Stream response from Bedrock
  const result = streamText({
    model: bedrock(model || 'anthropic.claude-3-sonnet-20240229-v1:0'),
    messages,
    tools: mcpTools,
    system: 'You are a helpful assistant with access to MCP tools.',
    onToolCall: async ({ toolCall }) => {
      return await mcpHandler.executeTool(toolCall);
    }
  });
  
  return result.toDataStreamResponse();
}
```

### 2. MCP Client Wrapper
```typescript
// lib/mcp/client.ts
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';

export class MCPClient {
  private clients: Map<string, Client> = new Map();
  
  async connect(server: MCPServerConfig) {
    const transport = this.createTransport(server);
    const client = new Client({
      name: 'mcp-chat-ui',
      version: '1.0.0'
    }, {
      capabilities: {}
    });
    
    await client.connect(transport);
    this.clients.set(server.id, client);
    
    return client;
  }
  
  private createTransport(server: MCPServerConfig) {
    switch (server.transport) {
      case 'stdio':
        return new StdioClientTransport({
          command: server.command,
          args: server.args
        });
      case 'sse':
        return new SSEClientTransport(server.url);
      case 'http':
        return new HTTPClientTransport(server.url, server.headers);
      default:
        throw new Error(`Unsupported transport: ${server.transport}`);
    }
  }
}
```

### 3. UI Resource Renderer
```typescript
// components/mcp/ui-resource-renderer.tsx
import { UIResourceRenderer } from '@mcp-ui/client';

interface Props {
  resource: any;
  onAction: (action: any) => void;
}

export function MCPResourceDisplay({ resource, onAction }: Props) {
  if (!resource?.uri?.startsWith('ui://')) {
    return null;
  }
  
  return (
    <div className="my-4 rounded-lg border p-4">
      <UIResourceRenderer
        resource={resource}
        onUIAction={onAction}
        htmlProps={{
          autoResizeIframe: true,
          style: { 
            maxHeight: '500px',
            width: '100%'
          },
          iframeProps: {
            sandbox: 'allow-scripts allow-same-origin',
            className: 'rounded-md'
          }
        }}
        supportedContentTypes={['rawHtml', 'externalUrl', 'remoteDom']}
      />
    </div>
  );
}
```

## Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_MAX_TOKENS=4096

# MCP Server Configurations
MCP_AGENTCORE_URL=https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/...
MCP_AGENTCORE_TOKEN=your-cognito-access-token

# Database (optional)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Observability
LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxx
LANGFUSE_HOST=https://your-langfuse-instance.com

# App Configuration
NEXT_PUBLIC_APP_URL=https://chat.yourdomain.com
```

## CDK Stack Configuration

```typescript
// infra-cdk/stacks/mcp-chat-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export class MCPChatStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // VPC Configuration
    const vpc = new ec2.Vpc(this, 'ChatVPC', {
      maxAzs: 2,
      natGateways: 1
    });
    
    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'ChatCluster', {
      vpc,
      containerInsights: true,
      clusterName: 'mcp-chat-cluster'
    });
    
    // Task Role with Bedrock permissions
    const taskRole = new iam.Role(this, 'TaskRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      inlinePolicies: {
        BedrockAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
              resources: ['*']
            })
          ]
        })
      }
    });
    
    // Task Definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'ChatTask', {
      memoryLimitMiB: 2048,
      cpu: 1024,
      taskRole
    });
    
    // Container
    const container = taskDefinition.addContainer('chat-app', {
      image: ecs.ContainerImage.fromAsset('../', {
        file: 'docker/Dockerfile'
      }),
      environment: {
        NODE_ENV: 'production',
        AWS_REGION: this.region
      },
      secrets: {
        // Pull secrets from AWS Secrets Manager
        DATABASE_URL: ecs.Secret.fromSecretsManager(dbSecret),
        LANGFUSE_SECRET_KEY: ecs.Secret.fromSecretsManager(langfuseSecret, 'secret_key')
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'mcp-chat',
        logRetention: 30
      })
    });
    
    container.addPortMappings({
      containerPort: 3000,
      protocol: ecs.Protocol.TCP
    });
    
    // Fargate Service
    const service = new ecs.FargateService(this, 'ChatService', {
      cluster,
      taskDefinition,
      desiredCount: 2,
      assignPublicIp: false,
      serviceName: 'mcp-chat-service'
    });
    
    // Auto Scaling
    const scaling = service.autoScaleTaskCount({
      minCapacity: 1,
      maxCapacity: 10
    });
    
    scaling.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 70
    });
    
    // Load Balancer
    const lb = new elbv2.ApplicationLoadBalancer(this, 'ChatALB', {
      vpc,
      internetFacing: true,
      loadBalancerName: 'mcp-chat-alb'
    });
    
    const listener = lb.addListener('Listener', {
      port: 443,
      certificates: [certificate],
      protocol: elbv2.ApplicationProtocol.HTTPS
    });
    
    listener.addTargets('ChatTarget', {
      port: 3000,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [service],
      healthCheck: {
        path: '/api/health',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3
      }
    });
    
    // Outputs
    new cdk.CfnOutput(this, 'LoadBalancerDNS', {
      value: lb.loadBalancerDnsName,
      description: 'Load balancer DNS name'
    });
  }
}
```

## Security Considerations

### Authentication & Authorization
- AWS Cognito for user authentication
- JWT tokens for session management
- API key rotation for MCP servers
- Role-based access control (RBAC)

### Network Security
- VPC with private subnets for ECS tasks
- Security groups with least privilege
- WAF rules for DDoS protection
- TLS 1.3 for all communications

### Data Security
- Encryption at rest for database
- Secrets in AWS Secrets Manager
- Environment variable validation
- Input sanitization

### UI Security
- Iframe sandboxing for MCP UI resources
- Content Security Policy (CSP) headers
- XSS protection
- CORS configuration

## Monitoring & Observability

### Metrics
- CloudWatch metrics for ECS tasks
- Custom metrics for:
  - Chat sessions
  - Tool executions
  - Response times
  - Token usage

### Logging
- Structured logging with JSON
- CloudWatch Logs integration
- Log aggregation and search
- Error tracking

### Tracing
- AWS X-Ray for distributed tracing
- Langfuse integration for LLM observability
- MCP tool execution tracking
- Performance monitoring

### Alerts
- High error rate
- Low availability
- High latency
- Resource exhaustion

## Testing Strategy

### Unit Tests
- Component testing with React Testing Library
- API route testing
- MCP client mocking
- Utility function tests

### Integration Tests
- MCP server connection tests
- Bedrock API integration
- Database operations
- Authentication flow

### E2E Tests
- User journey testing
- Tool execution flows
- UI resource rendering
- Error scenarios

### Performance Tests
- Load testing with k6
- Streaming performance
- Concurrent user handling
- Memory leak detection

## Deployment Process

### Local Development
```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env.local

# Run development server
npm run dev
```

### Docker Build
```bash
# Build image
docker build -t mcp-chat-ui .

# Run locally
docker run -p 3000:3000 --env-file .env mcp-chat-ui
```

### CDK Deployment
```bash
# Install CDK
npm install -g aws-cdk

# Bootstrap (first time)
cd infra-cdk
cdk bootstrap

# Deploy
cdk deploy MCPChatStack
```

## Cost Estimation

### Monthly Costs (estimated)
- ECS Fargate: $50-100 (2 tasks, 1vCPU, 2GB RAM)
- ALB: $25
- CloudWatch: $10-20
- Secrets Manager: $5
- Data Transfer: $10-50
- **Total**: ~$100-200/month

### Cost Optimization
- Use Fargate Spot for dev/staging
- Implement request caching
- Optimize container size
- Use CloudFront for static assets

## Timeline

### Week 1-2: Foundation
- Set up development environment
- Integrate core dependencies
- Basic chat interface
- Local MCP server connection

### Week 3-4: Features
- Bedrock integration
- MCP UI resource rendering
- Tool execution display
- Error handling

### Week 5-6: Production
- Docker containerization
- CDK stack creation
- Security implementation
- Monitoring setup

### Week 7-8: Polish
- Performance optimization
- Testing suite
- Documentation
- Deployment automation

## Success Criteria

1. **Functional Requirements**
   - Successfully connect to MCP servers
   - Stream responses from AWS Bedrock
   - Render MCP UI resources
   - Execute tools and display results

2. **Performance Requirements**
   - < 2s initial response time
   - Smooth streaming without lag
   - Handle 100+ concurrent users
   - 99.9% uptime

3. **Security Requirements**
   - Pass security audit
   - No critical vulnerabilities
   - Secure secret management
   - Proper authentication

4. **User Experience**
   - Intuitive interface
   - Mobile responsive
   - Accessible (WCAG 2.1 AA)
   - Fast load times

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| MCP server compatibility | High | Test with multiple server types |
| Bedrock rate limits | Medium | Implement retry logic and caching |
| UI resource security | High | Strict sandboxing and CSP |
| Cost overruns | Medium | Set up billing alerts and auto-scaling limits |
| Performance issues | Medium | Implement caching and CDN |

## Next Steps

1. **Immediate Actions**
   - Create project repository
   - Set up development environment
   - Configure AWS credentials
   - Start with basic chat interface

2. **Short Term**
   - Implement MCP client
   - Add Bedrock integration
   - Create Docker container
   - Deploy to staging

3. **Long Term**
   - Add advanced features
   - Optimize performance
   - Expand MCP server support
   - Build user management

## Appendix

### References
- [MCP Specification](https://modelcontextprotocol.io)
- [Vercel AI SDK](https://sdk.vercel.ai)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock)
- [MCP-UI SDK](https://github.com/idosal/mcp-ui)
- [Scira MCP Chat](https://github.com/zaidmukaddam/scira-mcp-chat)

### Glossary
- **MCP**: Model Context Protocol
- **LLM**: Large Language Model
- **CDK**: Cloud Development Kit
- **ECS**: Elastic Container Service
- **ALB**: Application Load Balancer

---

Document Version: 1.0
Last Updated: 2024-12-19
Author: MCP Observability Team