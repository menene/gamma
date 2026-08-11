-- ============================================================
-- Reentrenamiento del modelo de clasificacion: versionado y trazabilidad
--
-- El artefacto activo conserva siempre el mismo nombre en disco, de modo que
-- el cargador del API no cambia nunca. Cada reentrenamiento archiva el vigente
-- con una marca de tiempo antes de escribir el nuevo, lo que permite revertir
-- copiando el archivo de vuelta.
--
-- Migracion idempotente: puede aplicarse sobre una base ya inicializada.
-- ============================================================

-- Historial de artefactos entrenados. La fila con is_active = true es la que
-- esta cargada en el API en este momento.
CREATE TABLE IF NOT EXISTS silver.model_versions (
    id                  BIGSERIAL PRIMARY KEY,
    -- Marca de tiempo que identifica la version y nombra el archivo archivado.
    version             TEXT        NOT NULL UNIQUE,
    file_name           TEXT        NOT NULL,
    is_active           BOOLEAN     NOT NULL DEFAULT false,
    model_name          TEXT,
    n_classes           INTEGER,
    n_samples           INTEGER,
    -- Metricas sobre la particion de prueba retenida.
    accuracy            NUMERIC(6,4),
    f1_macro            NUMERIC(6,4),
    f1_weighted         NUMERIC(6,4),
    top3_accuracy       NUMERIC(6,4),
    train_seconds       NUMERIC(10,3),
    size_bytes          BIGINT,
    -- Procedencia del conjunto con el que se entreno.
    source_materials    INTEGER,
    source_requests     INTEGER,
    created_by          BIGINT REFERENCES public.users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes               TEXT
);

-- Solo un artefacto puede estar activo a la vez.
CREATE UNIQUE INDEX IF NOT EXISTS uq_model_versions_active
    ON silver.model_versions (is_active) WHERE is_active;

-- Ejecuciones de reentrenamiento. Se registran aunque fallen: el historial de
-- intentos fallidos es tan util como el de los exitosos.
CREATE TABLE IF NOT EXISTS silver.retrain_jobs (
    id                  BIGSERIAL PRIMARY KEY,
    status              TEXT        NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    -- Etapa en curso, para poder informar avance sin instrumentar mas.
    step                TEXT,
    triggered_by        BIGINT REFERENCES public.users(id),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    elapsed_s           NUMERIC(10,3),
    -- Version producida, cuando la ejecucion llega a publicar artefacto.
    version_id          BIGINT REFERENCES silver.model_versions(id),
    -- Version que estaba activa al iniciar, para saber contra que comparar.
    previous_version_id BIGINT REFERENCES silver.model_versions(id),
    n_train             INTEGER,
    n_test              INTEGER,
    n_classes           INTEGER,
    metrics             JSONB,
    error_message       TEXT
);

CREATE INDEX IF NOT EXISTS idx_retrain_jobs_status ON silver.retrain_jobs (status);
CREATE INDEX IF NOT EXISTS idx_retrain_jobs_started ON silver.retrain_jobs (started_at DESC);

-- Siembra del artefacto vigente como version inicial, para que exista una
-- referencia contra la cual comparar el primer reentrenamiento. Las metricas
-- son las reportadas por la competencia de modelos del laboratorio.
INSERT INTO silver.model_versions (
    version, file_name, is_active, model_name,
    n_classes, n_samples, accuracy, f1_macro, f1_weighted, top3_accuracy,
    notes
)
SELECT
    'inicial', 'model_artifact_v1.joblib', true, 'LinearSVC + CharTFIDF',
    1234, 39571, 0.8491, 0.7523, 0.8380, 0.9404,
    'Artefacto original entrenado en el laboratorio, previo al mecanismo de reentrenamiento.'
WHERE NOT EXISTS (SELECT 1 FROM silver.model_versions);
