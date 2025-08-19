# Infrastructure as Code (CDK)

This directory contains AWS CDK infrastructure definitions for deploying observability and chat services.

## Directory Structure

```
infra-cdk/
├── stacks/              # CDK stack definitions
│   ├── langfuse_stack.py    # Langfuse observability platform
│   ├── librechat_stack.py   # LibreChat AI interface
│   └── cloudfront_addon.py  # CloudFront distribution helper
│
├── configs/             # Configuration files
│   ├── langfuse/           # Langfuse-specific configs
│   └── librechat/          # LibreChat YAML configs
│       ├── librechat.yaml
│       ├── librechat-config.yaml
│       └── librechat-minimal.yaml
│
├── scripts/             # Automation scripts
│   ├── setup/              # Deployment and setup scripts
│   │   ├── enable-bedrock.sh
│   │   ├── setup-librechat-secrets.sh
│   │   ├── test_librechat.sh
│   │   ├── provision_clickhouse_ec2.sh
│   │   └── setup_clickhouse_complete.sh
│   └── database/           # Database schemas
│       ├── create_clickhouse_schema.sql
│       └── langfuse_official_clickhouse_schema.sql
│
├── docs/                # Documentation
│   ├── CDK_README.md       # CDK setup instructions
│   ├── CLICKHOUSE_SCHEMA.md
│   └── LIBRECHAT_README.md
│
├── app.py               # Main CDK application
├── requirements.txt     # Python dependencies
├── cdk.json            # CDK configuration
└── cdk.out/            # CDK synthesis output (generated)
```

## Quick Start

### Prerequisites
- AWS CLI configured
- Node.js 18+ and npm
- Python 3.10+
- AWS CDK CLI: `npm install -g aws-cdk`

### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap --qualifier mcpobs
```

### Deployment

#### Deploy Langfuse Observability
```bash
cdk deploy LangfuseStack
```

#### Deploy LibreChat
```bash
cdk deploy LibreChatStack
```

#### Deploy All Stacks
```bash
cdk deploy --all
```

### Configuration

#### Langfuse
- ClickHouse database for analytics
- ECS Fargate for web and worker services
- RDS PostgreSQL for metadata
- ElastiCache Redis for caching

#### LibreChat
- MongoDB for data storage
- Meilisearch for search functionality
- Support for multiple AI providers (OpenAI, Anthropic, Bedrock)
- CloudFront for HTTPS

### Scripts

#### Enable AWS Bedrock
```bash
./scripts/setup/enable-bedrock.sh
```

#### Configure API Keys
```bash
./scripts/setup/setup-librechat-secrets.sh
```

#### Setup ClickHouse Schema
```bash
# Run on ClickHouse instance
./scripts/setup/setup_clickhouse_complete.sh
```

### Useful Commands
- `cdk ls` - List all stacks
- `cdk synth` - Synthesize CloudFormation templates
- `cdk diff` - Compare deployed stack with current state
- `cdk destroy` - Remove deployed stack

### Environment Variables
Create a `.env` file in the project root:
```bash
AWS_REGION=us-east-1
AWS_PROFILE=your-profile
```

### Support
See documentation in the `docs/` folder for detailed setup and troubleshooting guides.