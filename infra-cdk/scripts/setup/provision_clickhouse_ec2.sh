#!/usr/bin/env bash
set -euo pipefail

# Provision a single-node ClickHouse EC2 via CDK and prepare Langfuse secrets.
# Usage:
#   REGION=us-east-1 PROFILE=kinpachi APPLY=false bash infra-cdk/scripts/provision_clickhouse_ec2.sh
# Env Vars:
#   REGION   - AWS region (default: us-east-1)
#   PROFILE  - AWS CLI profile (default: default)
#   STACK    - CloudFormation stack name (default: LangfuseStack)
#   APPLY    - If "true", apply the secrets and ECS redeploy automatically. Otherwise, just print commands.

REGION=${REGION:-us-east-1}
PROFILE=${PROFILE:-default}
STACK=${STACK:-LangfuseStack}
APPLY=${APPLY:-false}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
pushd "$SCRIPT_DIR" >/dev/null

echo "[1/3] Deploying $STACK with ClickHouse EC2 (context PROVISION_CLICKHOUSE_EC2=true)..."
# Uses local CDK (npx) so no global install needed
npx -y aws-cdk@^2 deploy "$STACK" --require-approval never -c PROVISION_CLICKHOUSE_EC2=true

echo "[2/3] Fetching stack outputs..."
CH_URL_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='ClickhouseUrlSecretName'].OutputValue" --output text)
CH_USER_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='ClickhouseUserSecretName'].OutputValue" --output text)
CH_PASS_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='ClickhousePasswordSecretName'].OutputValue" --output text)
CH_MIGR_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='ClickhouseMigrationUrlSecretName'].OutputValue" --output text)
CH_DB_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='ClickhouseDbSecretName'].OutputValue" --output text)
CH_MIGR_SSL_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='ClickhouseMigrationSslSecretName'].OutputValue" --output text)
CH_PRIV_IP=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='ClickhouseEc2PrivateIp'].OutputValue" --output text)
CLUSTER=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='ClusterName'].OutputValue" --output text)
WEB=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='WebServiceName'].OutputValue" --output text)
WORKER=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='WorkerServiceName'].OutputValue" --output text)

if [[ -z "$CH_PRIV_IP" || "$CH_PRIV_IP" == "None" ]]; then
  echo "Error: ClickHouse EC2 private IP not found. Ensure PROVISION_CLICKHOUSE_EC2=true was applied."
  exit 1
fi

CH_HTTP_URL="http://$CH_PRIV_IP:8123"
CH_NATIVE_URL="clickhouse://$CH_PRIV_IP:9000"

echo "[3/3] Prepared commands (non-TLS for private VPC):"
cat <<EOCMD
# Set ClickHouse secrets (use your own user/pass; DB default is 'default')
aws secretsmanager put-secret-value --region $REGION --profile $PROFILE --secret-id "$CH_URL_NAME"       --secret-string "$CH_HTTP_URL"
aws secretsmanager put-secret-value --region $REGION --profile $PROFILE --secret-id "$CH_USER_NAME"      --secret-string "<clickhouse_user>"
aws secretsmanager put-secret-value --region $REGION --profile $PROFILE --secret-id "$CH_PASS_NAME"      --secret-string "<clickhouse_password>"
aws secretsmanager put-secret-value --region $REGION --profile $PROFILE --secret-id "$CH_DB_NAME"        --secret-string "default"
aws secretsmanager put-secret-value --region $REGION --profile $PROFILE --secret-id "$CH_MIGR_NAME"      --secret-string "$CH_NATIVE_URL"
aws secretsmanager put-secret-value --region $REGION --profile $PROFILE --secret-id "$CH_MIGR_SSL_NAME"  --secret-string "false"

# Force ECS to pick up new secrets and start worker
aws ecs update-service --cluster "$CLUSTER" --service "$WEB" --force-new-deployment --region $REGION --profile $PROFILE
aws ecs update-service --cluster "$CLUSTER" --service "$WORKER" --desired-count 1 --force-new-deployment --region $REGION --profile $PROFILE
EOCMD

if [[ "$APPLY" == "true" ]]; then
  echo "Applying secrets and ECS updates..."
  aws secretsmanager put-secret-value --region "$REGION" --profile "$PROFILE" --secret-id "$CH_URL_NAME"      --secret-string "$CH_HTTP_URL"
  # If CH_USER is truly unset, prompt (allows CH_USER="" if ever needed)
  if [[ -z ${CH_USER+x} ]]; then
    echo "Enter ClickHouse username:"; read -r CH_USER
  fi
  aws secretsmanager put-secret-value --region "$REGION" --profile "$PROFILE" --secret-id "$CH_USER_NAME"     --secret-string "$CH_USER"
  # If CH_PASS is truly unset, prompt (allows CH_PASS="" for no-password users)
  if [[ -z ${CH_PASS+x} ]]; then
    echo "Enter ClickHouse password:"; read -rs CH_PASS; echo
  fi
  aws secretsmanager put-secret-value --region "$REGION" --profile "$PROFILE" --secret-id "$CH_PASS_NAME"     --secret-string "$CH_PASS"
  aws secretsmanager put-secret-value --region "$REGION" --profile "$PROFILE" --secret-id "$CH_DB_NAME"       --secret-string "default"
  aws secretsmanager put-secret-value --region "$REGION" --profile "$PROFILE" --secret-id "$CH_MIGR_NAME"     --secret-string "$CH_NATIVE_URL"
  aws secretsmanager put-secret-value --region "$REGION" --profile "$PROFILE" --secret-id "$CH_MIGR_SSL_NAME" --secret-string "false"
  aws ecs update-service --cluster "$CLUSTER" --service "$WEB" --force-new-deployment --region "$REGION" --profile "$PROFILE"
  aws ecs update-service --cluster "$CLUSTER" --service "$WORKER" --desired-count 1 --force-new-deployment --region "$REGION" --profile "$PROFILE"
  echo "Done. Check CloudWatch logs for LangfuseWeb/LangfuseWorker."
else
  echo "Not applying changes automatically. Re-run with APPLY=true to execute the commands above."
fi

popd >/dev/null
