-- ============================================================
-- BRONZE: logs del sistema
-- ============================================================

-- Registro de cada archivo importado
CREATE TABLE bronze.ingestion_logs (
    id              BIGSERIAL PRIMARY KEY,
    file_name       TEXT NOT NULL,
    file_path       TEXT,
    row_count       INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'partial', 'failed')),
    error_message   TEXT,
    elapsed_s       NUMERIC(8,3),
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Logs de cada prediccion del sistema
CREATE TABLE bronze.prediction_logs (
    id              BIGSERIAL PRIMARY KEY,
    request_id      BIGINT,
    type            TEXT NOT NULL CHECK (type IN ('duplicates', 'description', 'categorization')),
    input           JSONB,
    output          JSONB,
    confidence      NUMERIC(5,4),
    elapsed_s       NUMERIC(8,3),
    user_decision   JSONB,
    logged_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Logs de decisiones sobre duplicados
CREATE TABLE bronze.duplicate_logs (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id UUID,
    request_id      BIGINT,
    action          TEXT NOT NULL CHECK (action IN ('accepted', 'rejected')),
    short_text      TEXT,
    selected_material_id TEXT,
    duplicates      JSONB,
    elapsed_s       NUMERIC(8,3),
    logged_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Logs de errores de la aplicacion
CREATE TABLE bronze.app_errors (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    message         TEXT NOT NULL,
    details         JSONB,
    logged_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Logs de interacciones con LLM
CREATE TABLE bronze.llm_logs (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id UUID,
    model           TEXT NOT NULL,
    system_prompt   TEXT,
    user_message    TEXT NOT NULL,
    history_len     INTEGER NOT NULL DEFAULT 0,
    response_raw    TEXT,
    response_parsed JSONB,
    action          TEXT,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    elapsed_s       NUMERIC(8,3),
    error           TEXT,
    logged_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
