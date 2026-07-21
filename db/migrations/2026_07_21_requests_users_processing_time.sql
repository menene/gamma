-- Idempotent migration: evitar valores en blanco de processing_time_s en la
-- vista de detalle. Las solicitudes heredadas (antes de que existiera la
-- metrica) y las 'existing_match' no calculan processing_time_s al confirmar,
-- por lo que aparecian NULL en Power BI. Aqui se reconstruye desde los tiempos
-- por paso; solo queda 0 cuando no se midio ningun tiempo. Solo cambia la
-- expresion de una columna (mismo nombre), asi que CREATE OR REPLACE sirve.
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
    COALESCE(
        r.processing_time_s,
        COALESCE(r.llm_elapsed_s, 0)
            + COALESCE(r.duplicates_elapsed_s, 0)
            + COALESCE(r.predict_elapsed_s, 0)
    )                   AS processing_time_s,
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
