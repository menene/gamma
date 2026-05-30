CREATE TABLE gold.parametros (
    clave  TEXT PRIMARY KEY,
    valor  NUMERIC
);

INSERT INTO gold.parametros (clave, valor) VALUES
    ('t_manual_seg', 0),
    ('tarifa_hora', 0);

CREATE OR REPLACE VIEW gold.kpi_tiempos AS
SELECT
    date_trunc('week', confirmado_en) AS semana,
    count(*)                          AS materiales,
    avg(duracion_seg)                 AS prom_seg_sistema,
    avg(CASE WHEN auto_resuelto THEN 1 ELSE 0 END) AS tasa_auto
FROM silver.solicitudes
WHERE confirmado_en IS NOT NULL
GROUP BY 1;

CREATE OR REPLACE VIEW gold.kpi_calidad AS
SELECT
    date_trunc('week', confirmado_en) AS semana,
    avg(CASE WHEN correccion THEN 0 ELSE 1 END) AS exactitud_categoria,
    avg(confianza)                              AS confianza_prom
FROM silver.solicitudes
WHERE confirmado_en IS NOT NULL
GROUP BY 1;

CREATE OR REPLACE VIEW gold.monetizacion AS
WITH p AS (
    SELECT
        max(valor) FILTER (WHERE clave='t_manual_seg') AS t_manual,
        max(valor) FILTER (WHERE clave='tarifa_hora')  AS tarifa
    FROM gold.parametros
)
SELECT
    date_trunc('week', s.confirmado_en) AS semana,
    count(*) AS materiales,
    sum(greatest(p.t_manual - s.duracion_seg, 0)) / 3600.0       AS horas_ahorradas,
    (sum(greatest(p.t_manual - s.duracion_seg, 0)) / 3600.0) * p.tarifa AS ahorro_q
FROM silver.solicitudes s CROSS JOIN p
WHERE s.confirmado_en IS NOT NULL
GROUP BY 1, p.t_manual, p.tarifa;
