# Langfuse AWS CDK Stack

This folder provisions a minimal, self-hosted Langfuse on AWS using managed services:

- VPC with 2 AZs and 1 NAT
- ECS Fargate services
  - Web service behind an Application Load Balancer (ALB)
  - Worker service (no ALB)
- RDS PostgreSQL (engine 15) for Langfuse metadata
- ElastiCache Redis (single-node) for queue/cache
- AWS Secrets Manager for app secrets and DB credentials
- Security Groups to allow ECS tasks to access RDS (5432) and Redis (6379)

This stack is v3-ready: it provisions an S3 bucket for event uploads and ClickHouse secret placeholders to be populated post-deploy.

Current implementation paths:
- Stack: `infra-cdk/langfuse_stack.py`
- App entrypoint: `infra-cdk/app.py`


## Architecture summary

- `Vpc` → `Cluster` (ECS)
- `DatabaseInstance` (PostgreSQL 15) with generated password secret
- `CfnSubnetGroup` + `CfnCacheCluster` (Redis, single t3.micro)
- `ApplicationLoadBalancedFargateService` (web) with health check `/api/health`
- `FargateService` (worker)
- `S3 Bucket` for Langfuse v3 event uploads
- Secrets created:
  - `LangfuseDbPassword` (generated)
  - `NextAuthSecret` (generated)
  - `SaltSecret` (generated)
  - `EncryptionKeySecret` (demo 64 hex chars; replace for prod)
  - `ClickhouseUrl`, `ClickhouseUser`, `ClickhousePassword`, `ClickhouseMigrationUrl` (placeholders)
  - `ClickhouseDb` (default: `default`), `ClickhouseMigrationSsl` (default: `true`)

Outputs:
- `AlbUrl` → ALB HTTP URL for the web UI
- `EventsBucketName` → S3 bucket for event uploads
- `ClickhouseUrlSecretName`, `ClickhouseUserSecretName`, `ClickhousePasswordSecretName`, `ClickhouseMigrationUrlSecretName`
- `ClickhouseDbSecretName`, `ClickhouseMigrationSslSecretName`
- `ClusterName`, `WebServiceName`, `WorkerServiceName`

### Architecture diagram

```mermaid
flowchart TB
  internet[Internet] --> alb[Application Load Balancer]
  alb --> web[Langfuse Web (ECS Fargate)]

  subgraph VPC
    direction TB
    subgraph Public_Subnets ["Public Subnets"]
      alb
      nat[NAT Gateway]
    end
    subgraph Private_Subnets ["Private Subnets"]
      web
      worker[Langfuse Worker (ECS Fargate)]
      rds[(RDS PostgreSQL)]
      redis[(ElastiCache Redis)]
    end
  end

  web --- rds
  web --- redis
  worker --- rds
  worker --- redis
  web --- s3[(S3 Events Bucket)]
  worker --- s3

  secrets[AWS Secrets Manager] --> web
  secrets --> worker

  classDef svc fill:#e6f4ff,stroke:#6ea8fe,color:#003366
  classDef data fill:#f8f0ff,stroke:#b98aff,color:#3b235a
  class web,worker svc
  class rds,redis,s3 data
```

## Container configuration (env & secrets)

