-- Idempotent migration: add an `admin` flag to users. Admin accounts are used
-- for testing; their data (requests, materials, duplicate decisions) is excluded
-- from every gold reporting view so test noise stays out of the dashboards.
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS admin BOOLEAN NOT NULL DEFAULT false;

-- Recreate the gold views with the admin exclusion. A LEFT JOIN to users keeps
-- rows with no creator (legacy / ETL-imported) via COALESCE(u.admin, false).
-- Drop first: the running DB may have older column names, which CREATE OR
-- REPLACE cannot change. These views are independent (no view-to-view deps).
DROP VIEW IF EXISTS gold.kpi_processing_time;
DROP VIEW IF EXISTS gold.kpi_quality;
DROP VIEW IF EXISTS gold.kpi_savings;
DROP VIEW IF EXISTS gold.kpi_step_breakdown;
DROP VIEW IF EXISTS gold.kpi_duplicates;
DROP VIEW IF EXISTS gold.requests_users;
DROP VIEW IF EXISTS gold.kpi_requests_by_user;
DROP VIEW IF EXISTS gold.materials_by_type;

CREATE OR REPLACE VIEW gold.kpi_processing_time AS
SELECT
    date_trunc('week', r.confirmed_at)      AS week,
    count(*)                                AS materials,
    avg(r.processing_time_s)                AS avg_total_s,
    avg(r.llm_elapsed_s)                    AS avg_llm_s,
    avg(r.duplicates_elapsed_s)             AS avg_duplicates_s,
    avg(r.predict_elapsed_s)                AS avg_predict_s,
    avg(EXTRACT(EPOCH FROM (r.confirmed_at - r.predict_completed_at))) AS avg_user_review_s,
    avg(EXTRACT(EPOCH FROM (r.duplicates_decided_at - r.duplicates_completed_at))) AS avg_dup_decision_s,
    avg(CASE WHEN r.auto_resolved THEN 1 ELSE 0 END) AS auto_rate
FROM silver.requests r
LEFT JOIN public.users u ON u.id = r.created_by
WHERE r.confirmed_at IS NOT NULL
  AND COALESCE(u.admin, false) = false
GROUP BY 1;

CREATE OR REPLACE VIEW gold.kpi_quality AS
SELECT
    date_trunc('week', r.confirmed_at)      AS week,
    count(*)                                AS materials,
    avg(CASE WHEN r.corrected THEN 0 ELSE 1 END) AS accuracy,
    avg(r.confidence)                       AS avg_confidence,
    count(*) FILTER (WHERE r.status = 'existing_match') AS duplicate_matches,
    count(*) FILTER (WHERE r.corrected) AS corrections
FROM silver.requests r
LEFT JOIN public.users u ON u.id = r.created_by
WHERE (r.confirmed_at IS NOT NULL OR r.status = 'existing_match')
  AND COALESCE(u.admin, false) = false
GROUP BY 1;

CREATE OR REPLACE VIEW gold.kpi_savings AS
WITH p AS (
    SELECT
        max(value) FILTER (WHERE id = 'manual_time_s') AS manual_time,
        max(value) FILTER (WHERE id = 'hourly_rate')   AS rate
    FROM gold.parameters
)
SELECT
    date_trunc('week', r.confirmed_at)  AS week,
    count(*)                            AS materials,
    avg(r.processing_time_s)            AS avg_processing_s,
    sum(greatest(p.manual_time - r.processing_time_s, 0)) / 3600.0          AS hours_saved,
    (sum(greatest(p.manual_time - r.processing_time_s, 0)) / 3600.0) * p.rate AS savings_q
FROM silver.requests r
CROSS JOIN p
LEFT JOIN public.users u ON u.id = r.created_by
WHERE r.confirmed_at IS NOT NULL
  AND COALESCE(u.admin, false) = false
GROUP BY 1, p.manual_time, p.rate;

CREATE OR REPLACE VIEW gold.kpi_step_breakdown AS
SELECT
    date_trunc('week', r.created_at) AS week,
    count(*) AS total_requests,
    avg(r.llm_elapsed_s) AS avg_llm_s,
    avg(r.duplicates_elapsed_s) AS avg_dup_search_s,
    avg(r.predict_elapsed_s) AS avg_predict_s,
    avg(r.processing_time_s) AS avg_machine_total_s,
    avg(EXTRACT(EPOCH FROM (r.duplicates_decided_at - r.duplicates_completed_at)))
        FILTER (WHERE r.duplicates_decided_at IS NOT NULL) AS avg_dup_decision_s,
    avg(EXTRACT(EPOCH FROM (r.confirmed_at - r.predict_completed_at)))
        FILTER (WHERE r.confirmed_at IS NOT NULL AND r.predict_completed_at IS NOT NULL) AS avg_user_review_s,
    avg(EXTRACT(EPOCH FROM (COALESCE(r.confirmed_at, r.discarded_at) - r.created_at)))
        FILTER (WHERE r.confirmed_at IS NOT NULL OR r.discarded_at IS NOT NULL) AS avg_wall_time_s,
    count(*) FILTER (WHERE r.status = 'confirmed') AS confirmed,
    count(*) FILTER (WHERE r.status = 'discarded') AS discarded,
    count(*) FILTER (WHERE r.status = 'existing_match') AS existing_matches
FROM silver.requests r
LEFT JOIN public.users u ON u.id = r.created_by
WHERE COALESCE(u.admin, false) = false
GROUP BY 1;

CREATE OR REPLACE VIEW gold.kpi_duplicates AS
SELECT
    date_trunc('week', d.logged_at) AS week,
    count(*) AS total_decisions,
    count(*) FILTER (WHERE d.action = 'accepted') AS accepted,
    count(*) FILTER (WHERE d.action = 'rejected') AS rejected,
    avg(d.elapsed_s) AS avg_search_s
FROM bronze.duplicate_logs d
LEFT JOIN silver.requests r ON r.id = d.request_id
LEFT JOIN public.users u ON u.id = r.created_by
WHERE COALESCE(u.admin, false) = false
GROUP BY 1;

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
LEFT JOIN public.users u ON u.id = r.created_by
WHERE COALESCE(u.admin, false) = false;

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
WHERE COALESCE(u.admin, false) = false
GROUP BY 1, 2, 3, 4;

CREATE OR REPLACE VIEW gold.materials_by_type AS
SELECT
    t.code              AS material_type_code,
    t.description       AS type_description,
    count(*)            AS total_materials
FROM silver.materials m
LEFT JOIN silver.classes c ON c.id = m.class_id
LEFT JOIN silver.material_types t ON t.id = c.material_type_id
LEFT JOIN silver.requests r ON r.id = m.source_request_id
LEFT JOIN public.users u ON u.id = r.created_by
WHERE COALESCE(u.admin, false) = false
GROUP BY t.code, t.description
ORDER BY total_materials DESC;
