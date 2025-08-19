-- Langfuse ClickHouse Schema (v3)
-- Source: https://github.com/langfuse/langfuse/tree/main/packages/shared/clickhouse/migrations/clustered
-- This is the consolidated schema for Langfuse v3 with ClickHouse
-- Updated: 2024

-- Note: If using ClickHouse cluster, tables are created with "ON CLUSTER default"
-- For single-node deployments, remove "ON CLUSTER default" from CREATE TABLE statements

-- Schema migrations tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version Int64,
    dirty UInt8,
    sequence UInt64
) ENGINE = MergeTree ORDER BY sequence;

-- Traces table (core observability data)
CREATE TABLE IF NOT EXISTS traces (
    `id` String,
    `timestamp` DateTime64(3),
    `name` String,
    `user_id` Nullable(String),
    `metadata` Map(LowCardinality(String), String),
    `release` Nullable(String),
    `version` Nullable(String),
    `project_id` String,
    `environment` LowCardinality(String) DEFAULT 'default',
    `public` Bool,
    `bookmarked` Bool,
    `tags` Array(String),
    `input` Nullable(String) CODEC(ZSTD(3)),
    `output` Nullable(String) CODEC(ZSTD(3)),
    `session_id` Nullable(String),
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3) DEFAULT now64(3),
    `is_deleted` UInt8 DEFAULT 0,
    INDEX idx_id id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_res_metadata_key mapKeys(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_res_metadata_value mapValues(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_session_id session_id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_user_id user_id TYPE bloom_filter(0.001) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
PARTITION BY toYYYYMM(timestamp)
PRIMARY KEY (project_id, toDate(timestamp))
ORDER BY (project_id, toDate(timestamp), id);

-- Observations table (detailed execution data)
CREATE TABLE IF NOT EXISTS observations (
    `id` String,
    `trace_id` String,
    `project_id` String,
    `environment` LowCardinality(String) DEFAULT 'default',
    `type` LowCardinality(String),
    `parent_observation_id` Nullable(String),
    `start_time` DateTime64(3),
    `end_time` Nullable(DateTime64(3)),
    `name` String,
    `metadata` Map(LowCardinality(String), String),
    `level` LowCardinality(String),
    `status_message` Nullable(String),
    `version` Nullable(String),
    `input` Nullable(String) CODEC(ZSTD(3)),
    `output` Nullable(String) CODEC(ZSTD(3)),
    `provided_model_name` Nullable(String),
    `internal_model_id` Nullable(String),
    `model_parameters` Nullable(String),
    `provided_usage_details` Map(LowCardinality(String), UInt64),
    `usage_details` Map(LowCardinality(String), UInt64),
    `provided_cost_details` Map(LowCardinality(String), Decimal64(12)),
    `cost_details` Map(LowCardinality(String), Decimal64(12)),
    `total_cost` Nullable(Decimal64(12)),
    `completion_start_time` Nullable(DateTime64(3)),
    `prompt_id` Nullable(String),
    `prompt_name` Nullable(String),
    `prompt_version` Nullable(UInt16),
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3) DEFAULT now64(3),
    `is_deleted` UInt8 DEFAULT 0,
    INDEX idx_id id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_trace_id trace_id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_project_id project_id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_res_metadata_key mapKeys(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_res_metadata_value mapValues(metadata) TYPE bloom_filter(0.01) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
PARTITION BY toYYYYMM(start_time)
PRIMARY KEY (project_id, type, toDate(start_time))
ORDER BY (project_id, type, toDate(start_time), id);

-- Scores table (evaluation metrics)
CREATE TABLE IF NOT EXISTS scores (
    `id` String,
    `timestamp` DateTime64(3),
    `project_id` String,
    `environment` LowCardinality(String) DEFAULT 'default',
    `trace_id` Nullable(String),
    `observation_id` Nullable(String),
    `name` String,
    `value` Float64,
    `source` String,
    `comment` Nullable(String) CODEC(ZSTD(1)),
    `author_user_id` Nullable(String),
    `config_id` Nullable(String),
    `data_type` String,
    `string_value` Nullable(String),
    `queue_id` Nullable(String),
    `metadata` Map(LowCardinality(String), String),
    `session_id` Nullable(String),
    `run_id` Nullable(String),
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3) DEFAULT now64(3),
    `is_deleted` UInt8 DEFAULT 0,
    INDEX idx_id id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_project_trace_observation (project_id, trace_id, observation_id) TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_trace_id trace_id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_session_id session_id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_run_id run_id TYPE bloom_filter(0.001) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
PARTITION BY toYYYYMM(timestamp)
PRIMARY KEY (project_id, toDate(timestamp), name)
ORDER BY (project_id, toDate(timestamp), name, id);

-- Project environments table
CREATE TABLE IF NOT EXISTS project_environments (
    `project_id` String,
    `environments` SimpleAggregateFunction(groupUniqArrayArray, Array(String)),
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3) DEFAULT now64(3),
    `is_deleted` UInt8 DEFAULT 0
) ENGINE = AggregatingMergeTree
ORDER BY (project_id);

-- Event log table (for blob storage references)
CREATE TABLE IF NOT EXISTS event_log (
    `id` String,
    `project_id` String,
    `entity_type` String,
    `entity_id` String,
    `event_id` Nullable(String),
    `bucket_name` String,
    `bucket_path` String,
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3) DEFAULT now64(3),
    `is_deleted` UInt8 DEFAULT 0
) ENGINE = MergeTree()
ORDER BY (project_id, entity_type, entity_id);

-- Blob storage file log
CREATE TABLE IF NOT EXISTS blob_storage_file_log (
    `id` String,
    `project_id` String,
    `entity_type` String,
    `entity_id` String,
    `event_id` String,
    `bucket_name` String,
    `bucket_path` String,
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3) DEFAULT now64(3),
    `is_deleted` UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
ORDER BY (project_id, entity_type, entity_id, event_id);

-- Dataset run items table
CREATE TABLE IF NOT EXISTS dataset_run_items_rmt (
    `id` String,
    `project_id` String,
    `dataset_run_id` String,
    `dataset_item_id` String,
    `dataset_id` String,
    `trace_id` String,
    `observation_id` Nullable(String),
    `error` Nullable(String),
    `dataset_run_name` String,
    `dataset_run_description` Nullable(String),
    `dataset_run_metadata` Map(LowCardinality(String), String),
    `dataset_run_created_at` DateTime64(3),
    `dataset_item_input` Nullable(String) CODEC(ZSTD(3)),
    `dataset_item_expected_output` Nullable(String) CODEC(ZSTD(3)),
    `dataset_item_metadata` Map(LowCardinality(String), String),
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3) DEFAULT now64(3),
    `is_deleted` UInt8 DEFAULT 0,
    INDEX idx_dataset_item dataset_item_id TYPE bloom_filter(0.001) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
ORDER BY (project_id, dataset_id, dataset_run_id, id);

-- Insert migration records (marking all migrations as applied)
INSERT INTO schema_migrations (version, dirty, sequence) 
SELECT number, 0, number 
FROM system.numbers 
LIMIT 26
WHERE NOT EXISTS (SELECT 1 FROM schema_migrations);