#!/usr/bin/env bash
set -euo pipefail

# Complete ClickHouse setup script for Langfuse v3
# This script sets up ClickHouse with the complete schema including all required columns

REGION=${REGION:-us-east-1}
PROFILE=${PROFILE:-default}
CH_IP=${CH_IP:-}
CH_USER=${CH_USER:-default}
CH_PASSWORD=${CH_PASSWORD:-clickhouse123}

echo "==================================================================="
echo "ClickHouse Complete Setup for Langfuse v3"
echo "==================================================================="

# Function to execute SQL on ClickHouse via SSM
execute_clickhouse_sql() {
    local sql="$1"
    local instance_id="$2"
    
    # Escape the SQL for shell
    sql_escaped=$(echo "$sql" | sed 's/"/\\"/g')
    
    aws ssm send-command \
        --instance-ids "$instance_id" \
        --document-name "AWS-RunShellScript" \
        --parameters "commands=[\"docker exec clickhouse clickhouse-client --user=$CH_USER --password='$CH_PASSWORD' --multiquery --query=\\\"$sql_escaped\\\"\"]" \
        --region "$REGION" \
        --profile "$PROFILE" \
        --output text --query "Command.CommandId"
}

# Step 1: Find ClickHouse instance
if [[ -z "$CH_IP" ]]; then
    echo "Finding ClickHouse EC2 instance from stack..."
    STACK=${STACK:-LangfuseStack}
    CH_IP=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
        --query "Stacks[0].Outputs[?OutputKey=='ClickhouseEc2PrivateIp'].OutputValue" --output text)
fi

if [[ -z "$CH_IP" || "$CH_IP" == "None" ]]; then
    echo "Error: Could not find ClickHouse instance IP. Specify CH_IP environment variable."
    exit 1
fi

echo "Using ClickHouse at: $CH_IP"

# Step 2: Get instance ID
INSTANCE_ID=$(aws ec2 describe-instances --region "$REGION" --profile "$PROFILE" \
    --filters "Name=private-ip-address,Values=$CH_IP" \
    --query "Reservations[0].Instances[0].InstanceId" --output text)

if [[ -z "$INSTANCE_ID" || "$INSTANCE_ID" == "None" ]]; then
    echo "Error: Could not find EC2 instance with IP $CH_IP"
    exit 1
fi

echo "Found EC2 instance: $INSTANCE_ID"

# Step 3: Read the SQL schema file
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SQL_FILE="$SCRIPT_DIR/create_clickhouse_schema.sql"

if [[ ! -f "$SQL_FILE" ]]; then
    echo "Error: SQL schema file not found at $SQL_FILE"
    exit 1
fi

echo "Reading schema from: $SQL_FILE"

# Step 4: Execute the schema setup
echo "Setting up ClickHouse schema..."

# Split the SQL file into smaller chunks to avoid command length limits
# First drop existing tables
echo "Dropping existing tables if any..."
DROP_SQL="DROP TABLE IF EXISTS traces;
DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS scores;
DROP TABLE IF EXISTS project_environments;
DROP TABLE IF EXISTS event_log;
DROP TABLE IF EXISTS blob_storage_file_log;
DROP TABLE IF EXISTS dataset_run_items_rmt;
DROP TABLE IF EXISTS schema_migrations;"

CMD_ID=$(execute_clickhouse_sql "$DROP_SQL" "$INSTANCE_ID")
echo "Drop command sent: $CMD_ID"
sleep 10

# Create each table individually
echo "Creating schema_migrations table..."
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"CREATE TABLE IF NOT EXISTS schema_migrations (version Int64, dirty UInt8, sequence UInt64) ENGINE = MergeTree ORDER BY sequence\""]' \
    --region "$REGION" --profile "$PROFILE" --output text --query "Command.CommandId"

sleep 5

