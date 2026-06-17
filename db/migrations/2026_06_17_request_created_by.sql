-- Idempotent migration: add author tracking to silver.requests for the
-- Power BI dashboard. Safe to re-run.

ALTER TABLE silver.requests
    ADD COLUMN IF NOT EXISTS created_by BIGINT REFERENCES public.users(id);

CREATE INDEX IF NOT EXISTS idx_requests_created_by
    ON silver.requests (created_by);

-- Gold view: requests enriched with the user that created them, for BI tools.
CREATE OR REPLACE VIEW gold.requests_users AS
SELECT
    r.id                AS request_id,
    r.created_at,
    r.confirmed_at,
    r.discarded_at,
    r.exported_at,
    r.status,
    r.material_type_id,
    mt.code             AS material_type_code,
    mt.description      AS material_type_description,
    r.name              AS material_name,
    r.short_text,
    r.long_text,
    r.category          AS class_code,
    r.confidence,
    r.corrected,
    r.auto_resolved,
    r.processing_time_s,
    r.llm_elapsed_s,
    r.duplicates_elapsed_s,
    r.predict_elapsed_s,
    r.created_by        AS user_id,
    u.email             AS user_email,
    u.name              AS user_name
FROM silver.requests r
LEFT JOIN silver.material_types mt ON mt.id = r.material_type_id
LEFT JOIN public.users u ON u.id = r.created_by;

-- KPI: requests per user per week (for Power BI)
CREATE OR REPLACE VIEW gold.kpi_requests_by_user AS
SELECT
    date_trunc('week', r.created_at)                        AS week,
    r.created_by                                            AS user_id,
    u.email                                                 AS user_email,
    u.name                                                  AS user_name,
    count(*)                                                AS total_requests,
    count(*) FILTER (WHERE r.status = 'confirmed')          AS confirmed,
    count(*) FILTER (WHERE r.status = 'discarded')          AS discarded,
    count(*) FILTER (WHERE r.status = 'existing_match')     AS existing_matches,
    count(*) FILTER (WHERE r.corrected)                     AS corrections,
    avg(r.processing_time_s)                                AS avg_processing_s
FROM silver.requests r
LEFT JOIN public.users u ON u.id = r.created_by
GROUP BY 1, 2, 3, 4;
