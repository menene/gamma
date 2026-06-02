-- ============================================================
-- SILVER: datos operacionales y de referencia
-- ============================================================

-- Catálogo de clases/denominaciones
CREATE TABLE silver.classes (
    id                  BIGSERIAL PRIMARY KEY,
    code                TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    article_group       TEXT,
    sector              TEXT,
    material_type_id    TEXT,
    unspsc_id           TEXT
);

-- Maestro normalizado (base para fuzzy search de duplicados)
CREATE TABLE silver.materials (
    id                  TEXT PRIMARY KEY,
    deletion_flag       BOOLEAN NOT NULL DEFAULT false,
    material_type_id    TEXT NOT NULL,
    article_group       TEXT,
    unit_of_measure     TEXT,
    manufacturer_info   TEXT,
    class_id            TEXT REFERENCES silver.classes(code),
    short_text          TEXT NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_materials_short_text_trgm ON silver.materials
    USING gin (short_text gin_trgm_ops);

-- Clasificador UNSPSC de Naciones Unidas
CREATE TABLE silver.unspsc (
    id                  TEXT PRIMARY KEY,
    description         TEXT NOT NULL
);

-- Tipos de material
CREATE TABLE silver.material_types (
    id                  TEXT PRIMARY KEY,
    description         TEXT
);

INSERT INTO silver.material_types (id, description) VALUES
    ('DIEN', 'Servicios'),
    ('ZCON', 'Materiales de construcción'),
    ('ZEQU', 'Equipos'),
    ('ZHAR', 'Hardware y electrónica'),
    ('ZHER', 'Herramientas'),
    ('ZMAF', 'Maquinaria y fabricación'),
    ('ZMAQ', 'Maquinaria'),
    ('ZMER', 'Mercancía general'),
    ('ZQUI', 'Químicos'),
    ('ZRPA', 'Repuestos automotriz'),
    ('ZRPI', 'Repuestos industriales'),
    ('ZSEG', 'Seguridad'),
    ('ZSUM', 'Suministros');

-- Conversaciones del chatbot
CREATE TABLE silver.conversations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title               TEXT NOT NULL DEFAULT 'Nueva conversacion',
    messages            JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Solicitudes de alta de material
CREATE TABLE silver.requests (
    id                  BIGSERIAL PRIMARY KEY,
    conversation_id     UUID REFERENCES silver.conversations(id) ON DELETE SET NULL,
    name                TEXT NOT NULL,
    long_text           TEXT,
    specifications      JSONB,
    short_text          TEXT,
    material_type_id    TEXT,
    article_group       TEXT,
    category            TEXT,
    confidence          NUMERIC(5,4),
    alternatives        JSONB,
    duplicates          JSONB,
    auto_resolved       BOOLEAN NOT NULL DEFAULT false,
    corrected           BOOLEAN NOT NULL DEFAULT false,
    status              TEXT NOT NULL DEFAULT 'proposal'
                        CHECK (status IN ('proposal', 'confirmed', 'exported', 'discarded')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmed_at        TIMESTAMPTZ,
    exported_at         TIMESTAMPTZ,
    processing_time_s   NUMERIC
);

-- Datasets para entrenamiento y prueba del modelo
CREATE TABLE silver.dataset_train (
    short_text          TEXT NOT NULL,
    material_type_id    TEXT,
    article_group       TEXT
);

CREATE TABLE silver.dataset_test (
    short_text          TEXT NOT NULL,
    material_type_id    TEXT,
    article_group       TEXT
);
