# LibreChat Deployment Guide

This guide covers deploying LibreChat self-hosted AI chat interface on AWS using CDK.

## Overview

LibreChat is an open-source AI chat application that supports multiple AI providers including OpenAI, Anthropic, Google, and AWS Bedrock. This CDK stack deploys a production-ready LibreChat instance on AWS.

## Stack Components

- **Stack Definition**: `stacks/librechat_stack.py`
- **Configuration Files**: `configs/librechat/`
- **Setup Scripts**: `scripts/setup/`

## Architecture

The stack provisions:

- **VPC**: 2 AZs with NAT gateway for private subnet internet access
- **ECS Cluster**: Container orchestration with CloudMap service discovery
- **MongoDB**: Document database for chat data and user management
- **Meilisearch**: Fast search engine for conversation search
- **LibreChat API**: Main application service behind ALB
- **S3 Bucket**: File upload storage
- **CloudFront**: HTTPS distribution for secure access
- **Secrets Manager**: Secure storage for API keys and secrets

## Services

### MongoDB Service
- ECS Fargate task (2GB RAM, 1 vCPU)
- Service discovery: `mongodb.librechat.local:27017`
- No authentication in demo mode (configure for production)

### Meilisearch Service
- ECS Fargate task (1GB RAM, 0.5 vCPU)
- Service discovery: `meilisearch.librechat.local:7700`
- Master key stored in Secrets Manager

### LibreChat API Service
- ECS Fargate task (4GB RAM, 2 vCPU)
- Application Load Balancer for HTTP access
- CloudFront distribution for HTTPS
- Health check endpoint: `/health`

## Configuration

### Environment Variables
Key environment variables configured in the stack:
- `ENDPOINTS`: Enabled AI providers (openAI, anthropic, google, azureOpenAI)
- `ALLOW_REGISTRATION`: User registration enabled
- `SESSION_EXPIRY`: 15 minutes (900000ms)
- `FILE_UPLOAD_SIZE_LIMIT`: 10MB

### Encryption Keys
The stack generates secure encryption keys:
- `CREDS_KEY`: 64-character hex string for credential encryption
- `CREDS_IV`: 32-character hex string for initialization vector
- `JWT_SECRET` & `JWT_REFRESH_SECRET`: JWT token signing

### API Keys
Users can provide their own API keys through the UI:
- OpenAI API Key
- Anthropic API Key
- Google AI API Key
- Azure OpenAI credentials

For AWS Bedrock, use IAM role permissions (no API key needed).

## Deployment

### Prerequisites
1. AWS CLI configured with appropriate credentials
2. CDK bootstrapped: `cdk bootstrap --qualifier mcpobs`
3. Python dependencies installed: `pip install -r requirements.txt`

### Deploy Stack
```bash
cdk deploy LibreChatStack
```

### Post-Deployment Setup

#### Enable AWS Bedrock
```bash
./scripts/setup/enable-bedrock.sh
```

#### Configure API Keys (Optional)
```bash
./scripts/setup/setup-librechat-secrets.sh
```

## Access URLs

After deployment, access LibreChat via:
- **HTTP**: ALB URL (output as `LibreChatHTTP`)
- **HTTPS**: CloudFront URL (output as `LibreChatHTTPS`)

## Configuration Files

### librechat.yaml
Main configuration file for endpoints, models, and features. Located in `configs/librechat/`.

### librechat-minimal.yaml
Simplified configuration for basic setup with user-provided API keys.

## Security Considerations

1. **Production Deployment**:
   - Enable MongoDB authentication
   - Use strong encryption keys (not the demo values)
   - Configure proper CORS and domain settings
   - Enable AWS WAF on CloudFront

2. **API Key Management**:
   - Store API keys in AWS Secrets Manager
   - Use IAM roles for AWS services (Bedrock, S3)
   - Rotate keys regularly

3. **Network Security**:
   - Services run in private subnets
   - Security groups restrict inter-service communication
   - ALB handles public traffic

## Monitoring

- CloudWatch Logs: All services log to CloudWatch
- ECS Container Insights: Enabled for cluster monitoring
- ALB metrics: Request count, latency, errors

## Scaling

The stack uses Fargate with auto-scaling capabilities:
- Adjust `desired_count` for service replicas
- Configure auto-scaling policies based on CPU/memory
- MongoDB and Meilisearch can be scaled independently

## Troubleshooting

### Common Issues

1. **Service fails to start**: Check CloudWatch logs for the specific service
2. **"Invalid key length" error**: Ensure encryption keys are proper length (64/32 hex chars)
3. **API key errors**: Verify keys are correctly configured in Secrets Manager
4. **MongoDB connection issues**: Check service discovery and security groups

### Useful Commands
```bash
# View service logs
aws logs tail /ecs/librechat --follow

# Check service status
aws ecs describe-services --cluster LibreChatStack-LibreChatCluster --services librechat-api

# Update service
aws ecs update-service --cluster LibreChatStack-LibreChatCluster --service librechat-api --force-new-deployment
```

## Cost Optimization

- Use Fargate Spot for non-critical workloads
- Consider Reserved Instances for predictable usage
- Implement S3 lifecycle policies for uploads
- Use CloudFront caching where appropriate

## Support

For issues or questions:
- Check CloudWatch Logs for error details
- Review LibreChat documentation: https://www.librechat.ai/docs
- GitHub Issues: https://github.com/danny-avila/LibreChat