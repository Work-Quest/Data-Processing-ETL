-- Drop user_id from user_feature_profile (if present)
-- Safe to run multiple times.
ALTER TABLE IF EXISTS user_feature_profile
DROP COLUMN IF EXISTS user_id;


