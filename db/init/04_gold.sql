-- ============================================================
-- GOLD: vistas y parámetros para dashboard (Power BI)
-- ============================================================

CREATE TABLE gold.parameters (
    id      TEXT PRIMARY KEY,
    value   NUMERIC
);

INSERT INTO gold.parameters (id, value) VALUES
    ('manual_time_s', 0),
    ('hourly_rate', 0);

-- KPI: tiempos de procesamiento por semana
CREATE OR REPLACE VIEW gold.kpi_processing_time AS
SELECT
    date_trunc('week', r.confirmed_at)      AS week,
    count(*)                                AS materials,
    avg(r.processing_time_s)                AS avg_time_s,
    avg(CASE WHEN r.auto_resolved THEN 1 ELSE 0 END) AS auto_rate
FROM silver.requests r
WHERE r.confirmed_at IS NOT NULL
GROUP BY 1;

-- KPI: calidad del modelo por semana
CREATE OR REPLACE VIEW gold.kpi_quality AS
SELECT
    date_trunc('week', r.confirmed_at)      AS week,
    avg(CASE WHEN r.corrected THEN 0 ELSE 1 END) AS accuracy,
    avg(r.confidence)                       AS avg_confidence
FROM silver.requests r
WHERE r.confirmed_at IS NOT NULL
GROUP BY 1;

-- KPI: monetización (ahorro de horas-hombre)
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
    sum(greatest(p.manual_time - r.processing_time_s, 0)) / 3600.0          AS hours_saved,
    (sum(greatest(p.manual_time - r.processing_time_s, 0)) / 3600.0) * p.rate AS savings_q
FROM silver.requests r CROSS JOIN p
WHERE r.confirmed_at IS NOT NULL
GROUP BY 1, p.manual_time, p.rate;

-- Vista: resumen del maestro por tipo de material
CREATE OR REPLACE VIEW gold.materials_by_type AS
SELECT
    m.material_type_id,
    t.description       AS type_description,
    count(*)            AS total_materials
FROM silver.materials m
LEFT JOIN silver.material_types t ON t.id = m.material_type_id
GROUP BY m.material_type_id, t.description
ORDER BY total_materials DESC;
