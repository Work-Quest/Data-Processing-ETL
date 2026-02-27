-- ==========================================
-- AI FEATURE DATABASE INITIAL MIGRATION
-- For Neon PostgreSQL
-- ==========================================

-- Enable UUID extension (safe if already exists)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. ETL CHECKPOINT
-- ==========================================

CREATE TABLE IF NOT EXISTS etl_checkpoint (
    pipeline_name TEXT PRIMARY KEY,
    last_log_id BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO etl_checkpoint (pipeline_name, last_log_id)
VALUES ('log_pipeline', 0)
ON CONFLICT DO NOTHING;


-- ==========================================
-- 2. ETL RUN LOGGING
-- ==========================================

CREATE TABLE IF NOT EXISTS etl_run (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_name TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMP,
    logs_processed INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_etl_run_started_at
ON etl_run(started_at);


-- ==========================================
-- 3. USER FEATURE TABLE (TRAINING READY)
-- ==========================================

CREATE TABLE IF NOT EXISTS user_feature_daily (
    user_id BIGINT NOT NULL,
    date DATE NOT NULL,

    tasks_completed INTEGER,
    avg_completion_time FLOAT,
    avg_delay_time FLOAT,
    avg_complexity FLOAT,
    quality_score_mean FLOAT,
    on_time_rate FLOAT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_user_feature_daily_user
ON user_feature_daily(user_id);

CREATE INDEX IF NOT EXISTS idx_user_feature_daily_date
ON user_feature_daily(date);


-- ==========================================
-- 4. KMEANS TRAINING RUN METADATA
-- ==========================================

CREATE TABLE IF NOT EXISTS kmeans_run (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trained_at TIMESTAMP NOT NULL DEFAULT NOW(),
    window_start DATE,
    window_end DATE,
    k INTEGER NOT NULL,
    inertia FLOAT,
    silhouette_score FLOAT,
    is_active BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_kmeans_run_trained_at
ON kmeans_run(trained_at);


-- ==========================================
-- 5. MODEL BINARY STORAGE (JOBLIB BYTEA)
-- ==========================================

CREATE TABLE IF NOT EXISTS kmeans_model (
    run_id UUID PRIMARY KEY REFERENCES kmeans_run(run_id) ON DELETE CASCADE,
    model_blob BYTEA NOT NULL
);


-- ==========================================
-- 6. USER CLUSTER ASSIGNMENT
-- ==========================================

CREATE TABLE IF NOT EXISTS user_cluster_assignment (
    run_id UUID REFERENCES kmeans_run(run_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    cluster_id INTEGER NOT NULL,
    distance_to_centroid FLOAT,

    assigned_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (run_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_cluster_user
ON user_cluster_assignment(user_id);


-- ==========================================
-- 7. SAFETY: Only one active model at a time
-- ==========================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_only_one_active_model
ON kmeans_run(is_active)
WHERE is_active = TRUE;

-- ==========================================
-- 8. user_feature_daily : processed data
-- ==========================================
CREATE TABLE IF NOT EXISTS user_feature_profile (
    user_feature_profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    project_member_id UUID NOT NULL,
    work_load_per_day VARCHAR(255) NOT NULL,
    team_work FLOAT NOT NULL,
    work_category VARCHAR(255) NOT NULL,
    work_speed FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

