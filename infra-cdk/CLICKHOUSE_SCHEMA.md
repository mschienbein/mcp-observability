# ClickHouse Schema for Langfuse v3

This document describes the complete ClickHouse schema required for Langfuse v3 to function properly.

## Schema Overview

Langfuse v3 requires the following tables in ClickHouse:

### Core Tables
1. **traces** - Stores trace data with environment support
2. **observations** - Stores LLM observations/generations with environment support  
3. **scores** - Stores evaluation scores with environment support
4. **schema_migrations** - Tracks migration state

### Supporting Tables
5. **project_environments** - Stores project environment configurations
6. **event_log** - Event logging table
7. **blob_storage_file_log** - Tracks blob storage files
8. **dataset_run_items_rmt** - Dataset run items

## Important Schema Requirements

### Environment Column
All main tables (traces, observations, scores) MUST include an `environment` column of type `Nullable(String)`. This is required for the Langfuse dashboard to filter data by environment.

### Engine Requirements
Tables must use `ReplacingMergeTree` engine to support the `FINAL` clause that Langfuse queries use.

### Indexes
The following indexes are required for performance:
- traces: idx_session_id, idx_user_id, idx_environment
- observations: idx_trace_id, idx_environment
- scores: idx_trace_id, idx_environment

## Setup Instructions

### Automated Setup
Run the complete setup script after deploying ClickHouse:

```bash
# Set environment variables
export REGION=us-east-1
export CH_IP=<clickhouse-private-ip>
export CH_PASSWORD=<your-password>

# Run the setup script
bash infra-cdk/scripts/setup_clickhouse_complete.sh
```

### Manual Setup
If you need to set up the schema manually:

1. Connect to your ClickHouse instance
2. Execute the SQL from `scripts/create_clickhouse_schema.sql`
3. Verify all tables are created with the `environment` column
4. Restart Langfuse services to pick up the new schema

## Troubleshooting

### Missing environment column errors
If you see errors like "Identifier 'traces.environment' cannot be resolved", the environment column is missing. Add it with:

```sql
ALTER TABLE traces ADD COLUMN IF NOT EXISTS environment Nullable(String);
ALTER TABLE observations ADD COLUMN IF NOT EXISTS environment Nullable(String);
ALTER TABLE scores ADD COLUMN IF NOT EXISTS environment Nullable(String);
```

### FINAL clause errors
If you see "Storage MergeTree doesn't support FINAL", the table was created with the wrong engine. Recreate the table with `ReplacingMergeTree`.

### Migration state issues
If migrations are stuck, check the schema_migrations table:

```sql
SELECT * FROM schema_migrations ORDER BY sequence;
```

Ensure versions 1-6 are present with dirty=0.

## Version Compatibility

- ClickHouse version >= 24.3 is required
- Langfuse v3.x requires this complete schema
- The schema is backward compatible with Langfuse v2 data after migration