-- Add last_time checkpoint so we can fetch logs incrementally by time
ALTER TABLE etl_checkpoint
ADD COLUMN IF NOT EXISTS last_time TIMESTAMP;

-- Initialize for existing row(s)
UPDATE etl_checkpoint
SET last_time = COALESCE(last_time, updated_at, NOW())
WHERE pipeline_name = 'log_pipeline';







