-- Drop last_log_id from etl_checkpoint (we use last_time now)
ALTER TABLE etl_checkpoint
DROP COLUMN IF EXISTS last_log_id;







