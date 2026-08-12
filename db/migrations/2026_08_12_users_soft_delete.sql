-- ============================================================
-- Borrado logico de usuarios
--
-- Las cuentas no se eliminan de la tabla: se marcan con deleted_at. Sus
-- solicitudes, conversaciones y decisiones sobre duplicados conservan la
-- referencia al usuario que las creo, de modo que el historial no pierde
-- trazabilidad cuando alguien deja el equipo.
--
-- Migracion idempotente: puede aplicarse sobre una base ya inicializada.
-- ============================================================

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- La unicidad del correo debe aplicar solo entre cuentas vigentes. Con la
-- restriccion original, un correo dado de baja quedaba bloqueado para siempre
-- y no se podia volver a dar de alta a la misma persona.
ALTER TABLE public.users
    DROP CONSTRAINT IF EXISTS users_email_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_vigente
    ON public.users (email) WHERE deleted_at IS NULL;

-- Consultar cuentas vigentes es la operacion habitual.
CREATE INDEX IF NOT EXISTS idx_users_deleted_at
    ON public.users (deleted_at) WHERE deleted_at IS NULL;