Web container (`langfuse/langfuse:latest`):
- Env:
  - `REDIS_CONNECTION_STRING` (redis://host:port)
  - `LANGFUSE_TRACING_ENVIRONMENT=prod`
  - `NODE_OPTIONS=--max-old-space-size=3072`
  - `NEXTAUTH_URL` set post-creation to `http://<ALB DNS>`
  - `LANGFUSE_S3_EVENT_UPLOAD_BUCKET` (stack output value)
  - `LANGFUSE_S3_EVENT_UPLOAD_REGION` (stack region)
  - `LANGFUSE_S3_EVENT_UPLOAD_PREFIX=events/`
  - `CLICKHOUSE_CLUSTER_ENABLED=false` (default)
- Secrets (injected as env):
  - `DATABASE_URL` (stored in `LangfuseDbUrl`)
  - `NEXTAUTH_SECRET`, `SALT`, `ENCRYPTION_KEY`
  - `CLICKHOUSE_URL`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_MIGRATION_URL`, `CLICKHOUSE_DB`, `CLICKHOUSE_MIGRATION_SSL`

Worker container (`langfuse/langfuse-worker:latest`):
- Env:
  - `REDIS_CONNECTION_STRING`
  - `LANGFUSE_TRACING_ENVIRONMENT=prod`
  - `NODE_OPTIONS=--max-old-space-size=3072`
  - `LANGFUSE_S3_EVENT_UPLOAD_BUCKET`, `LANGFUSE_S3_EVENT_UPLOAD_REGION`, `LANGFUSE_S3_EVENT_UPLOAD_PREFIX=events/`
  - `CLICKHOUSE_CLUSTER_ENABLED=false`
- Secrets:
  - `DATABASE_URL`, `NEXTAUTH_SECRET`, `SALT`, `ENCRYPTION_KEY`
  - `CLICKHOUSE_URL`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_MIGRATION_URL`, `CLICKHOUSE_DB`, `CLICKHOUSE_MIGRATION_SSL`

Important: `EncryptionKeySecret` is a placeholder and must be replaced for production.

## Prerequisites

- AWS account with credentials configured. Recommended: set your profile and region
  - `export AWS_PROFILE=kinpachi`
  - `export AWS_REGION=<your-region>` (e.g., `us-west-2`). CDK will use `CDK_DEFAULT_*` envs.
- Node.js 18+
- Python 3.10+
- AWS CLI v2

Install local dependencies:

```bash
# From repo root
python3 -m venv .venv && source .venv/bin/activate
pip install -r infra-cdk/requirements.txt
# Option A: use npx (no global install required)
# Option B: npm install -g aws-cdk@^2
```

### CDK qualifier (important)

- This repo uses the CDK bootstrap qualifier `mcpobs`.
- It is enforced in both `infra-cdk/app.py` via `DefaultStackSynthesizer(qualifier="mcpobs")` and `infra-cdk/cdk.json` via `bootstrapQualifier`.
- If you need to bootstrap manually, pass `--qualifier mcpobs`.

## Bootstrap (first time per account/region)

```bash
# From infra-cdk/
export AWS_PROFILE=kinpachi
export CDK_DEFAULT_ACCOUNT=$(AWS_PROFILE=$AWS_PROFILE aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=${AWS_REGION:-us-east-1}
# Ensure the qualifier matches the project
npx -y aws-cdk@^2 bootstrap aws://$CDK_DEFAULT_ACCOUNT/$CDK_DEFAULT_REGION --qualifier mcpobs
```

## Synthesize

```bash
# In infra-cdk/
npx -y aws-cdk@^2 synth
```

## Deploy

```bash
# In infra-cdk/
npx -y aws-cdk@^2 deploy LangfuseStack --require-approval never
```

After deployment, the output `AlbUrl` will include the UI URL. It may take a few minutes for services to stabilize.

Note: The web service runs with desired_count=1 (ECS patterns requirement). It may start unhealthy until ClickHouse secrets are populated; this is expected.

## Langfuse v3 setup (S3 + ClickHouse)

1. Retrieve outputs (ALB URL, bucket, secret names):

```bash
AWS_PROFILE=kinpachi aws cloudformation describe-stacks \
  --stack-name LangfuseStack --region us-east-1 \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
```

2. Populate ClickHouse secret placeholders with your actual values:

```bash
REGION=us-east-1
STACK=LangfuseStack
CH_URL=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ClickhouseUrlSecretName'].OutputValue" --output text)
CH_USER=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ClickhouseUserSecretName'].OutputValue" --output text)
CH_PASS=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ClickhousePasswordSecretName'].OutputValue" --output text)
CH_MIGR=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ClickhouseMigrationUrlSecretName'].OutputValue" --output text)
CH_DB=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ClickhouseDbSecretName'].OutputValue" --output text)
CH_MIGR_SSL=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ClickhouseMigrationSslSecretName'].OutputValue" --output text)

# CLICKHOUSE_URL uses HTTP(S) interface; prefer TLS if available
AWS_PROFILE=kinpachi aws secretsmanager put-secret-value --region $REGION --secret-id "$CH_URL"        --secret-string "https://<host>:8443"
AWS_PROFILE=kinpachi aws secretsmanager put-secret-value --region $REGION --secret-id "$CH_USER"       --secret-string "<clickhouse_user>"
AWS_PROFILE=kinpachi aws secretsmanager put-secret-value --region $REGION --secret-id "$CH_PASS"       --secret-string "<clickhouse_password>"
# Migration uses native protocol scheme
AWS_PROFILE=kinpachi aws secretsmanager put-secret-value --region $REGION --secret-id "$CH_MIGR"      --secret-string "clickhouse://<host>:9440"
AWS_PROFILE=kinpachi aws secretsmanager put-secret-value --region $REGION --secret-id "$CH_DB"        --secret-string "default"
AWS_PROFILE=kinpachi aws secretsmanager put-secret-value --region $REGION --secret-id "$CH_MIGR_SSL"  --secret-string "true"
```

3. Force a new ECS deployment and scale the worker (using outputs for names):

```bash
CLUSTER=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ClusterName'].OutputValue" --output text)
WEB=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='WebServiceName'].OutputValue" --output text)
WORKER=$(AWS_PROFILE=kinpachi aws cloudformation describe-stacks --stack-name $STACK --region $REGION --query "Stacks[0].Outputs[?OutputKey=='WorkerServiceName'].OutputValue" --output text)

AWS_PROFILE=kinpachi aws ecs update-service --cluster "$CLUSTER" --service "$WEB" --force-new-deployment --region $REGION
AWS_PROFILE=kinpachi aws ecs update-service --cluster "$CLUSTER" --service "$WORKER" --desired-count 1 --force-new-deployment --region $REGION
```

## Optional: scale services during troubleshooting

If you need to stop service churn while iterating on infra:

```bash
# Identify cluster ARN
aws ecs list-clusters --query 'clusterArns[?contains(@, `LangfuseStack-Cluster`)]' --output text

# List services in that cluster
aws ecs list-services --cluster <cluster-arn> --output text

# Scale web and worker to 0
aws ecs update-service --cluster <cluster-arn> --service <web-service-arn-or-name> --desired-count 0
aws ecs update-service --cluster <cluster-arn> --service <worker-service-arn-or-name> --desired-count 0

# Later, scale up (e.g., web desired 1+, worker desired 1)
aws ecs update-service --cluster <cluster-arn> --service <web-service> --desired-count 1
aws ecs update-service --cluster <cluster-arn> --service <worker-service> --desired-count 1
```

## Logs and health

- Health check: ALB target group uses `/api/health` on port 3000
- Check CloudWatch Logs for the containers:
  - Web stream prefix: `LangfuseWeb`
  - Worker stream prefix: `LangfuseWorker`

Common startup issues:
- Postgres unreachable (Prisma P1001): ensure RDS is healthy and SG ingress from ECS is allowed.
- Secrets permission denied: the stack grants the ECS execution roles read access to required secrets.
- NEXTAUTH_URL must match the external URL; the stack injects it after ALB creation.
- Until ClickHouse secrets are populated with valid values, startup errors related to ClickHouse connectivity are expected.

## ClickHouse (required for full functionality)

This stack creates placeholders in Secrets Manager and wires them into both containers. Actions required:
- Set `CLICKHOUSE_URL`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_DB` and optionally `CLICKHOUSE_MIGRATION_URL` + `CLICKHOUSE_MIGRATION_SSL` using the provided secret names in the stack outputs.
- `CLICKHOUSE_CLUSTER_ENABLED` defaults to `false`.
- After updating secrets, force a new ECS deployment for the web and scale the worker as shown above.

### Optional: provision free ClickHouse on EC2 (single node)

For a free, self-hosted setup, the stack can optionally create a single EC2 instance with ClickHouse installed in private subnets and open only to the ECS services (ports 8123 HTTP and 9000 Native).

Enable with the CDK context flag or use the helper script:

```bash
# Using the helper script (prints commands by default; does not apply changes)
REGION=us-east-1 PROFILE=kinpachi APPLY=false \
bash infra-cdk/scripts/provision_clickhouse_ec2.sh

# When ready to apply secrets and ECS updates automatically:
REGION=us-east-1 PROFILE=kinpachi APPLY=true \
bash infra-cdk/scripts/provision_clickhouse_ec2.sh
```

What the script does:

- Deploys with `-c PROVISION_CLICKHOUSE_EC2=true` to create a small EC2 instance and security group.
- Retrieves outputs (ClickHouse EC2 private IP, secret names, ECS service names).
- Prepares non-TLS internal URLs derived from the private IP:
  - `CLICKHOUSE_URL=http://<private-ip>:8123`
  - `CLICKHOUSE_MIGRATION_URL=clickhouse://<private-ip>:9000`
  - `CLICKHOUSE_MIGRATION_SSL=false`
- Optionally applies the above secrets and forces a new ECS deployment, and scales the worker to 1.

Notes:

- This EC2 instance is in private subnets; no public access is exposed.
- For production, enable TLS (use HTTPS/8443 and Native/9440) and set `CLICKHOUSE_MIGRATION_SSL=true`.

### If a CloudFormation stack is stuck

Sometimes an earlier failed deploy leaves a stack in a non-terminal state. Check and delete if needed before re-deploying:

```bash
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE ROLLBACK_FAILED ROLLBACK_COMPLETE DELETE_FAILED UPDATE_ROLLBACK_FAILED \
  --query "StackSummaries[?contains(StackName, 'LangfuseStack')].[StackName, StackStatus]" --output table

# If a stuck stack exists:
aws cloudformation delete-stack --stack-name <stuck-stack-name>
aws cloudformation wait stack-delete-complete --stack-name <stuck-stack-name>
```

References:
- Langfuse self-hosting: https://langfuse.com/self-hosting
- AWS CDK ECS patterns: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ecs_patterns-readme.html
- ECS secrets: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data.html
