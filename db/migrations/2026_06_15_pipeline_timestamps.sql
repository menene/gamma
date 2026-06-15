-- Idempotent migration: add pipeline timestamp/elapsed columns expected by
-- the chat router. Safe to re-run.

-- silver.requests: pipeline timestamps and elapsed measurements
ALTER TABLE silver.requests
    ADD COLUMN IF NOT EXISTS llm_completed_at        TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS duplicates_completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS duplicates_decided_at   TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS predict_completed_at    TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS discarded_at            TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS llm_elapsed_s           NUMERIC(8,3),
    ADD COLUMN IF NOT EXISTS duplicates_elapsed_s    NUMERIC(8,3),
    ADD COLUMN IF NOT EXISTS predict_elapsed_s       NUMERIC(8,3);

-- bronze.prediction_logs: elapsed_s
ALTER TABLE bronze.prediction_logs
    ADD COLUMN IF NOT EXISTS elapsed_s NUMERIC(8,3);

-- bronze.duplicate_logs: elapsed_s
ALTER TABLE bronze.duplicate_logs
    ADD COLUMN IF NOT EXISTS elapsed_s NUMERIC(8,3);

-- bronze.ingestion_logs: elapsed_s
ALTER TABLE bronze.ingestion_logs
    ADD COLUMN IF NOT EXISTS elapsed_s NUMERIC(8,3);