echo "Creating all tables with complete schema..."
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --multiquery --query=\"
CREATE TABLE IF NOT EXISTS traces (
    id String, timestamp DateTime64(3), name Nullable(String), user_id Nullable(String),
    metadata Nullable(String), release Nullable(String), version Nullable(String), project_id String,
    public Nullable(UInt8), tags Array(String), bookmarked Nullable(UInt8), session_id Nullable(String),
    input Nullable(String), output Nullable(String), environment Nullable(String),
    created_at DateTime64(3), updated_at DateTime64(3), event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at) ORDER BY (project_id, id, event_ts) PARTITION BY toYYYYMM(timestamp);

CREATE TABLE IF NOT EXISTS observations (
    id String, trace_id Nullable(String), project_id String, type String,
    parent_observation_id Nullable(String), name Nullable(String), start_time DateTime64(3),
    end_time Nullable(DateTime64(3)), completion_start_time Nullable(DateTime64(3)),
    metadata Nullable(String), model Nullable(String), model_parameters Nullable(String),
    input Nullable(String), output Nullable(String), provided_model_name Nullable(String),
    unit Nullable(String), level Nullable(String), status_message Nullable(String),
    version Nullable(String), provided_usage_details Nullable(String), usage_details Nullable(String),
    provided_cost_details Nullable(String), cost_details Nullable(String), total_cost Nullable(Float64),
    provided_input_cost Nullable(Float64), input_cost Nullable(Float64), provided_output_cost Nullable(Float64),
    output_cost Nullable(Float64), provided_total_cost Nullable(Float64), completion_tokens Nullable(Int64),
    prompt_tokens Nullable(Int64), total_tokens Nullable(Int64), environment Nullable(String),
    created_at DateTime64(3), updated_at DateTime64(3), event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at) ORDER BY (project_id, id, event_ts) PARTITION BY toYYYYMM(start_time);

CREATE TABLE IF NOT EXISTS scores (
    id String, timestamp DateTime64(3), project_id String, trace_id String,
    observation_id Nullable(String), name String, value Nullable(Float64), string_value Nullable(String),
    source String, comment Nullable(String), author_user_id Nullable(String), config_id Nullable(String),
    data_type String, queue_id Nullable(String), environment Nullable(String),
    created_at DateTime64(3), updated_at DateTime64(3), event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at) ORDER BY (project_id, id, event_ts) PARTITION BY toYYYYMM(timestamp);

CREATE TABLE IF NOT EXISTS project_environments (
    project_id String, environments Array(String), created_at DateTime64(3), updated_at DateTime64(3),
    event_ts DateTime64(3) DEFAULT now64(3), is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at) ORDER BY (project_id, event_ts);

CREATE TABLE IF NOT EXISTS event_log (
    id String, project_id String, timestamp DateTime64(3), event_type String, event_data String,
    created_at DateTime64(3), updated_at DateTime64(3), event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at) ORDER BY (project_id, id, event_ts) PARTITION BY toYYYYMM(timestamp);

CREATE TABLE IF NOT EXISTS blob_storage_file_log (
    id String, project_id String, file_path String, bucket String, size Int64,
    created_at DateTime64(3), updated_at DateTime64(3)
) ENGINE = ReplacingMergeTree(updated_at) ORDER BY (project_id, id);

CREATE TABLE IF NOT EXISTS dataset_run_items_rmt (
    id String, dataset_run_id String, dataset_item_id String, project_id String,
    trace_id Nullable(String), observation_id Nullable(String),
    created_at DateTime64(3), updated_at DateTime64(3)
) ENGINE = ReplacingMergeTree(updated_at) ORDER BY (project_id, id);\""]' \
    --region "$REGION" --profile "$PROFILE" --output text --query "Command.CommandId"

echo "Waiting for tables to be created..."
sleep 15

