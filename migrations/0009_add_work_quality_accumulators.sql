-- Accumulators for all-time work quality (sentiment) so ETL can be incremental
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS work_quality_sum FLOAT NULL;

ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS work_quality_count INTEGER NOT NULL DEFAULT 0;

-- JSON: { "Category": {"sum": <float>, "count": <int>}, ... }
ALTER TABLE user_feature_daily
ADD COLUMN IF NOT EXISTS quality_per_category_sum_count TEXT NULL;






