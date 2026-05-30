CREATE TABLE silver.maestro (
    material     TEXT PRIMARY KEY,
    descripcion  TEXT NOT NULL,
    categoria    TEXT,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_maestro_desc_trgm ON silver.maestro
    USING gin (descripcion gin_trgm_ops);

CREATE TABLE silver.solicitudes (
    id            BIGINT PRIMARY KEY,
    categoria     TEXT,
    confianza     NUMERIC(5,4),
    auto_resuelto BOOLEAN,
    correccion    BOOLEAN,
    duracion_seg  NUMERIC,
    confirmado_en TIMESTAMPTZ
);

CREATE TABLE silver.dataset_train (descripcion TEXT, categoria TEXT);
CREATE TABLE silver.dataset_test  (descripcion TEXT, categoria TEXT);
