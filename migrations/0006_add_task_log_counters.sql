-- Incremental counters for task-related logs
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS task_assigned INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS task_created INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS task_completed INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS task_deleted INTEGER NOT NULL DEFAULT 0;









