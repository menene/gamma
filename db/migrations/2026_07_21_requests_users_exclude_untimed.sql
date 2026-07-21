-- Idempotent migration: la vista de detalle debe excluir las solicitudes
-- heredadas que no tienen NINGUN tiempo medido (no se pueden usar para KPIs).
-- Se conservan todas las que tienen al menos un valor real de tiempo, incluidas
-- las 'existing_match' nuevas (traen llm+duplicates aunque no lleguen a predict).
-- Solo se agrega una condicion al WHERE; CREATE OR REPLACE es suficiente.
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
WHERE COALESCE(u.admin, false) = false
  AND (
      r.processing_time_s IS NOT NULL
      OR r.llm_elapsed_s IS NOT NULL
      OR r.duplicates_elapsed_s IS NOT NULL
      OR r.predict_elapsed_s IS NOT NULL
  );
