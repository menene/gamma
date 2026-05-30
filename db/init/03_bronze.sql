CREATE TABLE bronze.maestro_raw (
    material     TEXT,
    descripcion  TEXT,
    ingerido_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE bronze.prediccion_logs (
    id             BIGSERIAL PRIMARY KEY,
    solicitud_id   BIGINT,
    tipo           TEXT,
    salida_modelo  JSONB,
    confianza      NUMERIC(5,4),
    decision_usuario JSONB,
    registrado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
