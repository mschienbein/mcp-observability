-- Langfuse Official ClickHouse Schema
-- Source: https://github.com/langfuse/langfuse/tree/main/packages/shared/clickhouse/migrations/clustered
-- This is the complete schema extracted from the official Langfuse v3 repository
-- Apply these migrations in order for a working Langfuse ClickHouse deployment

-- Migration 0001: Traces table
CREATE TABLE IF NOT EXISTS traces (
    `id` String,
    `timestamp` DateTime64(3),
    `name` String,
    `user_id` Nullable(String),
    `metadata` Map(LowCardinality(String), String),
    `release` Nullable(String),
    `version` Nullable(String),
    `project_id` String,
    `environment` LowCardinality(String) DEFAULT 'default',  -- Added in migration 0008
    `public` Bool,
    `bookmarked` Bool,
    `tags` Array(String),
    `input` Nullable(String) CODEC(ZSTD(3)),
    `output` Nullable(String) CODEC(ZSTD(3)),
    `session_id` Nullable(String),
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3),
    `is_deleted` UInt8,
    INDEX idx_id id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_res_metadata_key mapKeys(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_res_metadata_value mapValues(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_session_id session_id TYPE bloom_filter(0.001) GRANULARITY 1,  -- Added in migration 0005
    INDEX idx_user_id user_id TYPE bloom_filter(0.001) GRANULARITY 1  -- Added in migration 0006
) ENGINE = ReplacingMergeTree(event_ts, is_deleted) 
PARTITION BY toYYYYMM(timestamp)
PRIMARY KEY (project_id, toDate(timestamp))
ORDER BY (project_id, toDate(timestamp), id);

-- Migration 0002: Observations table
CREATE TABLE IF NOT EXISTS observations (
    `id` String,
    `trace_id` String,
    `project_id` String,
    `environment` LowCardinality(String) DEFAULT 'default',  -- Added in migration 0008
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
    `event_ts` DateTime64(3),
    `is_deleted` UInt8,
    INDEX idx_id id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_trace_id trace_id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_project_id project_id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_res_metadata_key mapKeys(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,  -- Added in migration 0025
    INDEX idx_res_metadata_value mapValues(metadata) TYPE bloom_filter(0.01) GRANULARITY 1  -- Added in migration 0025
) ENGINE = ReplacingMergeTree(event_ts, is_deleted) 
PARTITION BY toYYYYMM(start_time)
PRIMARY KEY (project_id, `type`, toDate(start_time))
ORDER BY (project_id, `type`, toDate(start_time), id);

-- Migration 0003: Scores table
CREATE TABLE IF NOT EXISTS scores (
    `id` String,
    `timestamp` DateTime64(3),
    `project_id` String,
    `environment` LowCardinality(String) DEFAULT 'default',  -- Added in migration 0008
    `trace_id` Nullable(String),  -- Made nullable in migration 0014
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
    `metadata` Map(LowCardinality(String), String),  -- Added in migration 0010
    `session_id` Nullable(String),  -- Added in migration 0012
    `run_id` Nullable(String),  -- Added in migration 0017
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `event_ts` DateTime64(3),
    `is_deleted` UInt8,
    INDEX idx_id id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_project_trace_observation (project_id, trace_id, observation_id) TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_trace_id trace_id TYPE bloom_filter(0.001) GRANULARITY 1,  -- Added in migration 0015
    INDEX idx_session_id session_id TYPE bloom_filter(0.001) GRANULARITY 1,  -- Added in migration 0016
    INDEX idx_run_id run_id TYPE bloom_filter(0.001) GRANULARITY 1  -- Added in migration 0018
) ENGINE = ReplacingMergeTree(event_ts, is_deleted) 
PARTITION BY toYYYYMM(timestamp)
PRIMARY KEY (project_id, toDate(timestamp), name)
ORDER BY (project_id, toDate(timestamp), name, id);

-- Migration 0007: Event log table
CREATE TABLE IF NOT EXISTS event_log (
    `id` String,
    `project_id` String,
    `entity_type` String,
    `entity_id` String,
    `event_id` Nullable(String),
    `bucket_name` String,
    `bucket_path` String,
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (project_id, entity_type, entity_id);

-- Migration 0009: Project environments table
CREATE TABLE IF NOT EXISTS project_environments (
    `project_id` String,
    `environments` SimpleAggregateFunction(groupUniqArrayArray, Array(String))
) ENGINE = AggregatingMergeTree
ORDER BY (project_id);

-- Migration 0011: Blob storage file log table
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
    `event_ts` DateTime64(3),
    `is_deleted` UInt8
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
ORDER BY (project_id, entity_type, entity_id, event_id);

-- Migration 0024: Dataset run items table
CREATE TABLE IF NOT EXISTS dataset_run_items_rmt (
    `id` String,
    `project_id` String,
    `dataset_run_id` String,
    `dataset_item_id` String,
    `dataset_id` String,
    `trace_id` String,
    `observation_id` Nullable(String),
    `error` Nullable(String),
    `created_at` DateTime64(3) DEFAULT now(),
    `updated_at` DateTime64(3) DEFAULT now(),
    `dataset_run_name` String,
    `dataset_run_description` Nullable(String),
    `dataset_run_metadata` Map(LowCardinality(String), String),
    `dataset_run_created_at` DateTime64(3),
    `dataset_item_input` Nullable(String) CODEC(ZSTD(3)),
    `dataset_item_expected_output` Nullable(String) CODEC(ZSTD(3)),
    `dataset_item_metadata` Map(LowCardinality(String), String),
    `event_ts` DateTime64(3),
    `is_deleted` UInt8,
    INDEX idx_dataset_item dataset_item_id TYPE bloom_filter(0.001) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
ORDER BY (project_id, dataset_id, dataset_run_id, id);

-- Schema migrations tracking table (not from official migrations but required by golang-migrate)
CREATE TABLE IF NOT EXISTS schema_migrations (
    `version` Int64,
    `dirty` UInt8,
    `sequence` UInt64
) ENGINE = MergeTree 
ORDER BY sequence;

-- IMPORTANT NOTES:
-- 1. This schema is for non-clustered deployments. For clustered deployments:
--    - Replace all engines with Replicated* variants (e.g., ReplicatedReplacingMergeTree)
--    - Add "ON CLUSTER default" to all CREATE TABLE statements
-- 2. Some migrations create materialized views (project_environments_*_mv) which are not included here
-- 3. Analytics tables (migrations 0019-0021) are not included as they're for specialized use cases
-- 4. The exact engine parameters may vary based on your ClickHouse cluster configuration