-- ============================================================
-- SILVER: datos operacionales y de referencia
-- ============================================================

-- Tipos de material
CREATE TABLE silver.material_types (
    id                  BIGSERIAL PRIMARY KEY,
    code                TEXT NOT NULL UNIQUE,
    description         TEXT
);

INSERT INTO silver.material_types (code, description) VALUES
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

-- Clasificador UNSPSC de Naciones Unidas
CREATE TABLE silver.unspsc (
    id                  BIGSERIAL PRIMARY KEY,
    code                TEXT NOT NULL UNIQUE,
    description         TEXT NOT NULL
);

-- Catálogo de clases/denominaciones
CREATE TABLE silver.classes (
    id                  BIGSERIAL PRIMARY KEY,
    code                TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    material_type_id    BIGINT REFERENCES silver.material_types(id),
    unspsc_id           BIGINT REFERENCES silver.unspsc(id),
    article_group       TEXT,
    sector              TEXT
);

-- Unidades de medida
CREATE TABLE silver.units_of_measure (
    id                  BIGSERIAL PRIMARY KEY,
    code                TEXT NOT NULL UNIQUE,
    description         TEXT
);

-- Maestro normalizado (base para fuzzy search de duplicados)
CREATE TABLE silver.materials (
    id                  BIGSERIAL PRIMARY KEY,
    code                TEXT NOT NULL UNIQUE,
    class_id            BIGINT REFERENCES silver.classes(id),
    unit_of_measure_id  BIGINT REFERENCES silver.units_of_measure(id),
    short_text          TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deletion_flag       BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_materials_short_text_trgm ON silver.materials
    USING gin (short_text gin_trgm_ops);

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
    material_type_id    BIGINT REFERENCES silver.material_types(id),
    name                TEXT NOT NULL,
    long_text           TEXT,
    specifications      JSONB,
    short_text          TEXT,
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
    material_type_id    BIGINT REFERENCES silver.material_types(id),
    article_group       TEXT
);

CREATE TABLE silver.dataset_test (
    short_text          TEXT NOT NULL,
    material_type_id    BIGINT REFERENCES silver.material_types(id),
    article_group       TEXT
);
