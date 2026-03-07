-- Store scaler separately for DB-loaded inference
ALTER TABLE kmeans_model
ADD COLUMN IF NOT EXISTS scaler_blob BYTEA;


