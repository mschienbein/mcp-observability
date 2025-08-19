-- ClickHouse Schema for Langfuse v3 (Official)
-- Based on: https://github.com/langfuse/langfuse/tree/main/packages/shared/clickhouse/migrations/clustered
-- This schema includes all required tables and columns from the official Langfuse repository

-- Drop existing tables if needed (for clean setup)
DROP TABLE IF EXISTS traces;
DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS scores;
DROP TABLE IF EXISTS project_environments;
DROP TABLE IF EXISTS event_log;
DROP TABLE IF EXISTS blob_storage_file_log;
DROP TABLE IF EXISTS dataset_run_items_rmt;
DROP TABLE IF EXISTS schema_migrations;

-- Schema migrations tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version Int64,
    dirty UInt8,
    sequence UInt64
) ENGINE = MergeTree ORDER BY sequence;

-- Traces table (from migration 0001 + 0005 + 0006 + 0008)
CREATE TABLE IF NOT EXISTS traces (
    id String,
    timestamp DateTime64(3),
    name String,
    user_id Nullable(String),
    metadata Map(LowCardinality(String), String),
    release Nullable(String),
    version Nullable(String),
    project_id String,
    environment LowCardinality(String) DEFAULT 'default',
    public Bool,
    bookmarked Bool,
    tags Array(String),
    input Nullable(String) CODEC(ZSTD(3)),
    output Nullable(String) CODEC(ZSTD(3)),
    session_id Nullable(String),
    created_at DateTime64(3) DEFAULT now(),
    updated_at DateTime64(3) DEFAULT now(),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0,
    INDEX idx_id id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_res_metadata_key mapKeys(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_res_metadata_value mapValues(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_session_id session_id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_user_id user_id TYPE bloom_filter(0.001) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
PARTITION BY toYYYYMM(timestamp)
PRIMARY KEY (project_id, toDate(timestamp))
ORDER BY (project_id, toDate(timestamp), id);

-- Observations table (from migration 0002 + 0008 + 0025)
CREATE TABLE IF NOT EXISTS observations (
    id String,
    trace_id String,
    project_id String,
    environment LowCardinality(String) DEFAULT 'default',
    type LowCardinality(String),
    parent_observation_id Nullable(String),
    start_time DateTime64(3),
    end_time Nullable(DateTime64(3)),
    name String,
    metadata Map(LowCardinality(String), String),
    level LowCardinality(String),
    status_message Nullable(String),
    version Nullable(String),
    input Nullable(String) CODEC(ZSTD(3)),
    output Nullable(String) CODEC(ZSTD(3)),
    provided_model_name Nullable(String),
    internal_model_id Nullable(String),
    model_parameters Nullable(String),
    provided_usage_details Map(LowCardinality(String), UInt64),
    usage_details Map(LowCardinality(String), UInt64),
    provided_cost_details Map(LowCardinality(String), Decimal64(12)),
    cost_details Map(LowCardinality(String), Decimal64(12)),
    total_cost Nullable(Decimal64(12)),
    completion_start_time Nullable(DateTime64(3)),
    prompt_id Nullable(String),
    prompt_name Nullable(String),
    prompt_version Nullable(UInt16),
    created_at DateTime64(3) DEFAULT now(),
    updated_at DateTime64(3) DEFAULT now(),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0,
    INDEX idx_id id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_trace_id trace_id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_project_id project_id TYPE bloom_filter() GRANULARITY 1,
    INDEX idx_res_metadata_key mapKeys(metadata) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_res_metadata_value mapValues(metadata) TYPE bloom_filter(0.01) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
PARTITION BY toYYYYMM(start_time)
PRIMARY KEY (project_id, type, toDate(start_time))
ORDER BY (project_id, type, toDate(start_time), id);

-- Scores table (from migration 0003 + 0008 + 0010 + 0012 + 0014 + 0015 + 0016 + 0017 + 0018)
CREATE TABLE IF NOT EXISTS scores (
    id String,
    timestamp DateTime64(3),
    project_id String,
    environment LowCardinality(String) DEFAULT 'default',
    trace_id Nullable(String),  -- Made nullable in migration 0014
    observation_id Nullable(String),
    name String,
    value Float64,
    source String,
    comment Nullable(String) CODEC(ZSTD(1)),
    author_user_id Nullable(String),
    config_id Nullable(String),
    data_type String,
    string_value Nullable(String),
    queue_id Nullable(String),
    metadata Map(LowCardinality(String), String),  -- Added in migration 0010
    session_id Nullable(String),  -- Added in migration 0012
    run_id Nullable(String),  -- Added in migration 0017
    created_at DateTime64(3) DEFAULT now(),
    updated_at DateTime64(3) DEFAULT now(),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0,
    INDEX idx_id id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_project_trace_observation (project_id, trace_id, observation_id) TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_trace_id trace_id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_session_id session_id TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_run_id run_id TYPE bloom_filter(0.001) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
PARTITION BY toYYYYMM(timestamp)
PRIMARY KEY (project_id, toDate(timestamp), name)
ORDER BY (project_id, toDate(timestamp), name, id);

-- Project environments table (from migration 0009)
CREATE TABLE IF NOT EXISTS project_environments (
    project_id String,
    environments SimpleAggregateFunction(groupUniqArrayArray, Array(String)),
    created_at DateTime64(3) DEFAULT now(),
    updated_at DateTime64(3) DEFAULT now(),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = AggregatingMergeTree
ORDER BY (project_id);

-- Event log table (from migration 0007)
CREATE TABLE IF NOT EXISTS event_log (
    id String,
    project_id String,
    entity_type String,
    entity_id String,
    event_id Nullable(String),
    bucket_name String,
    bucket_path String,
    created_at DateTime64(3) DEFAULT now(),
    updated_at DateTime64(3) DEFAULT now(),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = MergeTree()
ORDER BY (project_id, entity_type, entity_id);

-- Blob storage file log table (from migration 0011)
CREATE TABLE IF NOT EXISTS blob_storage_file_log (
    id String,
    project_id String,
    entity_type String,
    entity_id String,
    event_id String,
    bucket_name String,
    bucket_path String,
    created_at DateTime64(3) DEFAULT now(),
    updated_at DateTime64(3) DEFAULT now(),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
ORDER BY (project_id, entity_type, entity_id, event_id);

-- Dataset run items table (from migration 0024)
CREATE TABLE IF NOT EXISTS dataset_run_items_rmt (
    id String,
    project_id String,
    dataset_run_id String,
    dataset_item_id String,
    dataset_id String,
    trace_id String,
    observation_id Nullable(String),
    error Nullable(String),
    dataset_run_name String,
    dataset_run_description Nullable(String),
    dataset_run_metadata Map(LowCardinality(String), String),
    dataset_run_created_at DateTime64(3),
    dataset_item_input Nullable(String) CODEC(ZSTD(3)),
    dataset_item_expected_output Nullable(String) CODEC(ZSTD(3)),
    dataset_item_metadata Map(LowCardinality(String), String),
    created_at DateTime64(3) DEFAULT now(),
    updated_at DateTime64(3) DEFAULT now(),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0,
    INDEX idx_dataset_item dataset_item_id TYPE bloom_filter(0.001) GRANULARITY 1
) ENGINE = ReplacingMergeTree(event_ts, is_deleted)
ORDER BY (project_id, dataset_id, dataset_run_id, id);

-- Insert migration records (up to the latest migration 26)
INSERT INTO schema_migrations (version, dirty, sequence) 
SELECT * FROM (
    SELECT 1 as version, 0 as dirty, 1 as sequence
    UNION ALL SELECT 2, 0, 2
    UNION ALL SELECT 3, 0, 3
    UNION ALL SELECT 4, 0, 4
    UNION ALL SELECT 5, 0, 5
    UNION ALL SELECT 6, 0, 6
    UNION ALL SELECT 7, 0, 7
    UNION ALL SELECT 8, 0, 8
    UNION ALL SELECT 9, 0, 9
    UNION ALL SELECT 10, 0, 10
    UNION ALL SELECT 11, 0, 11
    UNION ALL SELECT 12, 0, 12
    UNION ALL SELECT 13, 0, 13
    UNION ALL SELECT 14, 0, 14
    UNION ALL SELECT 15, 0, 15
    UNION ALL SELECT 16, 0, 16
    UNION ALL SELECT 17, 0, 17
    UNION ALL SELECT 18, 0, 18
    UNION ALL SELECT 19, 0, 19
    UNION ALL SELECT 20, 0, 20
    UNION ALL SELECT 21, 0, 21
    UNION ALL SELECT 22, 0, 22
    UNION ALL SELECT 23, 0, 23
    UNION ALL SELECT 24, 0, 24
    UNION ALL SELECT 25, 0, 25
    UNION ALL SELECT 26, 0, 26
) AS migrations
WHERE version NOT IN (SELECT version FROM schema_migrations);

-- IMPORTANT: For clustered deployments, you need to:
-- 1. Add "ON CLUSTER default" to all CREATE TABLE statements
-- 2. Use Replicated* engine variants (e.g., ReplicatedReplacingMergeTree)
-- 3. Create the materialized views for project_environments as shown in the official migrations