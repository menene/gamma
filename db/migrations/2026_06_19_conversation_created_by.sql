-- Idempotent migration: add author tracking to silver.conversations so each
-- user only sees their own chats. Safe to re-run.

ALTER TABLE silver.conversations
    ADD COLUMN IF NOT EXISTS created_by BIGINT REFERENCES public.users(id);

CREATE INDEX IF NOT EXISTS idx_conversations_created_by
    ON silver.conversations (created_by);

-- Backfill existing conversations from silver.requests when possible.
-- A conversation may have multiple requests; take the earliest non-null owner.
UPDATE silver.conversations c
SET created_by = r.created_by
FROM (
    SELECT DISTINCT ON (conversation_id)
        conversation_id, created_by
    FROM silver.requests
    WHERE conversation_id IS NOT NULL
      AND created_by IS NOT NULL
    ORDER BY conversation_id, created_at
) r
WHERE c.id = r.conversation_id
  AND c.created_by IS NULL;
