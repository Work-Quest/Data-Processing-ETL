-- Support incremental ETL merges: store JSON arrays + raw diligence counters

-- Arrays can exceed 255 chars, so widen to TEXT
ALTER TABLE user_feature_daily
ALTER COLUMN work_load_per_day TYPE TEXT;

ALTER TABLE user_feature_daily
ALTER COLUMN work_speed TYPE TEXT;

-- Track what date index 0 corresponds to for arrays
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS window_start_date DATE;

UPDATE user_feature_daily
SET window_start_date = COALESCE(window_start_date, created_at::date, CURRENT_DATE);

ALTER TABLE user_feature_daily
ALTER COLUMN window_start_date SET NOT NULL;

-- Raw diligence counters (by priority)
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS diligence_p1 INTEGER NOT NULL DEFAULT 0;
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS diligence_p2 INTEGER NOT NULL DEFAULT 0;
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS diligence_p3 INTEGER NOT NULL DEFAULT 0;
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS diligence_p4 INTEGER NOT NULL DEFAULT 0;





