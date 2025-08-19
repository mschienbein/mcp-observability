# LibreChat AWS CDK Deployment

## Overview

This CDK stack deploys a fully functional LibreChat instance on AWS ECS Fargate with all required services:

- **LibreChat API**: Main application server
- **MongoDB**: Document database for user data and conversations
- **Meilisearch**: Full-text search engine
- **PostgreSQL with pgvector**: Vector database for RAG functionality
- **RAG API**: Retrieval-Augmented Generation API for enhanced AI capabilities

## Architecture

```
Internet → ALB → LibreChat API (ECS Fargate)
                      ↓
        ┌─────────────┼─────────────┬──────────────┐
        ↓             ↓             ↓              ↓
    MongoDB      Meilisearch    VectorDB      RAG API
    (ECS)          (ECS)         (ECS)         (ECS)
```

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CDK CLI installed
3. Docker (for local testing)
4. API Keys for AI providers (OpenAI, Anthropic, etc.)

## Deployment

### 1. Set Environment Variables

```bash
export CDK_DEFAULT_ACCOUNT=your-aws-account-id
export CDK_DEFAULT_REGION=us-east-1
export AWS_PROFILE=your-aws-profile
```

### 2. Bootstrap CDK (if not already done)

```bash
cd infra-cdk
npx -y aws-cdk@^2 bootstrap --qualifier mcpobs
```

### 3. Deploy the Stack

```bash
# Deploy LibreChat stack
npx -y aws-cdk@^2 deploy LibreChatStack --require-approval never

# Or deploy both Langfuse and LibreChat
npx -y aws-cdk@^2 deploy --all --require-approval never
```

### 4. Configure API Keys

After deployment, update the secrets in AWS Secrets Manager with your actual API keys:

1. Go to AWS Secrets Manager
2. Find `LibreChatStack-LibreChatSecrets*`
3. Update with your actual values:
   - Add OpenAI API key
   - Add Anthropic API key
   - Update JWT secrets
   - Update encryption keys

### 5. Create librechat.yaml Configuration

Create a configuration file to customize LibreChat endpoints and features:

```yaml
# librechat.yaml
version: 1.0.3
cache: true
endpoints:
  openAI:
    title: OpenAI
    apiKey: ${OPENAI_API_KEY}
    models:
      default: ["gpt-4", "gpt-3.5-turbo"]
  anthropic:
    title: Anthropic
    apiKey: ${ANTHROPIC_API_KEY}
    models:
      default: ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
  custom:
    - name: "Custom Model"
      apiKey: ${CUSTOM_API_KEY}
      baseURL: "https://api.custom.com/v1"
      models:
        default: ["custom-model"]
```

Upload this to the ECS task or use AWS Systems Manager Parameter Store.

## Services Details

### MongoDB
- **Purpose**: Stores user data, conversations, and settings
- **Access**: Internal only via service discovery
- **Persistence**: EFS volume mount at `/data/db`

### Meilisearch
- **Purpose**: Provides fast full-text search across conversations
- **Access**: Internal only, accessed by LibreChat API
- **Master Key**: Stored in AWS Secrets Manager

### PostgreSQL with pgvector
- **Purpose**: Vector database for RAG functionality
- **Extension**: pgvector for similarity search
- **Persistence**: EFS volume mount

### RAG API
- **Purpose**: Handles document processing and retrieval for RAG
- **Features**: Document upload, embedding, similarity search
- **Integration**: Works with vector database

## Security Considerations

1. **Network Security**:
   - All services except ALB are in private subnets
   - Inter-service communication via service discovery
   - Security groups restrict access appropriately

2. **Secrets Management**:
   - All sensitive data in AWS Secrets Manager
   - Automatic rotation can be configured

3. **Data Persistence**:
   - EFS for shared file storage
   - Encrypted at rest and in transit

4. **Authentication**:
   - JWT-based authentication
   - Session management with configurable expiry

## Monitoring

1. **CloudWatch Logs**:
   - Each service has its own log group
   - Retention set to 1 week (configurable)

2. **Container Insights**:
   - Enabled on ECS cluster
   - Metrics for CPU, memory, network

3. **Health Checks**:
   - ALB health checks on `/health` endpoint
   - ECS service health monitoring

## Cost Optimization

1. **Fargate Spot** (optional):
   - Can use Spot instances for non-critical services
   - MongoDB and VectorDB should use on-demand

2. **Auto-scaling**:
   - Configure based on CPU/memory metrics
   - Scale down during off-hours

3. **EFS Lifecycle**:
   - Moves infrequent files to IA storage class after 30 days

## Troubleshooting

### Service Won't Start
- Check CloudWatch logs for the specific service
- Verify secrets are properly configured
- Ensure security groups allow inter-service communication

### Database Connection Issues
- Verify service discovery is working
- Check that MongoDB is running without auth (or configure auth)
- Ensure network connectivity between services

### Search Not Working
- Verify Meilisearch master key is set
- Check Meilisearch logs for indexing issues
- Ensure LibreChat can reach Meilisearch service

### RAG Features Not Available
- Verify RAG API and VectorDB are running
- Check PostgreSQL has pgvector extension
- Ensure proper environment variables are set

## Cleanup

To remove all resources:

```bash
npx -y aws-cdk@^2 destroy LibreChatStack
```

Note: EFS and S3 buckets are retained by default to prevent data loss.

## Additional Resources

- [LibreChat Documentation](https://www.librechat.ai/docs)
- [LibreChat GitHub](https://github.com/danny-avila/LibreChat)
- [Configuration Guide](https://www.librechat.ai/docs/configuration)
- [Docker Compose Reference](https://github.com/danny-avila/LibreChat/blob/main/deploy-compose.yml)