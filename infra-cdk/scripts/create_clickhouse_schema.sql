-- ClickHouse Schema for Langfuse v3
-- This file contains the complete schema required for Langfuse to work with ClickHouse

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

-- Traces table (with all required columns)
CREATE TABLE IF NOT EXISTS traces (
    id String,
    timestamp DateTime64(3),
    name Nullable(String),
    user_id Nullable(String),
    metadata Nullable(String),
    release Nullable(String),
    version Nullable(String),
    project_id String,
    public Nullable(UInt8),
    tags Array(String),
    bookmarked Nullable(UInt8),
    session_id Nullable(String),
    input Nullable(String),
    output Nullable(String),
    environment Nullable(String),
    external_id Nullable(String),
    latency Nullable(Float64),
    total_cost Nullable(Float64),
    input_tokens Nullable(Int64),
    output_tokens Nullable(Int64),
    total_tokens Nullable(Int64),
    created_at DateTime64(3),
    updated_at DateTime64(3),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (project_id, id, event_ts)
PARTITION BY toYYYYMM(timestamp);

-- Observations table (with all required columns)
CREATE TABLE IF NOT EXISTS observations (
    id String,
    trace_id Nullable(String),
    project_id String,
    type String,
    parent_observation_id Nullable(String),
    name Nullable(String),
    start_time DateTime64(3),
    end_time Nullable(DateTime64(3)),
    completion_start_time Nullable(DateTime64(3)),
    metadata Nullable(String),
    model Nullable(String),
    model_parameters Nullable(String),
    input Nullable(String),
    output Nullable(String),
    provided_model_name Nullable(String),
    unit Nullable(String),
    level Nullable(String),
    status_message Nullable(String),
    version Nullable(String),
    provided_usage_details Nullable(String),
    usage_details Nullable(String),
    provided_cost_details Nullable(String),
    cost_details Nullable(String),
    total_cost Nullable(Float64),
    provided_input_cost Nullable(Float64),
    input_cost Nullable(Float64),
    provided_output_cost Nullable(Float64),
    output_cost Nullable(Float64),
    provided_total_cost Nullable(Float64),
    completion_tokens Nullable(Int64),
    prompt_tokens Nullable(Int64),
    total_tokens Nullable(Int64),
    environment Nullable(String),
    latency Nullable(Float64),
    created_at DateTime64(3),
    updated_at DateTime64(3),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (project_id, id, event_ts)
PARTITION BY toYYYYMM(start_time);

-- Scores table
CREATE TABLE IF NOT EXISTS scores (
    id String,
    timestamp DateTime64(3),
    project_id String,
    trace_id String,
    observation_id Nullable(String),
    name String,
    value Nullable(Float64),
    string_value Nullable(String),
    source String,
    comment Nullable(String),
    author_user_id Nullable(String),
    config_id Nullable(String),
    data_type String,
    queue_id Nullable(String),
    environment Nullable(String),
    created_at DateTime64(3),
    updated_at DateTime64(3),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (project_id, id, event_ts)
PARTITION BY toYYYYMM(timestamp);

-- Project environments table
CREATE TABLE IF NOT EXISTS project_environments (
    project_id String,
    environments Array(String),
    created_at DateTime64(3),
    updated_at DateTime64(3),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (project_id, event_ts);

-- Event log table (with blob storage migration columns)
CREATE TABLE IF NOT EXISTS event_log (
    id String,
    project_id String,
    timestamp DateTime64(3),
    event_type String,
    event_data String,
    entity_type Nullable(String),
    entity_id Nullable(String),
    event_id Nullable(String),
    bucket_name Nullable(String),
    bucket_path Nullable(String),
    created_at DateTime64(3),
    updated_at DateTime64(3),
    event_ts DateTime64(3) DEFAULT now64(3),
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (project_id, id, event_ts)
PARTITION BY toYYYYMM(timestamp);

-- Blob storage file log table
CREATE TABLE IF NOT EXISTS blob_storage_file_log (
    id String,
    project_id String,
    file_path String,
    bucket String,
    size Int64,
    created_at DateTime64(3),
    updated_at DateTime64(3)
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (project_id, id);

-- Dataset run items table
CREATE TABLE IF NOT EXISTS dataset_run_items_rmt (
    id String,
    dataset_run_id String,
    dataset_item_id String,
    project_id String,
    trace_id Nullable(String),
    observation_id Nullable(String),
    created_at DateTime64(3),
    updated_at DateTime64(3)
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (project_id, id);

-- Add indexes for performance
ALTER TABLE traces ADD INDEX IF NOT EXISTS idx_session_id (session_id) TYPE bloom_filter GRANULARITY 1;
ALTER TABLE traces ADD INDEX IF NOT EXISTS idx_user_id (user_id) TYPE bloom_filter GRANULARITY 1;
ALTER TABLE traces ADD INDEX IF NOT EXISTS idx_environment (environment) TYPE bloom_filter GRANULARITY 1;
ALTER TABLE observations ADD INDEX IF NOT EXISTS idx_trace_id (trace_id) TYPE bloom_filter GRANULARITY 1;
ALTER TABLE observations ADD INDEX IF NOT EXISTS idx_environment (environment) TYPE bloom_filter GRANULARITY 1;
ALTER TABLE scores ADD INDEX IF NOT EXISTS idx_trace_id (trace_id) TYPE bloom_filter GRANULARITY 1;
ALTER TABLE scores ADD INDEX IF NOT EXISTS idx_environment (environment) TYPE bloom_filter GRANULARITY 1;

-- Insert migration records
INSERT INTO schema_migrations (version, dirty, sequence) VALUES (1, 0, 1);
INSERT INTO schema_migrations (version, dirty, sequence) VALUES (2, 0, 2);
INSERT INTO schema_migrations (version, dirty, sequence) VALUES (3, 0, 3);
INSERT INTO schema_migrations (version, dirty, sequence) VALUES (4, 0, 4);
INSERT INTO schema_migrations (version, dirty, sequence) VALUES (5, 0, 5);
INSERT INTO schema_migrations (version, dirty, sequence) VALUES (6, 0, 6);