# Add indexes
echo "Adding performance indexes..."
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"ALTER TABLE traces ADD INDEX IF NOT EXISTS idx_session_id (session_id) TYPE bloom_filter GRANULARITY 1\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"ALTER TABLE traces ADD INDEX IF NOT EXISTS idx_user_id (user_id) TYPE bloom_filter GRANULARITY 1\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"ALTER TABLE traces ADD INDEX IF NOT EXISTS idx_environment (environment) TYPE bloom_filter GRANULARITY 1\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"ALTER TABLE observations ADD INDEX IF NOT EXISTS idx_trace_id (trace_id) TYPE bloom_filter GRANULARITY 1\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"ALTER TABLE observations ADD INDEX IF NOT EXISTS idx_environment (environment) TYPE bloom_filter GRANULARITY 1\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"ALTER TABLE scores ADD INDEX IF NOT EXISTS idx_trace_id (trace_id) TYPE bloom_filter GRANULARITY 1\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"ALTER TABLE scores ADD INDEX IF NOT EXISTS idx_environment (environment) TYPE bloom_filter GRANULARITY 1\""
    ]' \
    --region "$REGION" --profile "$PROFILE" --output text --query "Command.CommandId"

sleep 10

# Mark migrations as complete
echo "Marking migrations as complete..."
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"TRUNCATE TABLE schema_migrations\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"INSERT INTO schema_migrations (version, dirty, sequence) VALUES (1, 0, 1), (2, 0, 2), (3, 0, 3), (4, 0, 4), (5, 0, 5), (6, 0, 6)\""
    ]' \
    --region "$REGION" --profile "$PROFILE" --output text --query "Command.CommandId"

sleep 5

# Verify setup
echo "Verifying ClickHouse setup..."
CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "echo \"Tables created:\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"SHOW TABLES\"",
        "echo \"\"",
        "echo \"Checking environment column in traces:\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"DESCRIBE TABLE traces\" | grep environment || echo \"environment column not found in traces\"",
        "echo \"\"",
        "echo \"Checking environment column in observations:\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"DESCRIBE TABLE observations\" | grep environment || echo \"environment column not found in observations\"",
        "echo \"\"",
        "echo \"Checking environment column in scores:\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"DESCRIBE TABLE scores\" | grep environment || echo \"environment column not found in scores\"",
        "echo \"\"",
        "echo \"Migration status:\"",
        "docker exec clickhouse clickhouse-client --user=default --password=clickhouse123 --query=\"SELECT * FROM schema_migrations ORDER BY sequence\""
    ]' \
    --region "$REGION" --profile "$PROFILE" --output text --query "Command.CommandId")

echo "Verification command: $CMD_ID"
echo "Waiting for verification results..."
sleep 15

# Get verification results
aws ssm get-command-invocation \
    --command-id "$CMD_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$REGION" \
    --profile "$PROFILE" \
    --query "StandardOutputContent" \
    --output text

echo ""
echo "==================================================================="
echo "ClickHouse schema setup complete!"
echo "==================================================================="
echo ""
echo "Next steps:"
echo "1. Update Langfuse secrets if not already done"
echo "2. Restart ECS services to pick up the new schema:"
echo ""
echo "   # Get cluster and service names"
echo "   CLUSTER=\$(aws cloudformation describe-stacks --stack-name LangfuseStack --region $REGION --query \"Stacks[0].Outputs[?OutputKey=='ClusterName'].OutputValue\" --output text)"
echo "   WEB=\$(aws cloudformation describe-stacks --stack-name LangfuseStack --region $REGION --query \"Stacks[0].Outputs[?OutputKey=='WebServiceName'].OutputValue\" --output text)"
echo "   WORKER=\$(aws cloudformation describe-stacks --stack-name LangfuseStack --region $REGION --query \"Stacks[0].Outputs[?OutputKey=='WorkerServiceName'].OutputValue\" --output text)"
echo ""
echo "   # Restart services"
echo "   aws ecs update-service --cluster \"\$CLUSTER\" --service \"\$WEB\" --force-new-deployment --region $REGION"
echo "   aws ecs update-service --cluster \"\$CLUSTER\" --service \"\$WORKER\" --force-new-deployment --region $REGION"
echo ""