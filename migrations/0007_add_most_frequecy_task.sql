-- Incremental counters for task-related logs
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS most_frequency_task VARCHAR(225) NULL;

ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS most_frequency_task_counters INTEGER NOT NULL DEFAULT 0;
