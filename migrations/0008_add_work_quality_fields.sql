-- Work quality fields from reviewed_task_log (sentiment analysis)
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS work_quality FLOAT NULL;

ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS best_quality VARCHAR(255) NULL;

ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS best_quality_avg FLOAT NULL;

ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS quality_per_category TEXT NULL;


