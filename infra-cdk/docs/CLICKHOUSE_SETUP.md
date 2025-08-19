# ClickHouse Setup Guide

This guide covers setting up ClickHouse for Langfuse v3 observability data storage.

## Overview

Langfuse v3 uses ClickHouse as its primary analytics database for storing traces, observations, and scores. ClickHouse provides excellent performance for time-series data and complex analytical queries.

## Schema Location

The complete ClickHouse schema is located at:
```
scripts/database/langfuse_clickhouse_schema.sql
```

## Tables Structure

### Core Tables

1. **traces** - Top-level execution traces
   - Partitioned by month (`toYYYYMM(timestamp)`)
   - Includes metadata, input/output, tags
   - Bloom filter indexes for efficient queries

2. **observations** - Detailed execution steps
   - Links to parent trace via `trace_id`
   - Stores model usage, costs, and timing
   - Supports nested observations

3. **scores** - Evaluation metrics
   - Links to traces and observations
   - Stores numeric and string values
   - Supports custom metadata

4. **project_environments** - Environment tracking
   - Aggregates unique environments per project

5. **event_log** & **blob_storage_file_log** - File storage references
   - Tracks S3 blob storage for large payloads

6. **dataset_run_items_rmt** - Dataset evaluation results
   - Links dataset items to execution traces

7. **schema_migrations** - Migration tracking
   - Tracks applied schema versions

## Deployment Options

### Option 1: EC2 Instance (Recommended for Production)

Use the provisioning script:
```bash
cd infra-cdk
REGION=us-east-1 PROFILE=your-profile APPLY=true \
  bash scripts/setup/provision_clickhouse_ec2.sh
```

This creates:
- EC2 instance with Docker
- ClickHouse container with persistent storage
- Security group for port 8123/9000
- Elastic IP for stable access

### Option 2: Docker Compose (Development)

```yaml
clickhouse:
  image: clickhouse/clickhouse-server:24.3-alpine
  ports:
    - "8123:8123"
    - "9000:9000"
  environment:
    CLICKHOUSE_DB: default
    CLICKHOUSE_USER: default
    CLICKHOUSE_PASSWORD: clickhouse123
  volumes:
    - clickhouse_data:/var/lib/clickhouse
```

### Option 3: ClickHouse Cloud (Managed Service)

1. Create account at https://clickhouse.cloud
2. Create a service in your preferred region
3. Note connection details for Langfuse configuration

## Schema Application

### Manual Application

```bash
# Connect to ClickHouse
clickhouse-client --host=<host> --password=<password>

# Apply schema
clickhouse-client --host=<host> --password=<password> --multiquery < scripts/database/langfuse_clickhouse_schema.sql
```

### Via SSM (for EC2)

```bash
aws ssm send-command \
  --instance-ids <instance-id> \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["cat /path/to/schema.sql | docker exec -i clickhouse clickhouse-client --password=<password> --multiquery"]'
```

## Configuration

### Langfuse Environment Variables

```bash
# ClickHouse connection
CLICKHOUSE_URL=http://<host>:8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=<password>
CLICKHOUSE_DATABASE=default

# Migration settings
CLICKHOUSE_MIGRATION_URL=clickhouse://<host>:9000
LANGFUSE_AUTO_CLICKHOUSE_MIGRATION_DISABLED=false

# Cluster mode (if using cluster)
CLICKHOUSE_CLUSTER_ENABLED=false
CLICKHOUSE_CLUSTER_NAME=default
```

### AWS Secrets Manager (CDK Deployment)

The CDK stack creates placeholder secrets that need to be updated:
```bash
# Update ClickHouse URL
aws secretsmanager update-secret \
  --secret-id LangfuseStack-ClickhouseUrl \
  --secret-string "http://<clickhouse-ip>:8123"

# Update password
aws secretsmanager update-secret \
  --secret-id LangfuseStack-ClickhousePassword \
  --secret-string "<your-password>"
```

## Performance Optimization

### Partition Management

Tables are partitioned by month. For high-volume deployments:
```sql
-- Drop old partitions
ALTER TABLE traces DROP PARTITION '202301';

-- Optimize table
OPTIMIZE TABLE traces FINAL;
```

### Index Optimization

The schema includes bloom filter indexes for:
- ID lookups (0.001 false positive rate)
- Metadata keys/values (0.01 false positive rate)

### Memory Settings

For production workloads, adjust ClickHouse settings:
```xml
<clickhouse>
  <max_memory_usage>10000000000</max_memory_usage>
  <max_memory_usage_for_user>10000000000</max_memory_usage_for_user>
  <max_server_memory_usage>20000000000</max_server_memory_usage>
</clickhouse>
```

## Monitoring

### Key Metrics

Monitor via ClickHouse system tables:
```sql
-- Table sizes
SELECT 
  table,
  formatReadableSize(sum(bytes)) as size,
  sum(rows) as rows
FROM system.parts
WHERE active
GROUP BY table;

-- Query performance
SELECT 
  query,
  query_duration_ms,
  read_rows,
  memory_usage
FROM system.query_log
ORDER BY query_start_time DESC
LIMIT 10;
```

### CloudWatch Integration

For EC2 deployments, use CloudWatch agent:
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure for ClickHouse metrics
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## Backup and Recovery

### Backup Strategy

1. **Incremental Backups**:
```bash
clickhouse-backup create --tables='traces,observations,scores'
clickhouse-backup upload
```

2. **S3 Backup**:
```sql
-- Backup to S3
BACKUP TABLE traces TO S3('s3://bucket/backup/', 'key', 'secret');
```

### Recovery

```sql
-- Restore from S3
RESTORE TABLE traces FROM S3('s3://bucket/backup/', 'key', 'secret');
```

## Troubleshooting

### Common Issues

1. **Connection refused**: Check security groups and ClickHouse binding address
2. **Out of memory**: Adjust max_memory_usage settings
3. **Slow queries**: Check partition pruning and index usage
4. **Dirty migrations**: Reset schema_migrations table if needed

### Debug Commands

```bash
# Check ClickHouse logs
docker logs clickhouse

# Check table structure
clickhouse-client --query="DESCRIBE TABLE traces"

# Check running queries
clickhouse-client --query="SELECT * FROM system.processes"

# Kill long-running query
clickhouse-client --query="KILL QUERY WHERE query_id = 'xxx'"
```

## Migration from v2 to v3

If migrating from Langfuse v2 (PostgreSQL) to v3 (ClickHouse):

1. Export data from PostgreSQL
2. Transform to ClickHouse schema format
3. Import using clickhouse-client or Langfuse migration tools
4. Verify data integrity

Langfuse provides background migration jobs to minimize downtime during upgrade.

## Support

- ClickHouse Documentation: https://clickhouse.com/docs
- Langfuse v3 Migration Guide: https://langfuse.com/self-hosting/upgrade-guides/upgrade-v2-to-v3
- GitHub Discussions: https://github.com/orgs/langfuse/discussions