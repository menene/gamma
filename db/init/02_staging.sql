CREATE TABLE staging.solicitudes (
    id              BIGSERIAL PRIMARY KEY,
    nombre          TEXT NOT NULL,
    texto_largo     TEXT,
    especificaciones JSONB,
    texto_breve     TEXT,
    categoria       TEXT,
    confianza       NUMERIC(5,4),
    duplicados      JSONB,
    estado          TEXT NOT NULL DEFAULT 'propuesta'
                    CHECK (estado IN ('propuesta','confirmado','exportado','descartado')),
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmado_en   TIMESTAMPTZ,
    exportado_en    TIMESTAMPTZ,
    duracion_seg    NUMERIC
);
